# local-llm-agent

> **Deploy a fully observable local LLM agent with LangFuse tracing**
> Ngagne Demba Dia · Master Sécurité des Systèmes Embarqués · UCAD · LLMOps

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

The agent is equipped with **3 tools** that demonstrate different observability scenarios:

| Tool | Purpose | Security angle |
| --- | --- | --- |
| `calculator` | Math evaluation (safe) | Baseline — no risk |
| `web_search` | Simulated knowledge retrieval | Information leakage |
| `execute_command` | System command execution | **OWASP LLM08** — Excessive Agency |

**Key question answered:** *How do you know what your LLM is doing in production
if you can't see it — and how do you detect when it does something it shouldn't?*

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
| GPU VRAM used | 5816 MB / 6144 MB (94.7%) |
| Latency — warm (GPU) | 7.92 s |
| Latency — cold start | 22.68 s |
| TTFT | 0.61 s |
| Estimated cost / call | $0.00 (local) |
| Traces captured | 2+ |

> Screenshots: [`docs/dashboard_traces.png`](docs/dashboard_traces.png) · [`docs/trace_details.png`](docs/trace_details.png)
> Agent traces: [`docs/agent_traces_list.png`](docs/agent_traces_list.png) · [`docs/agent_calculator_spans.png`](docs/agent_calculator_spans.png) · [`docs/agent_execute_command_spans.png`](docs/agent_execute_command_spans.png)

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
cd AngeVirusLab-LLMOps/llmops/local-llm-agent

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

1. **LangFuse reads keys from env** — `CallbackHandler()` with no args is all you need; hardcoding keys in code is both insecure and unnecessary.
2. **Cold start is real** — 22.68s first call vs 7.92s warm. TTFT (0.61s) stays fast once loaded.
3. **6 GB VRAM is enough** — LLaMA3:8b Q4_K_M uses 5816 MB / 6144 MB. Tight but functional.
4. **Language must be explicit** — without `"Réponds uniquement en français"`, LLaMA3 can respond in the wrong language based on lexical similarity.
5. **Observability catches drift** — every input/output is traced. Reproducing a "weird response" goes from impossible to trivial.

---

## References

- Lewis et al. (2020). *Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks*. arXiv:2005.11401
- Huyen, C. (2023). *Building LLM Applications for Production*. huyenchip.com
- LangFuse Documentation. *Tracing & Observability*. langfuse.com/docs
- Ollama. *Run Large Language Models Locally*. ollama.ai

---

*Ngagne Demba Dia · Master Sécurité des Systèmes Embarqués · UCAD · Dakar, 2026*
