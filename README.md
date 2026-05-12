# AngeVirusLab — LLMOps

> **Ngagne Demba Dia · Master Sécurité des Systèmes Embarqués · UCAD · Dakar**
> *AngeVirus · CCDOC · LACGAA 2026*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![Ollama](https://img.shields.io/badge/Ollama-LLaMA3-black.svg)](https://ollama.ai)
[![LangFuse](https://img.shields.io/badge/Observability-LangFuse-orange.svg)](https://langfuse.com)

---

## What is this?

This repository documents my **LLMOps specialization** — a structured 8-week program
covering the full operational lifecycle of Large Language Models:
from local deployment to production observability, RAG pipelines, and LLM security guardrails.

All projects run **100% open source, 0$ tooling** on a local GPU (NVIDIA + CUDA via WSL2).

---

## Stack

| Layer | Tools |
|---|---|
| **LLM Runtime** | Ollama · LLaMA3:8b |
| **Orchestration** | LangChain |
| **Observability** | LangFuse |
| **RAG** | ChromaDB · RAGAS |
| **Guardrails** | NeMo Guardrails (NVIDIA) |
| **Infra** | WSL2 · CUDA 12.0 · NVIDIA GPU |

---

## Projects

### Pilier 0 — LLMOps Foundations

| # | Project | Description | Status |
| --- | --- | --- | --- |
| 01 | [local-llm-agent](pilier-0-llmops/local-llm-agent/) | Local LLM agent (3 tools) with full LangFuse tracing | ✅ Done |
| 02 | [prompt-tracker](pilier-0-llmops/prompt-tracker/) | Prompt versioning + A/B testing + hallucination detection | ✅ Done |
| 03 | [llm-guardrails](pilier-0-llmops/llm-guardrails/) | NeMo Guardrails anti-injection rails | ⏳ Planned |
| 04 | [rag-pipeline](pilier-0-llmops/rag-pipeline/) | Full RAG: LangChain + ChromaDB + RAGAS eval | ⏳ Planned |
| 05 | [secure-rag](pilier-0-llmops/secure-rag/) | Final: RAG + guardrails + observability | ⏳ Planned |

---

## Hardware

```
CPU  : AMD Ryzen 7 5800H @ 3.2 GHz
RAM  : 40 GB DDR4
GPU  : NVIDIA GeForce (6 GB VRAM) — CUDA 12.0
OS   : WSL2 Ubuntu on Windows 11
```

---

## Context

This work is part of a **LLMSecOps specialization** conducted at UCAD (Dakar) as part of
the Master Sécurité des Systèmes Embarqués program.
The LLMOps pillar directly feeds into **LLM Security offensive research** (Pilier 1) —
building the pipeline first means understanding exactly where it breaks under attack.

---

## Author

**Ngagne Demba Dia** — AngeVirus
Master Sécurité des Systèmes Embarqués · UCAD · CCDOC · Dakar, Sénégal

[![GitHub](https://img.shields.io/badge/GitHub-Ngagne--Demba--Dia-black?logo=github)](https://github.com/Ngagne-Demba-Dia)
