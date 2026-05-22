# AI-Assisted Embedded Hardware Attack Framework

> **Projet signature — Master Sécurité des Systèmes Embarqués**
> Ngagne Demba Dia · AngeVirusLab · UCAD · 2026

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![LangChain](https://img.shields.io/badge/LangChain-0.3+-green.svg)
![Ollama](https://img.shields.io/badge/LLM-LLaMA3.1-orange.svg)
![Architecture](https://img.shields.io/badge/Arch-x86%2FARM%2FMIPS-purple.svg)

---

## Présentation

Framework d'analyse de firmware IoT assisté par LLM. Il automatise en 4 minutes
ce qui demande 2 heures d'analyse manuelle : extraction, détection d'architecture,
identification de vulnérabilités, et explication en langage naturel.

Ce projet ferme la boucle entre les 4 domaines du programme LLMSecOps :

```
LLMOps (LLMOps/RAG/LangFuse) ──► Module 4 : LLM-assisted explanation
Cloud Pentest (ARM exploitation)    ──► Module 2 : Architecture detection
Embedded Security (MIPS/Firmware IoT)   ──► Module 1 : Firmware extraction
                                    Module 3 : Vulnerability analysis
```

---

## Architecture

```text
Firmware binaire (input)
        │
        ▼
┌─────────────────────────────┐
│  Module 1 — Extraction      │  binwalk → SquashFS → filesystem
└──────────────┬──────────────┘
               │
        ▼
┌─────────────────────────────┐
│  Module 2 — Architecture    │  file + ELF magic → ARM/MIPS/x86
└──────────────┬──────────────┘
               │
        ▼
┌─────────────────────────────┐
│  Module 3 — Vuln Analysis   │  strings · checksec · regex · backdoors
└──────────────┬──────────────┘
               │
        ▼
┌─────────────────────────────┐
│  Module 4 — LLM Explanation │  LLaMA3.1:8b · LangFuse tracing
└──────────────┬──────────────┘
               │
        ▼
  Rapport structuré (terminal + JSON)
```

---

## Installation

```bash
# Prérequis système (Linux/WSL)
sudo apt install binwalk squashfs-tools checksec

# Python
cd projet-signature/
pip install -r requirements.txt

# LangFuse (optionnel)
cp .env.example .env
# Remplir LANGFUSE_SECRET_KEY et LANGFUSE_PUBLIC_KEY

# Ollama + modèle
ollama pull llama3.1:8b
```

---

## Utilisation

### Analyse complète (firmware fictif Lab22)

```bash
python main.py --firmware ../pilier-3-casm-embedded/lab22-firmware-iot/firmware.bin
```

### Sans LLM (mode rapide)

```bash
python main.py --firmware firmware.bin --skip-llm
```

### Si extraction déjà faite

```bash
python main.py --firmware firmware.bin --skip-extract
```

### Sortie JSON pour intégration

```bash
python main.py --firmware firmware.bin --skip-llm --json > rapport.json
```

---

## Exemple de sortie

```
━━━━━━━━━━━━━━━━━━━━ AI-Assisted Embedded Hardware Attack Framework ━━━━━━━━━━━━━━━━━━━━

▶ Module 1 — Firmware Extraction
  ✓ Firmware : 8 200 bytes
  8         0x8   Squashfs filesystem, little endian, lzma compression
  ✓ Filesystem extrait : /path/squashfs-root/

▶ Module 2 — Architecture Detection
  ✓ Architecture dominante : MIPSEL
  MIPSEL : 1 binaire(s)
  Binaires analysés : 1

▶ Module 3 — Vulnerability Analysis
  ┌──────────────────────────────────────────┐
  │           Rapport de vulnérabilités      │
  ├──────────────────────────────┬───────────┤
  │ Credentials hardcodés        │         3 │
  │ Fichiers cachés              │         1 │
  │ Binaires avec fonctions dang.│         1 │
  │ Backdoors                    │         1 │
  └──────────────────────────────┴───────────┘

▶ Module 4 — LLM-Assisted Analysis
  ╭─────────────────── Analyse LLM ──────────────────────╮
  │ 1. Résumé exécutif                                    │
  │    Firmware critique — 3 credentials en clair,        │
  │    backdoor nc sur port 31337, strcpy exploitable.    │
  │                                                       │
  │ 2. Vulnérabilités critiques                           │
  │    [Critical] Credentials admin en clair              │
  │    [Critical] Backdoor shell non authentifié          │
  │    [High]     strcpy sans vérification → RCE          │
  │    [Medium]   Hash MD5 faible (bruteforce)            │
  │                                                       │
  │ 3. Vecteurs d'exploitation                            │
  │    → Connexion directe port 31337                     │
  │    → Auth HTTP avec credentials extraits              │
  │    → BoF sur parse_auth() → shell (Lab23)             │
  │                                                       │
  │ 4. Recommandations                                    │
  │    → Chiffrer les credentials (vault/HSM)             │
  │    → Supprimer backdoor dev avant production          │
  │    → Utiliser strncpy + validation de taille          │
  │    → Activer stack protector (-fstack-protector)      │
  ╰───────────────────────────────────────────────────────╯
```

---

## Modules

| Module | Fichier | Dépendances |
|---|---|---|
| 1 — Extraction | `modules/m1_extractor.py` | `binwalk`, `unsquashfs` |
| 2 — Architecture | `modules/m2_detector.py` | `file` (system) |
| 3 — Analyse | `modules/m3_analyzer.py` | `strings`, `checksec` |
| 4 — LLM | `modules/m4_llm.py` | `langchain-ollama`, `langfuse` |

---

## Connexion avec les labs

| Lab | Contribution au framework |
|---|---|
| Lab22 — Firmware IoT | Firmware de test + pipeline d'extraction |
| Lab23 — httpd BoF | Démontre l'exploitabilité des findings du Module 3 |
| LLMOps — RAG/LangFuse | Architecture Module 4 (LLM + tracing) |
| Labs 18-21 — ARM/MIPS | Signatures architecture détectées par Module 2 |

---

Ngagne Demba Dia · AngeVirusLab · Master Sécurité des Systèmes Embarqués · UCAD · Dakar, 2026
