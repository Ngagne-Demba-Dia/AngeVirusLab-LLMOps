# prompt-tracker

> **Prompt versioning + A/B testing with LangFuse**
> Ngagne Demba Dia · Master Sécurité des Systèmes Embarqués · UCAD · LLMOps

[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![LangFuse](https://img.shields.io/badge/LangFuse-Prompts-orange.svg)](https://langfuse.com)
[![Ollama](https://img.shields.io/badge/Ollama-LLaMA3.1:8b-black.svg)](https://ollama.ai)

---

## Overview

This project demonstrates **prompt versioning** as a core LLMOps practice.
Prompts are stored and versioned in LangFuse (not hardcoded in source code),
and an A/B test runner compares all versions on the same model.

**Key question answered:** *Which prompt version produces the best output
for a given task — and how do you measure it systematically?*

---

## Prompts tested

| Version | Topic | Style |
| --- | --- | --- |
| v1 | LLMOps | Direct, minimal instructions |
| v2 | Cloud Security | Role + structured output format |
| v3 | Embedded Security | Role + pedagogical constraints |

---

## Results

| Version | Topic | Latency | TTFT | Output |
| --- | --- | --- | --- | --- |
| v1 | LLMOps | 33.13s | 16.74s | 1266 chars — **hallucination détectée** |
| v2 | Cloud Security | 11.46s | 0.43s | 773 chars — réponse concise et correcte |
| v3 | Embedded Security | 28.45s | 0.37s | 2034 chars — réponse pédagogique détaillée |

**Finding critique — v1 :** LLaMA3.1:8b a défini LLMOps comme *"Low-Code Machine Learning Operations"*
au lieu de *"Large Language Model Operations"* — hallucination capturée en temps réel par LangFuse.
Sans observabilité, cette erreur factuelle passerait inaperçue en production.

**Finding performance — v2 :** Un prompt avec rôle explicite + format de sortie structuré
réduit la latence de 65% (33s → 11s) et produit une réponse plus précise.

> Screenshots: [`docs/ab_test_traces_list.png`](docs/ab_test_traces_list.png) · [`docs/ab_test_v1_hallucination.png`](docs/ab_test_v1_hallucination.png)

---

## Setup

```bash
cd AngeVirusLab-LLMOps/llmops/prompt-tracker
cp ../local-llm-agent/.env .
python src/ab_test.py
```

---

## Key Learnings

1. **Hallucinations sont invisibles sans tracing** — v1 a halluciné la définition de LLMOps (Low-Code vs Large Language). LangFuse l'a capturé ; sans observabilité, ça passe en production sans qu'on le sache.
2. **Le style du prompt impacte directement la latence** — rôle + format structuré (v2) = 3× plus rapide que prompt minimal (v1). Pas besoin de changer le modèle.
3. **Les prompts appartiennent au registry, pas au code** — versionner dans LangFuse permet de rollback, de comparer, et d'auditer sans toucher le codebase.
4. **TTFT révèle le comportement du modèle** — v2 : TTFT 0.43s pour 11.46s total = génération rapide et courte. v1 : TTFT 16.74s = le modèle a "réfléchi" longtemps avant de répondre (et mal).

---

*Ngagne Demba Dia · Master Sécurité des Systèmes Embarqués · UCAD · Dakar, 2026*
