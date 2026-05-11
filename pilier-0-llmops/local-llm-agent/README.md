# local-llm-agent

> **Deploy a fully observable local LLM agent with LangFuse tracing**
> Shadow Bytes · Pilier 0 · Week 3

[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![LangChain](https://img.shields.io/badge/LangChain-0.2-green.svg)](https://python.langchain.com)
[![LangFuse](https://img.shields.io/badge/LangFuse-OSS-orange.svg)](https://langfuse.com)
[![Ollama](https://img.shields.io/badge/Ollama-LLaMA3:8b-black.svg)](https://ollama.ai)
[![CUDA](https://img.shields.io/badge/CUDA-12.0-76B900?logo=nvidia)](https://developer.nvidia.com/cuda)

---

## Overview

This project deploys a **local LLM agent** (LLaMA3:8b via Ollama) with complete
observability through LangFuse. Every LLM call is traced — latency, token usage,
cost estimate, and tool calls are all visible in the dashboard.

**Key question answered:** *How do you know what your LLM is doing in production
if you can't see it?*

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                  User Query                         │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│              LangChain Agent                        │
│   ┌─────────────┐    ┌──────────────────────────┐   │
│   │  LLM Chain  │    │  Tools (calculator, etc) │   │
│   └──────┬──────┘    └──────────────────────────┘   │
│          │                                          │
│   LangFuse CallbackHandler (instruments everything) │
└──────────┬──────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────┐
│              Ollama (local)                         │
│              LLaMA3:8b · CUDA 12.0 · 6GB VRAM       │
└─────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────┐
│              LangFuse Dashboard                     │
│   Traces · Latency P95 · Token usage · Cost         │
└─────────────────────────────────────────────────────┘
```

---

## Results

| Metric | Value |
|---|---|
| Model | LLaMA3:8b (Q4_K_M) |
| GPU VRAM used | ~5.8 GB / 6 GB |
| Avg latency | — ms *(fill after lab)* |
| Tokens/response | — *(fill after lab)* |
| Traces captured | — *(fill after lab)* |

> Screenshots: see [docs/](docs/)

---

## Setup

### Prerequisites
```bash
# WSL2 Ubuntu + NVIDIA CUDA 12.0
ollama --version   # Ollama installed
python3 --version  # Python 3.10+
```

### Install
```bash
git clone https://github.com/Ngagne-Demba-Dia/AngeVirusLab-LLMOps
cd AngeVirusLab-LLMOps/pilier-0-llmops/local-llm-agent

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Configure LangFuse
```bash
cp .env.example .env
# Edit .env — add your LangFuse keys from cloud.langfuse.com
```

### Run
```bash
python3 src/agent.py
```

---

## Project Structure

```
local-llm-agent/
├── src/
│   ├── agent.py          ← main agent with LangFuse instrumentation
│   ├── tools.py          ← custom tools for the agent
│   └── config.py         ← configuration (model, LangFuse keys)
├── docs/
│   ├── architecture.png  ← architecture diagram
│   └── dashboard.png     ← LangFuse dashboard screenshot
├── paper.md              ← technical paper (FR)
├── blog.md               ← blog post (FR)
├── requirements.txt
├── .env.example
└── README.md
```

---

## Key Learnings

- *To be filled after completing the lab*

---

## References

- Lewis et al. (2020). *Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks*. arXiv:2005.11401
- Huyen, C. (2023). *Building LLM Applications for Production*. huyenchip.com
- LangFuse Documentation. *Tracing & Observability*. langfuse.com/docs
- Ollama. *Run Large Language Models Locally*. ollama.ai

---

*Shadow Bytes Red Team · UCAD · Dakar — AngeVirus 2026*
