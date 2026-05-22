import subprocess
from langchain_core.tools import tool


@tool
def calculator(expression: str) -> str:
    """Évalue une expression mathématique Python. Exemples : '2 + 2', '15 * 7', '(100 / 4) + 8'."""
    allowed_chars = set("0123456789+-*/.() ")
    if not all(c in allowed_chars for c in expression):
        return "Erreur : seules les opérations mathématiques de base sont autorisées (+, -, *, /, parenthèses)."
    try:
        result = eval(expression)  # safe: all chars validated against whitelist
        return f"{expression} = {result}"
    except Exception as e:
        return f"Erreur de calcul : {e}"


@tool
def web_search(query: str) -> str:
    """Effectue une recherche web et retourne un résultat pertinent pour la requête."""
    mock_results = {
        "llmops": (
            "LLMOps est la discipline qui gère les LLMs en production. "
            "Ses 3 défis principaux : le prompt drift, les hallucinations, et le coût par token. "
            "Référence : Chip Huyen, 'Building LLM Applications for Production', 2023."
        ),
        "langfuse": (
            "LangFuse est une plateforme open source d'observabilité pour les LLMs. "
            "Elle capture les traces, la latence, les tokens et les tool calls en temps réel. "
            "Self-hostable, framework-agnostic. Source : langfuse.com"
        ),
        "ollama": (
            "Ollama permet d'exécuter des LLMs localement (LLaMA3, Mistral, Gemma, Phi3...). "
            "API REST compatible OpenAI. Supporte CUDA pour inférence GPU. Source : ollama.ai"
        ),
        "llama": (
            "LLaMA3:8b (Meta AI) est un modèle open source de 8 milliards de paramètres. "
            "En quantization Q4_K_M, il occupe ~4.7 GB de VRAM. "
            "Bon équilibre performance / ressources pour GPU laptops 6 GB."
        ),
        "excessive agency": (
            "OWASP LLM08 — Excessive Agency : vulnérabilité où un LLM dispose de permissions "
            "trop larges et peut exécuter des actions destructrices sans contrôle humain. "
            "Exemple réel : LLM qui exécute DELETE FROM users sans validation."
        ),
        "rag": (
            "RAG (Retrieval-Augmented Generation) augmente un LLM avec une base de connaissances externe. "
            "Pipeline : query → retriever (vectorstore) → context + query → LLM → réponse. "
            "Réduit les hallucinations sur des données spécifiques au domaine."
        ),
    }
    query_lower = query.lower()
    for key, result in mock_results.items():
        if key in query_lower:
            return result
    return (
        f"[Recherche simulée — requête : '{query}']\n"
        "Aucune entrée trouvée dans la base de démo. "
        "Dans un vrai agent, ceci appellerait DuckDuckGo, SerpAPI, ou un pipeline RAG."
    )


@tool
def execute_command(command: str) -> str:
    """Exécute une commande système et retourne la sortie.

    AVERTISSEMENT — OWASP LLM08 (Excessive Agency) :
    Un LLM avec accès non restreint à cet outil constitue une surface d'attaque critique.
    En démo, seules les commandes de lecture sont autorisées.
    """
    ALLOWED_PREFIXES = ("ls", "pwd", "whoami", "date", "uname", "echo", "cat")
    cmd_base = command.strip().split()[0] if command.strip() else ""

    if cmd_base not in ALLOWED_PREFIXES:
        return (
            f"[BLOCKED — DEMO SAFETY GUARD]\n"
            f"Commande refusée : '{command}'\n"
            f"Commandes autorisées en démo : {', '.join(ALLOWED_PREFIXES)}\n\n"
            "Dans un système non protégé (OWASP LLM08), cette commande aurait été exécutée. "
            "C'est exactement ce vecteur qu'on exploite en Pilier 1."
        )

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=10,
        )
        output = result.stdout or result.stderr or "(pas de sortie)"
        return f"$ {command}\n{output.strip()}"
    except subprocess.TimeoutExpired:
        return "Erreur : timeout dépassé (10s)"
    except Exception as e:
        return f"Erreur d'exécution : {e}"
