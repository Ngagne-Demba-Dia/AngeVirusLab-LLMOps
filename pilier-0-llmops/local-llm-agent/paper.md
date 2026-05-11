# Déploiement d'un Agent LLM Local Observable avec LangFuse
## Mini-Papier Technique

**Auteur :** AngeVirus — Ngagne Demba Dia
**Organisation :** Shadow Bytes Red Team · UCAD · CCDOC · Dakar, Sénégal
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

Ce travail s'inscrit dans le cadre du programme de spécialisation LLMSecOps de
Shadow Bytes Red Team (UCAD, Dakar). Le Pilier 0 pose les fondations opérationnelles
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
from langfuse.callback import CallbackHandler

handler = CallbackHandler(
    public_key=LANGFUSE_PUBLIC_KEY,
    secret_key=LANGFUSE_SECRET_KEY,
    host=LANGFUSE_HOST
)

response = chain.invoke(query, config={"callbacks": [handler]})
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

### 3.1 Métriques collectées

*[À remplir après le lab — copier depuis le dashboard LangFuse]*

| Métrique | Valeur observée |
|---|---|
| Latence moyenne | — ms |
| Latence P95 | — ms |
| Tokens input (moyenne) | — |
| Tokens output (moyenne) | — |
| Coût estimé / requête | — $ |
| Nombre de traces totales | — |

### 3.2 Utilisation GPU

```
NVIDIA GeForce (6 GB VRAM)
LLaMA3:8b (Q4_K_M) : ~5.8 GB occupés
GPU Util pendant inférence : ~XX% (à mesurer)
```

### 3.3 Observations qualitatives

*[À remplir après le lab]*

- Qualité des réponses :
- Comportement lors de questions hors domaine :
- Comportement lors de tentatives d'injection :

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

*Shadow Bytes Red Team · UCAD · Dakar — AngeVirus 2026*
*Activités réalisées sur environnements de lab autorisés.*
