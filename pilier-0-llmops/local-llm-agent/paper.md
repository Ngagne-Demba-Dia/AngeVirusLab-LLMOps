# Déploiement d'un Agent LLM Local Observable avec LangFuse
## Mini-Papier Technique

**Auteur :** AngeVirus — Ngagne Demba Dia
**Organisation :** Master Sécurité des Systèmes Embarqués · UCAD · CCDOC · Dakar, Sénégal
**Date :** Mai 2026
**Catégorie :** LLMOps · Observabilité · Systèmes IA

---

## Abstract

Ce papier documente le déploiement d'un agent LLM local basé sur LLaMA3:8b (Meta AI)
via Ollama, orchestré par LangChain et entièrement instrumenté avec LangFuse pour
l'observabilité en production. Nous présentons l'architecture du système, les métriques
collectées (latence, consommation de tokens, coût estimé), et les leçons tirées
sur la nécessité de l'observabilité dans les systèmes LLM opérationnels.
L'ensemble du stack est open source et exécuté localement sur GPU NVIDIA via CUDA 12.0.

**Mots-clés :** LLMOps, LLaMA3, Ollama, LangChain, LangFuse, observabilité, agent LLM,
GPU local, CUDA, tracing.

---

## 1. Introduction

### 1.1 Motivation

Les Large Language Models (LLMs) déployés en production présentent des défis
opérationnels fondamentalement différents des modèles de machine learning classiques.
Là où MLOps gère le data drift et l'accuracy, LLMOps doit répondre à des problèmes
nouveaux : hallucinations, prompt drift, coût par token, et tentatives d'injection.

Sans observabilité, un LLM en production est une boîte noire. Il est impossible de
savoir pourquoi une réponse est incorrecte, quelle requête génère le plus de latence,
ou si un utilisateur tente une attaque par prompt injection.

### 1.2 Objectif

Ce projet répond à la question suivante : **comment déployer et instrumenter un agent
LLM local de manière à rendre son comportement en production entièrement observable ?**

### 1.3 Contexte

Ce travail s'inscrit dans le cadre d'une spécialisation LLMSecOps conduite à l'UCAD (Dakar)
dans le cadre du Master Sécurité des Systèmes Embarqués. Le Pilier 0 pose les fondations opérationnelles
qui seront attaquées en Pilier 1 (LLM Security offensive). Comprendre comment
construire un pipeline LLM observable est un prérequis pour comprendre où il est vulnérable.

---

## 2. Architecture et Méthodologie

### 2.1 Stack technique

| Composant | Outil | Version | Rôle |
|---|---|---|---|
| Modèle LLM | LLaMA3:8b (Meta AI) | Q4_K_M | Génération de texte |
| Runtime local | Ollama | 0.5.x | Servir le modèle via API REST |
| Orchestration | LangChain | 0.2.x | Chaînes, agents, outils |
| Observabilité | LangFuse | 2.x | Tracing, métriques, évaluations |
| Accélération | NVIDIA CUDA | 12.0 | Inférence GPU |
| Environnement | WSL2 Ubuntu | 22.04 | Linux sur Windows 11 |

### 2.2 Architecture du système

```
Requête utilisateur
        ↓
LangChain Agent
  ├── LLM Chain (Ollama → LLaMA3:8b)
  └── Tools (fonctions Python appelables par le LLM)
        ↓ (via CallbackHandler)
LangFuse Collector
  ├── Traces (chaque appel complet)
  ├── Spans (étapes : tool call, génération, etc.)
  └── Métriques (tokens, latence, coût)
        ↓
LangFuse Dashboard
  └── Visualisation temps réel
```

### 2.3 Instrumentation LangFuse

L'instrumentation est réalisée via le `CallbackHandler` de LangFuse, qui s'intègre
nativement dans LangChain. Une seule ligne de configuration instrumente l'ensemble
du pipeline, y compris les appels d'outils (tool calls).

```python
from dotenv import load_dotenv
from langchain_ollama import OllamaLLM
from langfuse.langchain import CallbackHandler
from langfuse import Langfuse

load_dotenv()  # lit LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_HOST depuis .env

handler = CallbackHandler()  # pas de clés en dur — tout vient des variables d'environnement
llm = OllamaLLM(model="llama3:8b")

response = llm.invoke(query, config={"callbacks": [handler]})
Langfuse().flush()  # s'assure que la trace est envoyée avant la fin du process
```

Chaque exécution génère une **trace** structurée contenant :
- L'input exact envoyé au modèle
- L'output généré
- Le modèle utilisé et ses paramètres
- Le nombre de tokens (input + output)
- La latence de chaque span
- Le coût estimé

---

## 3. Résultats

### 3.1 Phase 1 — LLM simple (LLaMA3:8b)

Métriques issues du dashboard LangFuse (2026-05-11).

| Métrique | Valeur observée |
|---|---|
| Latence (warm, GPU) | 7.92 s |
| Latence (cold start) | 22.68 s |
| TTFT (Time To First Token) | 0.61 s |
| Coût estimé / requête | $0.00 (inférence locale) |
| Modèle tracé | llama3:8b · provider: ollama |

> Screenshots : `docs/dashboard_traces.png` (vue liste) · `docs/trace_details.png` (trace détaillée)

**Analyse :** Le cold start (22.68s) correspond au chargement des poids en VRAM.
Une fois chargé, la latence warm tombe à 7.92s avec un TTFT de 0.61s — la génération
démarre rapidement même si la réponse complète prend plusieurs secondes.

### 3.2 Phase 2 — Agent avec 3 outils (LLaMA3.1:8b)

L'agent est instrumenté via LangFuse `CallbackHandler`. Chaque trace contient
des **spans imbriqués** : `AgentExecutor → ChatOllama → tool:<name>`.

| Outil | Requête de test | Résultat | Tool call tracé |
| --- | --- | --- | --- |
| `calculator` | "1337 × 42 + 256 ?" | 56 410 ✅ | `calculator("1337 * 42 + 256")` |
| `web_search` | "Qu'est-ce que LLMOps ?" | Contenu + synthèse ✅ | `web_search("LLMOps")` |
| `execute_command` | "Utilisateur et répertoire courant ?" | `angevirus` · chemin complet ✅ | `execute_command("whoami && pwd")` |

> Screenshots LangFuse :
> `docs/agent_traces_list.png` — vue liste des 3 traces
> `docs/agent_calculator_spans.png` — arbre de spans (tool: calculator)
> `docs/agent_execute_command_spans.png` — arbre de spans (tool: execute_command) · illustration OWASP LLM08
> `docs/agent_web_search_spans.png` — arbre de spans (tool: web_search)

**Observation critique :** À `temperature=0.7` (défaut), LLaMA 3.1 produisait le JSON
de l'appel outil en texte brut plutôt que de l'exécuter via le protocole function calling.
À `temperature=0`, le comportement devient déterministe et les 3 outils s'exécutent
correctement. Ce phénomène illustre un défi LLMOps réel : **la fiabilité du tool calling
dépend des hyperparamètres du modèle**, pas seulement de l'architecture agent.

> Note : `llama3:8b` (v3.0) ne supporte pas l'API tool calling d'Ollama — migration
> vers `llama3.1:8b` requise pour les agents. Différence invisible dans le code, critique
> en production.

### 3.3 Utilisation GPU

```text
Matériel   : NVIDIA GeForce RTX (6 GB VRAM)
Modèle     : LLaMA3.1:8b — quantization Q4_K_M
VRAM       : ~5.8 GB occupés / 6.0 GB disponibles (97%)
Runtime    : Ollama via CUDA 12.0 · WSL2 Ubuntu 22.04
```

### 3.4 Observations qualitatives

- **Multilingue** : sans instruction explicite de langue, LLaMA3 répond en espagnol
  sur des requêtes courtes — la spécification de langue dans le system prompt est obligatoire.
- **Visibilité complète** : LangFuse capture input/output exact, provider (`ollama`),
  modèle (`llama3.1:8b`), métadonnées LangChain — zero overhead côté code métier.
- **Excessive Agency détectée** : le tool `execute_command` avec guard whitelist montre
  comment LangFuse rend visible chaque commande système soumise par le LLM —
  connexion directe avec OWASP LLM08 (Pilier 1).

---

## 4. Discussion

### 4.1 Apport de l'observabilité

Sans LangFuse, les problèmes suivants seraient invisibles en production :
- **Latence anormale** sur certains types de requêtes
- **Consommation de tokens** excessive sur certains prompts
- **Tool calls inattendus** (connexion directe avec LLM08 Excessive Agency)
- **Drift de réponse** entre deux versions du même prompt

### 4.2 Connexion avec la sécurité LLM

L'observabilité est la première ligne de détection des attaques LLM.
Dans le Lab 1 PortSwigger (Pilier 1), l'Excessive Agency a permis l'exécution
d'une commande SQL destructrice. LangFuse, instrumenté correctement, aurait tracé
ce tool call anormal et permis une alerte immédiate.

### 4.3 Limites

- LLaMA3:8b reste limité en capacité de raisonnement complexe vs GPT-4
- 6 GB VRAM contraignent la taille du modèle utilisable localement
- LangFuse cloud envoie les traces vers des serveurs externes — données sensibles CCDOC nécessitent le self-hosting

---

## 5. Conclusion

Ce projet démontre qu'il est possible de déployer un agent LLM **entièrement local**,
**sans coût API**, et **avec observabilité complète** grâce à des outils open source.

Les métriques collectées (latence, tokens, tool calls) constituent la base de la
détection d'anomalies et d'attaques LLM en production.

**Leçon principale :** Un LLM sans observabilité est une boîte noire.
LLMOps n'est pas optionnel en production — c'est la fondation de toute sécurité LLM.

---

## Références

[1] Touvron, H. et al. (2023). *Llama 2: Open Foundation and Fine-Tuned Chat Models*. arXiv:2307.09288

[2] Huyen, C. (2023). *Building LLM Applications for Production*. https://huyenchip.com/2023/04/11/llm-engineering.html

[3] Huyen, C. (2024). *Building A Generative AI Platform*. https://huyenchip.com/2024/07/25/genai-platform.html

[4] LangFuse. (2024). *Open Source LLM Observability*. https://langfuse.com/docs

[5] OWASP. (2023). *OWASP Top 10 for Large Language Model Applications*. https://owasp.org/www-project-top-10-for-llm-applications/

[6] Chase, H. (2022). *LangChain: Building applications with LLMs through composability*. https://python.langchain.com

[7] Ollama. (2023). *Run Large Language Models Locally*. https://ollama.ai

---

*Ngagne Demba Dia · Master Sécurité des Systèmes Embarqués · UCAD · Dakar, 2026*
*Activités réalisées sur environnements de lab autorisés.*
