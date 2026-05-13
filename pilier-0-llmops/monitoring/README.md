# monitoring

> **Monitoring LLM en production — Prometheus + Grafana + LangFuse**
> Ngagne Demba Dia · Master Sécurité des Systèmes Embarqués · UCAD · Pilier 0 · Week 7

[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![Prometheus](https://img.shields.io/badge/Prometheus-Metrics-orange.svg)](https://prometheus.io)
[![Grafana](https://img.shields.io/badge/Grafana-Dashboard-yellow.svg)](https://grafana.com)
[![LangFuse](https://img.shields.io/badge/LangFuse-Observabilite-purple.svg)](https://langfuse.com)

---

## Overview

Pipeline de monitoring complet pour un LLM local (LLaMA3.1:8b via Ollama) :

1. **LangFuse** — stocke les traces LLM (input, output, latence)
2. **Prometheus Exporter** — interroge l'API LangFuse, calcule les métriques, les expose sur `/metrics`
3. **Prometheus** — scrape les métriques toutes les 15s
4. **Grafana** — dashboard avec 5 métriques clés + alerting

---

## Architecture

```
LLM Agent (LangChain)
      │ traces
      ▼
LangFuse API (cloud.langfuse.com)
      │ REST API /api/public/traces
      ▼
exporter.py (port 8000)  ← prometheus_client
      │ /metrics
      ▼
Prometheus (port 19090)  ← scrape toutes les 15s
      │ PromQL
      ▼
Grafana (port 13000)     ← dashboard 5 métriques
```

---

## Les 5 métriques

| Métrique | Query Prometheus | Description |
| --- | --- | --- |
| **Latence P95** | `llm_latency_p95_ms` | 95e percentile du temps de réponse (ms) |
| **Tokens moyens** | `llm_tokens_total_avg` | Tokens input+output moyens par requête |
| **Error Rate** | `llm_error_rate_percent` | % de traces avec niveau ERROR ou WARNING |
| **Hallucination Rate** | `llm_hallucination_rate` | % de réponses hors contexte (proxy) |
| **Throughput** | `llm_throughput_rpm` | Requêtes par minute sur la dernière heure |

---

## Résultats observés

| Métrique | Valeur | Analyse |
| --- | --- | --- |
| Latence P95 | 34095 ms | Normal pour LLaMA3.1:8b en local sur CPU/GPU |
| Tokens moyens | No data | Voir explication ci-dessous |
| Error Rate | 0% | Aucune erreur détectée |
| Hallucination Rate | 0% | Aucune réponse hors contexte |
| Throughput | ~0 req/min | Usage de lab, pas de production |

> Screenshots: see [docs/](docs/)

---

## Pourquoi "No data" sur les Tokens dans Grafana ?

Le panneau **Tokens moyens par requête** affiche "No data" pour une raison technique précise :

**LangFuse ne stocke pas les tokens dans le champ `usage` des traces** lorsque le LLM est appelé via l'intégration LangChain (`CallbackHandler`).

Voici pourquoi :

1. **LangChain CallbackHandler** enregistre les traces dans LangFuse via des événements (`on_llm_start`, `on_llm_end`). Les informations de tokens sont transmises uniquement si le LLM les retourne explicitement dans sa réponse.

2. **Ollama (LLaMA local)** retourne les tokens consommés dans sa réponse API, mais le `CallbackHandler` LangFuse ne mappe pas toujours ce champ vers `usage.input` / `usage.output` dans la trace — selon la version du SDK.

3. **Résultat** : l'API REST `/api/public/traces` retourne `"usage": null` ou `"usage": {"input": 0, "output": 0}` pour ces traces → le calcul de moyenne donne 0 ou None → Grafana affiche "No data".

**Solutions en production :**
- Utiliser `langfuse.generation(usage=Usage(input=n, output=m))` pour logger manuellement les tokens
- Utiliser un LLM via OpenAI API qui retourne toujours les tokens
- Interroger les spans individuels (pas les traces) via `/api/public/observations`

Cette limitation est documentée et ne remet pas en cause l'architecture de monitoring — les 4 autres métriques fonctionnent correctement.

---

## Setup

```bash
cd AngeVirusLab-LLMOps/pilier-0-llmops/monitoring
cp ../local-llm-agent/.env .

# Terminal 1 — Exporter
pip install prometheus_client requests
python src/exporter.py

# Terminal 2 — Prometheus + Grafana
docker compose up -d
```

**Accès :**
- Prometheus : http://localhost:19090
- Grafana : http://localhost:13000 (admin / angevirus)

**Datasource Grafana :** `http://angevirus_prometheus:9090`

---

*Ngagne Demba Dia · Master Sécurité des Systèmes Embarqués · UCAD · Dakar, 2026*
