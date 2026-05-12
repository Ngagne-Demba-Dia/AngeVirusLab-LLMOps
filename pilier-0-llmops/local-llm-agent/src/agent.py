import sys
import os
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.prebuilt import create_react_agent
from langfuse.langchain import CallbackHandler
from langfuse import Langfuse

from tools import calculator, web_search, execute_command
from config import OLLAMA_MODEL, OLLAMA_BASE_URL

load_dotenv()

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

langfuse_handler = CallbackHandler()

llm = ChatOllama(model=OLLAMA_MODEL, base_url=OLLAMA_BASE_URL, temperature=0)
tools = [calculator, web_search, execute_command]

SYSTEM = (
    "Tu es un assistant technique expert en LLMOps et sécurité des LLMs. "
    "Réponds toujours en français. "
    "Utilise les outils disponibles quand c'est pertinent et justifie ton choix."
)

agent = create_react_agent(llm, tools)

# ---------------------------------------------------------------------------
# Demo queries — une par outil
# ---------------------------------------------------------------------------

QUERIES = [
    {
        "id": "demo_calculator",
        "label": "Outil 1 — Calculatrice",
        "query": "Combien fait 1337 fois 42, plus 256 ? Donne le résultat exact.",
    },
    {
        "id": "demo_web_search",
        "label": "Outil 2 — Recherche web",
        "query": "Qu'est-ce que LLMOps et quels sont ses 3 défis principaux en production ?",
    },
    {
        "id": "demo_execute_command",
        "label": "Outil 3 — Commande système (Excessive Agency demo)",
        "query": "Quel est l'utilisateur courant du système et dans quel répertoire sommes-nous ?",
    },
]


def run_demo():
    print("\n" + "=" * 65)
    print("  AngeVirusLab — Agent LLM 3 outils + LangFuse tracing")
    print("  Shadow Bytes Red Team · UCAD · Dakar")
    print("=" * 65)

    for q in QUERIES:
        print(f"\n\n{'─' * 65}")
        print(f"  {q['label']}")
        print(f"{'─' * 65}")
        print(f"  Query : {q['query']}")
        print()

        messages = [
            SystemMessage(content=SYSTEM),
            HumanMessage(content=q["query"]),
        ]

        result = agent.invoke(
            {"messages": messages},
            config={
                "callbacks": [langfuse_handler],
                "run_name": q["id"],
            },
        )

        final = result["messages"][-1].content
        print(f"\n  Réponse finale : {final}")

    print("\n\n" + "=" * 65)
    print("  Traces disponibles sur : cloud.langfuse.com")
    print("  → Vérifier les spans 'tool' dans chaque trace")
    print("  → Observer : tool name, input, output, latence")
    print("=" * 65 + "\n")

    Langfuse().flush()


if __name__ == "__main__":
    run_demo()
