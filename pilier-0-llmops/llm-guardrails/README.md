# llm-guardrails

> **Input + Output rails — anti prompt injection sur agent LLM local**
> Ngagne Demba Dia · Master Sécurité des Systèmes Embarqués · UCAD · Pilier 0 · Week 5

[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![NeMo Guardrails](https://img.shields.io/badge/NeMo-Guardrails-76B900?logo=nvidia)](https://github.com/NVIDIA/NeMo-Guardrails)
[![LangFuse](https://img.shields.io/badge/LangFuse-OSS-orange.svg)](https://langfuse.com)
[![OWASP LLM01](https://img.shields.io/badge/OWASP-LLM01-red.svg)](https://owasp.org/www-project-top-10-for-llm-applications/)

---

## Overview

This project implements two layers of guardrails on a local LLM agent:

- **Input rail** — detects and blocks prompt injection attempts before they reach the LLM
- **Output rail** — detects and blocks dangerous content in the LLM's response

Two implementations are compared:
1. **Custom Python guardrails** — regex-based, zero dependency, fully transparent
2. **NeMo Guardrails** (NVIDIA) — Colang-based dialogue flow control

---

## Architecture

```
User Input
    │
    ▼
┌─────────────────┐
│   INPUT RAIL    │ ← regex patterns (injection, jailbreak, DAN...)
│  (OWASP LLM01)  │
└────────┬────────┘
         │ ALLOWED only
         ▼
┌─────────────────┐
│   LLM (Ollama)  │ ← LLaMA3.1:8b · traced in LangFuse
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   OUTPUT RAIL   │ ← regex patterns (rm -rf, SQL DROP, API keys...)
│  (OWASP LLM02)  │
└────────┬────────┘
         │ ALLOWED only
         ▼
    User Response
```

---

## Results

| Test | Type | Expected | Result |
| --- | --- | --- | --- |
| normal_llmops | Normal | ALLOWED | — |
| normal_securite | Normal | ALLOWED | — |
| normal_cloud | Normal | ALLOWED | — |
| inject_override | Injection | BLOCKED | — |
| inject_dan | DAN jailbreak | BLOCKED | — |
| inject_context_wipe | Context wipe | BLOCKED | — |
| inject_role_tag | Role tag | BLOCKED | — |
| inject_inst_tag | Instruction tag | BLOCKED | — |
| output_dangerous_cmd | Dangerous output | BLOCKED | — |

> Screenshots: see [docs/](docs/)

---

## Setup

```bash
cd AngeVirusLab-LLMOps/pilier-0-llmops/llm-guardrails
cp ../local-llm-agent/.env .

# Custom guardrails
python src/agent.py

# NeMo Guardrails
python nemo/demo.py
```

---

## Key Learnings

- Les guardrails custom (regex Python) sont plus fiables que NeMo pour un stack LLM local — zéro dépendance, comportement prévisible
- La sécurité native d'un LLM (safety training) peut être contournée par jailbreak, persona override, context wipe — les guardrails constituent une couche indépendante
- Les guardrails agissent sur les **patterns textuels**, pas sur l'intention — ils bloquent AVANT que le LLM soit appelé (zéro token consommé)
- Defense in depth : safety training + guardrails + monitoring (LangFuse) = trois couches indépendantes

## NeMo Guardrails — Limitation connue

NeMo Guardrails utilise un LLM pour interpréter les règles Colang (semantic matching). Avec Ollama en local, deux problèmes bloquants ont été identifiés :

1. **API OpenAI-compatible** (`http://localhost:11434/v1`) — NeMo envoie des requêtes au format OpenAI mais Ollama retourne `{'role': 'assistant', 'content': ''}` (contenu vide)
2. **ChatOllama direct** (`llm=ChatOllama(...)`) — même avec le paramètre `llm=`, NeMo retourne des réponses vides car le matching sémantique Colang échoue silencieusement

**Conclusion** : NeMo Guardrails est conçu pour fonctionner avec des LLMs cloud (OpenAI, Azure). Pour un stack 100% local avec Ollama, les guardrails custom Python sont l'alternative fiable.

---

*Ngagne Demba Dia · Master Sécurité des Systèmes Embarqués · UCAD · Dakar, 2026*
