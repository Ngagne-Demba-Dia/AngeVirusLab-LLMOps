# AngeVirusLab — LLMOps

> **Ngagne Demba Dia · Master Sécurité des Systèmes Embarqués · UCAD · Dakar**
> AngeVirus · Shadow Bytes Red Team · CCDOC · 2026

[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![Ollama](https://img.shields.io/badge/Ollama-LLaMA3.1:8b-black.svg)](https://ollama.ai)
[![LangFuse](https://img.shields.io/badge/Observability-LangFuse_4.x-orange.svg)](https://langfuse.com)
[![OWASP](https://img.shields.io/badge/OWASP-LLM01%20%7C%20LLM02-red.svg)](https://owasp.org/www-project-top-10-for-llm-applications/)

---

## What is this?

Pilier 0 d'un programme **LLMSecOps** de 31 semaines — les fondations LLMOps avant l'offensive.

8 semaines couvrant le cycle complet d'un LLM en production :
déploiement local → prompt engineering → guardrails → RAG → monitoring → pipeline sécurisé intégré.

Tout tourne **100% open source, 0$ tooling** sur GPU local (NVIDIA RTX 3060 + CUDA 12.4 via WSL2).

> Paper global : [paper.md](paper.md)

---

## Stack

| Couche | Outils |
| --- | --- |
| **LLM Runtime** | Ollama · LLaMA3.1:8b |
| **Orchestration** | LangChain |
| **Observabilité** | LangFuse 4.x |
| **RAG** | ChromaDB · RAGAS |
| **Guardrails** | InputRail + OutputRail (regex) |
| **Monitoring** | Prometheus + Grafana |
| **Infra** | WSL2 · CUDA 12.4 · NVIDIA RTX 3060 Laptop |

---

## Pilier 0 — LLMOps Foundations

| # | Lab | Description | Score |
| --- | --- | --- | --- |
| Week 1-2 | [local-llm-agent](pilier-0-llmops/local-llm-agent/) | Agent LLM local (3 outils) + tracing LangFuse complet | ✅ Done |
| Week 3-4 | [prompt-tracker](pilier-0-llmops/prompt-tracker/) | Versioning prompts + A/B testing + détection hallucination | ✅ Done |
| Week 5 | [llm-guardrails](pilier-0-llmops/llm-guardrails/) | InputRail + OutputRail — anti-injection regex (OWASP LLM01/02) | ✅ Done |
| Week 6 | [rag-pipeline](pilier-0-llmops/rag-pipeline/) | RAG complet : ChromaDB · 3387 chunks · RAGAS eval | ✅ Done |
| Week 7 | [monitoring](pilier-0-llmops/monitoring/) | Prometheus + Grafana + LangFuse exporter — 5 métriques | ✅ Done |
| Week 8 | [final-project](pilier-0-llmops/final-project/) | Secure RAG Pipeline : Guardrails + RAG + LangFuse — **8/8** | ✅ Done |

---

## Résultats clés

### Final Project — Secure RAG Pipeline (8/8)

```text
User Input → INPUT RAIL → RAG → LLM → OUTPUT RAIL → LangFuse → Grafana
```

- 5 menaces bloquées (injection, jailbreak, malware) — zéro token consommé
- 3 requêtes légitimes répondues avec sources documentaires
- Tokens loggués dans LangFuse : ~729 tokens/req (652 input + 76 output)
- Latence P95 : ~43 secondes (LLaMA3.1:8b local sur GPU)

### Monitoring — métriques temps réel

| Métrique | Valeur |
| --- | --- |
| Latence P95 | 43 030 ms |
| Tokens total moy. | 729 |
| Error Rate | 0% |
| Hallucination Rate | 33% (proxy : réponses "not found") |
| Throughput | 0.43 req/min |

---

## Hardware

```text
CPU : AMD Ryzen 7 5800H @ 3.2 GHz
RAM : 40 GB DDR4
GPU : NVIDIA GeForce RTX 3060 Laptop (6 GB VRAM) — CUDA 12.4
OS  : WSL2 Ubuntu sur Windows 11 Pro
```

---

## Pilier 1 — LLM Security Offensive

Labs PortSwigger Web Security Academy — LLM Attacks (4 labs couverts) :

| Lab | Niveau | Vulnérabilité |
| --- | --- | --- |
| Exploitation des API LLM avec autonomie excessive | APPRENTI | OWASP LLM08 — Excessive Agency |
| Exploitation des vulnérabilités dans les API LLM | PRATICIEN | OS Command Injection via LLM |
| Injection indirecte de prompt | PRATICIEN | Indirect Prompt Injection |
| Exploitation d'agents IA — actions destructives | APPRENTI | AI Agent Manipulation |

Axes couverts : Excessive Agency · OS Command Injection · Indirect Prompt Injection · AI Agent Exploitation

---

## Contexte

Ce Pilier 0 est la **fondation défensive** avant l'offensive.
Comprendre comment un pipeline LLM fonctionne en détail permet d'identifier exactement
où il est vulnérable — c'est l'objet du **Pilier 1 : LLM Security Offensive**.

---

**Ngagne Demba Dia** — AngeVirus
Master Sécurité des Systèmes Embarqués · UCAD · CCDOC · Dakar, Sénégal

[![GitHub](https://img.shields.io/badge/GitHub-Ngagne--Demba--Dia-black?logo=github)](https://github.com/Ngagne-Demba-Dia)
