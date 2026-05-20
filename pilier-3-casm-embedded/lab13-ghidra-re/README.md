# Write-up — Lab 13 : Reverse Engineering avec Ghidra (Crackme XOR)

> **Pilier 3 — Embarqué / C-ASM x86-64**
> Ngagne Demba Dia · AngeVirusLab · Shadow Bytes Red Team · UCAD · 2026

[![Ghidra](https://img.shields.io/badge/tool-Ghidra-red.svg)]()
[![XOR Obfuscation](https://img.shields.io/badge/technique-XOR%200x13-orange.svg)]()
[![Crackme](https://img.shields.io/badge/type-crackme-blue.svg)]()
[![Solved](https://img.shields.io/badge/Lab-Solved-brightgreen.svg)]()

---

## 1. TL;DR

**Contexte :** Binaire crackme — mot de passe obfusqué par XOR 0x13 (invisible via `strings`)  
**Technique :** Analyse statique Ghidra + décompileur → identifier la boucle XOR → décoder le mot de passe  
**Résultat :** `ShadowBytes` → FLAG : `AngeVirus{ghidra_reverse_engineering}`

---

## 2. Contexte : pourquoi Ghidra ?

La commande `strings ./target` ne révèle pas le mot de passe — les octets encodés ne forment pas une chaîne ASCII lisible. Seule l'analyse statique du code assembleur (ou du décompileur Ghidra) permet de retrouver la logique XOR et donc le mot de passe en clair.

---

## 3. Code vulnérable — `target.c`

```c
#include <stdio.h>
#include <string.h>

void win() {
    printf(">>> FLAG : AngeVirus{ghidra_reverse_engineering} <<<\n");
}

// Mot de passe encodé XOR 0x13 — invisible dans strings
int check(const char* input) {
    unsigned char encoded[] = {
        0x40, 0x7b, 0x72, 0x77, 0x7c, 0x64,  // S h a d o w
        0x51, 0x6a, 0x67, 0x76, 0x60,         // B y t e s
        0x00
    };
    char decoded[12];
    for (int i = 0; i < 11; i++)
        decoded[i] = encoded[i] ^ 0x13;
    decoded[11] = '\0';

    return strcmp(input, decoded) == 0;
}

int main() {
    char input[64];
    printf("Password : ");
    fgets(input, sizeof(input), stdin);
    input[strcspn(input, "\n")] = 0;

    if (check(input)) win();
    else printf("Wrong password.\n");
    return 0;
}
```

**Compilation :**
```bash
gcc -g -no-pie -o target target.c
```

---

## 4. Analyse — étape par étape

### 4.1 strings — échec attendu

```bash
strings ./target | grep -i shadow
# (rien — les octets XORés ne forment pas une chaîne lisible)
```

### 4.2 Ghidra — décompileur

Ouvrir le binaire dans Ghidra → analyser → naviguer vers `check()`.

Le décompileur produit :

```c
int check(char *input) {
    uchar encoded [12];
    char decoded [12];
    int i;

    encoded[0]  = 0x40;  encoded[1]  = 0x7b;  encoded[2]  = 0x72;
    encoded[3]  = 0x77;  encoded[4]  = 0x7c;  encoded[5]  = 0x64;
    encoded[6]  = 0x51;  encoded[7]  = 0x6a;  encoded[8]  = 0x67;
    encoded[9]  = 0x76;  encoded[10] = 0x60;  encoded[11] = 0;

    for (i = 0; i < 11; i++)
        decoded[i] = encoded[i] ^ 0x13;       // ← clé visible !
    decoded[11] = '\0';

    return strcmp(input, decoded) == 0;
}
```

**Observation clé :** XOR key = `0x13`, tableau de 11 octets.

### 4.3 GDB — validation dynamique

```bash
gdb ./target
(gdb) break check
(gdb) run
Password : test
(gdb) x/s $rsp+0xXX    # inspecter decoded[] après la boucle
# → "ShadowBytes"
```

### 4.4 Décodage offline

```
0x40 ^ 0x13 = 0x53 → 'S'
0x7b ^ 0x13 = 0x68 → 'h'
0x72 ^ 0x13 = 0x61 → 'a'
0x77 ^ 0x13 = 0x64 → 'd'
0x7c ^ 0x13 = 0x6f → 'o'
0x64 ^ 0x13 = 0x77 → 'w'
0x51 ^ 0x13 = 0x42 → 'B'
0x6a ^ 0x13 = 0x79 → 'y'
0x67 ^ 0x13 = 0x74 → 't'
0x76 ^ 0x13 = 0x65 → 'e'
0x60 ^ 0x13 = 0x73 → 's'
→ "ShadowBytes"
```

---

## 5. Solve — `solve.py`

```python
from pwn import *

encoded = [0x40, 0x7b, 0x72, 0x77, 0x7c, 0x64,
           0x51, 0x6a, 0x67, 0x76, 0x60]
password = ''.join(chr(b ^ 0x13) for b in encoded)
log.info(f"Mot de passe retrouvé : {password}")

p = process('./target')
p.recvuntil(b'Password : ')
p.sendline(password.encode())

output = p.recvall(timeout=2)
log.success(output.decode().strip())
```

---

## 6. Résultat

```
[*] Mot de passe retrouvé : ShadowBytes
[+] >>> FLAG : AngeVirus{ghidra_reverse_engineering} <<<
```

> Screenshot : [docs/lab13_ghidra_re.png](docs/lab13_ghidra_re.png)

---

## 7. Progression Reverse Engineering

| Lab | Technique | Outil |
| --- | --- | --- |
| Lab05 | ret2libc | pwntools |
| Lab10 | ret2syscall | pwntools + GDB |
| **Lab13** | **XOR crackme** | **Ghidra + GDB** |

---

## 8. Défense

| Vecteur | Mesure |
| --- | --- |
| XOR simple | Utiliser un chiffrement asymétrique ou dérivation de clé |
| Clé visible | Ne jamais stocker la clé dans le binaire |
| Décompilation | Obfuscation + packing (UPX, custom packer) |
| `strings` | Fragmenter les chaînes, éviter les constantes en clair |

---

## Résumé technique

| Élément | Valeur |
| --- | --- |
| Obfuscation | XOR key 0x13 |
| Mot de passe | ShadowBytes |
| FLAG | AngeVirus{ghidra_reverse_engineering} |
| Outil principal | Ghidra décompileur |
| Commande clé | `strings` (inefficace) → Ghidra (succès) |

---

*Ngagne Demba Dia · AngeVirusLab · Shadow Bytes Red Team · UCAD · Dakar, 2026*
