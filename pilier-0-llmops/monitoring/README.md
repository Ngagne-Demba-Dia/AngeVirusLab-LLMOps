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

1. **LangFuse** — stocke les traces LLM (input, output, latence, tokens)
2. **Prometheus Exporter** — interroge l'API LangFuse, calcule les métriques, les expose sur `/metrics`
3. **Prometheus** — scrape les métriques toutes les 15s
4. **Grafana** — dashboard avec 5 métriques clés

---

## Architecture

```text
LLM Agent (LangChain + LangFuse 4.x)
      │ traces + token counts
      ▼
LangFuse API (cloud.langfuse.com)
      │ REST API /api/public/traces + /api/public/observations
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

| Métrique | Gauge Prometheus | Description |
| --- | --- | --- |
| **Latence P95** | `llm_latency_p95_ms` | 95e percentile du temps de réponse (ms) |
| **Tokens moyens** | `llm_tokens_total_avg` | Tokens input+output moyens par requête |
| **Error Rate** | `llm_error_rate_percent` | % de traces avec niveau ERROR ou WARNING |
| **Hallucination Rate** | `llm_hallucination_rate` | % de réponses hors contexte (proxy) |
| **Throughput** | `llm_throughput_rpm` | Requêtes par minute sur la dernière heure |

---

## Phase 1 — Infrastructure (Week 7)

Mise en place du stack de monitoring :

| Composant | Valeur observée | Analyse |
| --- | --- | --- |
| Latence P95 | 34 095 ms | Normal pour LLaMA3.1:8b en local |
| Tokens moyens | No data | Voir fix Phase 2 |
| Error Rate | 0% | Aucune erreur détectée |
| Hallucination Rate | 0% | Aucune réponse hors contexte |
| Throughput | ~0 req/min | Usage de lab |

> Screenshots Phase 1 : [docs/grafanna_Dashboard.png](docs/grafanna_Dashboard.png) · [docs/prometheus_targets.png](docs/prometheus_targets.png) · [docs/exporter_metrique.png](docs/exporter_metrique.png)

---

## Phase 2 — Fix tokens + génération de trafic

### Problème identifié : "No data" sur les Tokens

En Phase 1, le panel **Tokens moyens** affichait "No data". Cause : une incompatibilité entre LangFuse v4.x et l'exporter.

**Deux sources du problème :**

### 1. LangFuse v4.x stocke les tokens dans les observations, pas les traces

L'exporter interrogeait `GET /api/public/traces` et lisait `t.get("usage")` :

```python
usage = t.get("usage") or {}  # → toujours null en v4.x
```

En LangFuse v4.x, les token counts sont dans les **observations** (générations) :

```json
GET /api/public/observations?type=GENERATION
→ { "usage": { "input": 1083, "output": 9, "total": 1092 } }
```

**Fix :** l'exporter fait maintenant deux appels API — traces pour la latence/erreurs, observations pour les tokens.

### 2. Le pipeline utilisait `CallbackHandler` qui ne trackait pas les tokens

Avec l'ancienne intégration LangChain (`CallbackHandler`), les tokens Ollama n'étaient pas transmis à LangFuse. Le pipeline a été réécrit pour LangFuse 4.x avec tracking manuel :

```python
# LangFuse 4.x — context manager pour tracker les tokens
with self.langfuse.start_as_current_observation(
    name=run_name, as_type="generation", model=OLLAMA_MODEL,
) as gen:
    llm_response = self.llm.invoke(messages)
    meta = llm_response.response_metadata
    gen.update(usage_details={
        "input":  meta.get("prompt_eval_count", 0),  # tokens Ollama
        "output": meta.get("eval_count", 0),
        "total":  meta.get("prompt_eval_count", 0) + meta.get("eval_count", 0),
    })
```

### Résultats Phase 2

Après 15 appels LLM via `load_test.py` :

| Métrique | Valeur | Analyse |
| --- | --- | --- |
| Latence P95 | 43 030 ms | Cohérent avec Phase 1 |
| Tokens input moy. | 652 | Prompt RAG (contexte 4 chunks) |
| Tokens output moy. | 76 | Réponse LLM |
| **Tokens total moy.** | **729** | Données réelles — plus de "No data" |
| Error Rate | 0% | Aucune erreur |
| Hallucination Rate | 33% | Proxy : réponses "not found in documents" |
| Throughput | 0.43 req/min | 15 requêtes sur ~35 minutes |

> Screenshots Phase 2 : [docs/phase2_dashboard.png](docs/phase2_dashboard.png) · [docs/phase2_traces.png](docs/phase2_traces.png) · [docs/phase2_loadtest.png](docs/phase2_loadtest.png)

---

## Setup

```bash
cd AngeVirusLab-LLMOps/pilier-0-llmops/monitoring
cp ../local-llm-agent/.env .

# Terminal 1 — Exporter
pip install prometheus_client requests numpy
python src/exporter.py

# Terminal 2 — Prometheus + Grafana
docker compose up -d
```

**Accès :**

- Prometheus : <http://localhost:19090>
- Grafana : <http://localhost:13000> (admin / angevirus)

**Datasource Grafana :** `http://angevirus_prometheus:9090`

---

Ngagne Demba Dia · Master Sécurité des Systèmes Embarqués · UCAD · Dakar, 2026
