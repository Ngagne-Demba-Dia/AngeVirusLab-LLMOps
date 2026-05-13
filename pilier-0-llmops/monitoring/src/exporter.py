import os
import time
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

import numpy as np
import requests
from requests.auth import HTTPBasicAuth
from prometheus_client import start_http_server, Gauge
from dotenv import load_dotenv

load_dotenv()

PORT = 8000
SCRAPE_INTERVAL = 30  # secondes

LANGFUSE_HOST = os.getenv("LANGFUSE_BASE_URL", "https://cloud.langfuse.com").rstrip("/")
LANGFUSE_AUTH = HTTPBasicAuth(
    os.getenv("LANGFUSE_PUBLIC_KEY"),
    os.getenv("LANGFUSE_SECRET_KEY"),
)

# ── Métriques Prometheus ─────────────────────────────────────────
LATENCY_P95     = Gauge("llm_latency_p95_ms",      "Latence P95 en millisecondes")
LATENCY_AVG     = Gauge("llm_latency_avg_ms",      "Latence moyenne en millisecondes")
TOKEN_INPUT_AVG = Gauge("llm_tokens_input_avg",    "Tokens input moyens par requete")
TOKEN_OUTPUT_AVG= Gauge("llm_tokens_output_avg",   "Tokens output moyens par requete")
TOKEN_TOTAL_AVG = Gauge("llm_tokens_total_avg",    "Tokens totaux moyens par requete")
ERROR_RATE      = Gauge("llm_error_rate_percent",  "Taux d erreurs en pourcentage")
THROUGHPUT      = Gauge("llm_throughput_rpm",      "Requetes par minute (derniere heure)")
HALLUC_RATE     = Gauge("llm_hallucination_rate",  "Taux de reponses hors contexte (proxy)")
TOTAL_TRACES    = Gauge("llm_total_traces",        "Nombre total de traces")


def fetch_metrics():
    try:
        resp = requests.get(
            f"{LANGFUSE_HOST}/api/public/traces",
            auth=LANGFUSE_AUTH,
            params={"limit": 100},
            timeout=10,
        )
        resp.raise_for_status()
        traces = resp.json().get("data", [])
    except Exception as e:
        print(f"  [ERREUR] LangFuse API traces : {e}")
        return

    if not traces:
        print("  [INFO] Aucune trace trouvee dans LangFuse.")
        return

    # Token data vit dans les observations (générations), pas dans les traces
    try:
        obs_resp = requests.get(
            f"{LANGFUSE_HOST}/api/public/observations",
            auth=LANGFUSE_AUTH,
            params={"limit": 100, "type": "GENERATION"},
            timeout=10,
        )
        obs_resp.raise_for_status()
        observations = obs_resp.json().get("data", [])
    except Exception as e:
        print(f"  [WARN] LangFuse API observations : {e}")
        observations = []

    latencies   = []
    input_tokens  = []
    output_tokens = []
    total_tokens  = []
    errors      = 0
    halluc      = 0

    for t in traces:
        # Latence (en secondes → ms)
        try:
            lat = t.get("latency")
            if lat is not None:
                latencies.append(float(lat) * 1000)
        except Exception:
            pass

        # Erreurs
        try:
            if t.get("level") in ("ERROR", "WARNING"):
                errors += 1
        except Exception:
            pass

        # Proxy hallucination
        try:
            output = str(t.get("output") or "").lower()
            if any(kw in output for kw in ["not found", "je ne sais pas", "information not found", "cannot answer"]):
                halluc += 1
        except Exception:
            pass

    # Tokens depuis les observations (générations) — c'est là que LangFuse 4.x les stocke
    for obs in observations:
        try:
            usage = obs.get("usage") or {}
            if usage.get("input"):
                input_tokens.append(usage["input"])
            if usage.get("output"):
                output_tokens.append(usage["output"])
            if usage.get("total"):
                total_tokens.append(usage["total"])
        except Exception:
            pass

    n = len(traces)
    TOTAL_TRACES.set(n)

    if latencies:
        LATENCY_P95.set(round(float(np.percentile(latencies, 95)), 1))
        LATENCY_AVG.set(round(float(np.mean(latencies)), 1))

    if input_tokens:
        TOKEN_INPUT_AVG.set(round(float(np.mean(input_tokens)), 1))
    if output_tokens:
        TOKEN_OUTPUT_AVG.set(round(float(np.mean(output_tokens)), 1))
    if total_tokens:
        TOKEN_TOTAL_AVG.set(round(float(np.mean(total_tokens)), 1))

    ERROR_RATE.set(round(errors / n * 100, 2) if n else 0)
    HALLUC_RATE.set(round(halluc / n * 100, 2) if n else 0)

    # Throughput : traces avec timestamp dans les 60 dernières minutes
    try:
        from datetime import datetime, timezone, timedelta
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=60)
        recent = 0
        for t in traces:
            ts = t.get("timestamp")
            if ts:
                try:
                    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    if dt >= cutoff:
                        recent += 1
                except Exception:
                    pass
        THROUGHPUT.set(round(recent / 60, 3))
    except Exception:
        THROUGHPUT.set(0)

    print(f"  Metriques mises a jour — {n} traces")
    print(f"    Latence P95     : {LATENCY_P95._value.get():.0f} ms")
    print(f"    Latence moy.    : {LATENCY_AVG._value.get():.0f} ms")
    print(f"    Tokens input    : {TOKEN_INPUT_AVG._value.get():.0f}")
    print(f"    Tokens output   : {TOKEN_OUTPUT_AVG._value.get():.0f}")
    print(f"    Error rate      : {ERROR_RATE._value.get():.1f}%")
    print(f"    Hallucination   : {HALLUC_RATE._value.get():.1f}%")
    print(f"    Throughput      : {THROUGHPUT._value.get():.3f} req/min")


def run():
    print("\n" + "=" * 65)
    print("  AngeVirusLab — LLM Monitoring Exporter")
    print("  Ngagne Demba Dia · Master SSE · UCAD · Dakar")
    print("=" * 65)
    print(f"\n  Exporter Prometheus sur http://localhost:{PORT}/metrics")
    print(f"  Scraping LangFuse toutes les {SCRAPE_INTERVAL}s\n")

    start_http_server(PORT)

    while True:
        print(f"\n  [{time.strftime('%H:%M:%S')}] Collecte des metriques...")
        fetch_metrics()
        time.sleep(SCRAPE_INTERVAL)


if __name__ == "__main__":
    run()
