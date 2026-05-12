# rag-pipeline

> **RAG Pipeline — Retrieval-Augmented Generation sur corpus de sécurité matérielle**
> Ngagne Demba Dia · Master Sécurité des Systèmes Embarqués · UCAD · Pilier 0 · Week 6

[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-Vectorstore-orange.svg)](https://www.trychroma.com)
[![LangChain](https://img.shields.io/badge/LangChain-RAG-blue.svg)](https://langchain.com)
[![RAGAS](https://img.shields.io/badge/RAGAS-Evaluation-green.svg)](https://docs.ragas.io)
[![OWASP LLM](https://img.shields.io/badge/OWASP-LLM02%20%7C%20LLM10-red.svg)](https://owasp.org/www-project-top-10-for-llm-applications/)

---

## Overview

This project implements a complete RAG (Retrieval-Augmented Generation) pipeline on a local LLM using a corpus of 13 hardware security documents.

Three stages:
1. **Ingest** — PDF loading, chunking, embedding, ChromaDB vectorstore
2. **Generate** — retrieval + LLM answer grounded in source documents
3. **Evaluate** — RAGAS metrics (faithfulness, answer relevancy) + manual metrics

---

## Architecture

```
PDF Documents (13 files)
        │
        ▼
┌─────────────────────┐
│     ingest.py       │ ← PyPDF + RecursiveCharacterTextSplitter
│  1360 pages         │   chunk_size=1000, overlap=200
│  3387 chunks        │
└────────┬────────────┘
         │ HuggingFace Embeddings
         │ paraphrase-multilingual-MiniLM-L12-v2
         ▼
┌─────────────────────┐
│  ChromaDB           │ ← vectorstore local persistant
│  (chroma_db/)       │
└────────┬────────────┘
         │ Retrieval k=4
         ▼
┌─────────────────────┐
│     rag.py          │ ← LangChain RAG chain
│  LLaMA3.1:8b        │   retrieve → prompt → generate
│  (Ollama local)     │
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│   evaluate.py       │ ← RAGAS + métriques manuelles
│  faithfulness       │
│  answer_relevancy   │
└─────────────────────┘
```

---

## Corpus

| Document | Domaine |
| --- | --- |
| The-Trojan-Horse-in-Your-Code.pdf | Hardware Trojans |
| FLARE Malware Analysis Crash Course.pdf | Malware Analysis |
| H A R D W A R E H A C K I N G HANDBOOK.pdf | Hardware Hacking |
| ISO-IEC-15408-1-2009.pdf | Common Criteria (FR) |
| ISO-IEC-15408-1-2022.pdf | Common Criteria (EN) |
| The Car Hacker's Handbook.pdf | Automotive Security |
| Understanding Cryptography — Christof Paar.pdf | Cryptography |
| originalhackingmanual.pdf | Hacking Techniques |
| 3-540-* / 978-3-540-* | Academic Security Papers |

---

## Results

### RAGAS Evaluation

| Question | Faithfulness | Answer Relevancy |
| --- | --- | --- |
| Hardware Trojan horse | — | 0.062 |
| Common Criteria EALs | 0.50 | 0.726 |
| Side-channel attack | — | 0.693 |
| CAN bus vulnerabilities | **1.00** | **0.959** |
| Static malware analysis | 0.50 | 0.827 |

### Manuel Metrics

| Metric | Score |
| --- | --- |
| Context Hit Rate (avg) | 0.20 |
| Answer Coverage (avg) | 0.14 |
| No hallucination | 2/5 |

> Screenshots: see [docs/](docs/)

---

## Key Learnings

- Un RAG est aussi bon que son corpus : CAN bus (score 1.0) vs Hardware Trojan (score 0.06) selon la richesse des documents sur le sujet
- Le chunking (taille, overlap) impacte directement la qualité du retrieval
- RAGAS avec un LLM local (LLaMA3.1:8b) comme juge est fonctionnel mais plus lent qu'avec GPT-4
- OWASP LLM02 — Insecure Output : le RAG peut générer du contenu dangereux si le corpus contient des documents malveillants (RAG Poisoning)
- OWASP LLM10 — Model Theft : le vectorstore doit être protégé en production

---

## Setup

```bash
cd AngeVirusLab-LLMOps/pilier-0-llmops/rag-pipeline
cp ../local-llm-agent/.env .

# 1 — Ingestion (une seule fois)
python src/ingest.py

# 2 — Generation
python src/rag.py

# 3 — Evaluation
python src/evaluate.py
```

**Requirements**
```
chromadb
langchain-chroma
langchain-community
langchain-text-splitters
sentence-transformers
ragas
pypdf
python-dotenv
langchain-ollama
```

---

*Ngagne Demba Dia · Master Sécurité des Systèmes Embarqués · UCAD · Dakar, 2026*
