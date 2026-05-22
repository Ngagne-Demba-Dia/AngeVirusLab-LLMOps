"""Module 4 — LLM-Assisted Exploit Explanation
Utilise un LLM local (LLaMA3.1 via Ollama) pour expliquer les vulnérabilités
en langage naturel, avec tracing LangFuse et guardrails de base.
Dégradation gracieuse si Ollama ou LangFuse non disponibles.
"""
import os
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

try:
    from langfuse import observe
    _LANGFUSE_OK = True
except ImportError:
    _LANGFUSE_OK = False
    def observe(*args, **kwargs):
        def decorator(func):
            return func
        return decorator

SYSTEM_PROMPT = (
    "Tu es un expert en sécurité des systèmes embarqués et IoT, spécialisé dans l'analyse de firmware. "
    "Tu analyses des rapports d'analyse statique et expliques les vulnérabilités de façon claire, "
    "structurée et actionnnable pour une équipe de sécurité. Réponds en français."
)

HUMAN_TEMPLATE = """\
=== RAPPORT D'ANALYSE FIRMWARE ===

Architecture détectée : {arch}
Taille du firmware    : {size} bytes
Binaires analysés     : {binaries_count}

--- Vulnérabilités identifiées ---
{vulnerabilities}

--- Credentials hardcodés ---
{credentials}

--- Fichiers cachés ---
{hidden_files}

--- Fonctions dangereuses (strcpy/gets/sprintf) ---
{dangerous_functions}

--- Backdoors détectés ---
{backdoors}

=== DEMANDE ===
Fournis une analyse structurée en 4 parties :
1. **Résumé exécutif** (2-3 phrases, sévérité globale)
2. **Vulnérabilités critiques** (classées Critical / High / Medium)
3. **Vecteurs d'exploitation** (comment un attaquant exploiterait ces failles)
4. **Recommandations** (actions concrètes pour l'équipe de remédiation)
"""


def _format_list(items: list, key: str | None = None, limit: int = 10) -> str:
    if not items:
        return "Aucun"
    if key:
        lines = [f"- {item[key]}" for item in items[:limit]]
    else:
        lines = [f"- {item}" for item in items[:limit]]
    if len(items) > limit:
        lines.append(f"  ... et {len(items) - limit} autres")
    return "\n".join(lines)


@observe(name="firmware-analysis")
def explain_with_llm(arch_result: dict, vuln_report: dict) -> str:
    creds_formatted = "\n".join(
        f"- {c['file']}: {c['match']}"
        for c in vuln_report.get("credentials", [])[:10]
    ) or "Aucun"

    funcs_formatted = "\n".join(
        f"- {d['binary']}: {', '.join(d['functions'])}"
        for d in vuln_report.get("dangerous_functions", [])[:10]
    ) or "Aucune"

    backdoors_formatted = "\n".join(
        f"- {b['binary']}: {', '.join(b['patterns'])}"
        for b in vuln_report.get("backdoors", [])[:10]
    ) or "Aucun"

    try:
        llm = ChatOllama(model="llama3.1:8b", temperature=0, timeout=120)
        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            ("human", HUMAN_TEMPLATE),
        ])
        chain = prompt | llm | StrOutputParser()

        return chain.invoke(
            {
                "arch": arch_result.get("dominant_arch", "Unknown"),
                "size": vuln_report.get("firmware_size", "N/A"),
                "binaries_count": arch_result.get("binaries_analyzed", "N/A"),
                "vulnerabilities": _format_list(vuln_report.get("vulnerabilities", [])),
                "credentials": creds_formatted,
                "hidden_files": _format_list(vuln_report.get("hidden_files", [])),
                "dangerous_functions": funcs_formatted,
                "backdoors": backdoors_formatted,
            }
        )

    except Exception as e:
        lines = [
            f"[Ollama non disponible : {e}]",
            "",
            "=== RAPPORT STATIQUE ===",
            f"Architecture : {arch_result.get('dominant_arch', 'Unknown')}",
            "",
            "Vulnérabilités détectées :",
        ]
        for v in vuln_report.get("vulnerabilities", []):
            lines.append(f"  • {v}")
        return "\n".join(lines)
