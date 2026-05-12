import sys
import os
import time
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
from langchain_ollama import OllamaLLM
from langfuse import Langfuse
from langfuse.langchain import CallbackHandler

load_dotenv()

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

langfuse = Langfuse()
llm = OllamaLLM(model=os.getenv("OLLAMA_MODEL", "llama3.1:8b"), temperature=0)

PROMPT_NAME = "llmops-explainer"
VERSIONS = [1, 2, 3]

TOPIC_LABELS = {
    1: "LLMOps",
    2: "Sécurité Cloud",
    3: "Sécurité Embarquée",
}


# ---------------------------------------------------------------------------
# A/B test runner
# ---------------------------------------------------------------------------

def run_ab_test():
    print("\n" + "=" * 65)
    print("  AngeVirusLab — A/B Test Prompt Versioning")
    print("  Prompt : llmops-explainer  ·  Modèle : LLaMA3.1:8b")
    print("  Ngagne Demba Dia · Master SSE · UCAD · Dakar")
    print("=" * 65)

    results = []

    for version in VERSIONS:
        print(f"\n{'─' * 65}")
        print(f"  Version {version} — {TOPIC_LABELS[version]}")
        print(f"{'─' * 65}")

        # Pull prompt from LangFuse registry
        prompt_obj = langfuse.get_prompt(PROMPT_NAME, version=version)
        prompt_text = prompt_obj.prompt
        print(f"  Prompt : {prompt_text[:80]}{'...' if len(prompt_text) > 80 else ''}")
        print()

        handler = CallbackHandler()
        start = time.time()

        response = llm.invoke(
            prompt_text,
            config={
                "callbacks": [handler],
                "run_name": f"ab_test_{PROMPT_NAME}_v{version}",
                "metadata": {
                    "prompt_name": PROMPT_NAME,
                    "prompt_version": version,
                    "topic": TOPIC_LABELS[version],
                },
            },
        )

        latency = round(time.time() - start, 2)

        print(f"  Réponse :\n{response}")
        print(f"\n  Latence : {latency}s")

        results.append({
            "version": version,
            "topic": TOPIC_LABELS[version],
            "latency": latency,
            "chars": len(response),
        })

    # Summary table
    print("\n\n" + "=" * 65)
    print("  Résultats comparatifs")
    print("=" * 65)
    print(f"  {'Version':<10} {'Topic':<25} {'Latence':<12} {'Longueur'}")
    print(f"  {'─'*8:<10} {'─'*23:<25} {'─'*10:<12} {'─'*10}")
    for r in results:
        print(f"  v{r['version']:<9} {r['topic']:<25} {r['latency']:<12} {r['chars']} chars")

    best = min(results, key=lambda x: x["latency"])
    print(f"\n  Latence minimale : v{best['version']} ({best['topic']}) → {best['latency']}s")
    print(f"\n  → Traces disponibles sur cloud.langfuse.com")
    print(f"  → Filtrer par : run_name = 'ab_test_llmops-explainer_v*'")
    print("=" * 65 + "\n")

    langfuse.flush()


if __name__ == "__main__":
    run_ab_test()
