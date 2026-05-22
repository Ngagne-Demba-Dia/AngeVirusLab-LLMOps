# J'ai fait tourner un LLM local sur mon GPU en 30 minutes — et je vois tout ce qu'il fait

> *Ngagne Demba Dia · AngeVirus · Master Sécurité des Systèmes Embarqués · UCAD · Dakar, Mai 2026*

---

J'ai voulu répondre à une question simple :

**Est-ce qu'on peut déployer un LLM local, gratuit, observable, sans envoyer une seule donnée à OpenAI ?**

Réponse courte : **oui**. Et ça tourne sur un GPU de laptop.

---

## Le problème avec les LLMs en production

La plupart des équipes qui déploient des LLMs font la même erreur :
elles branchent l'API, ça répond, elles passent à la suite.

Mais après un moment :
- Les réponses se dégradent — personne ne sait pourquoi
- Un utilisateur obtient une réponse bizarre — impossible de reproduire
- Le coût API explose — impossible de savoir quelle requête est responsable

Sans observabilité, un LLM en production est une boîte noire.

---

## Ce que j'ai construit

**Stack complet, 100% open source, 0$ :**

```
LLaMA3:8b (Meta AI)         ← le cerveau
     via Ollama              ← tourne localement sur mon GPU
     via LangChain           ← orchestre les appels
     via LangFuse            ← trace TOUT : tokens, latence, tool calls
```

Mon GPU : NVIDIA 6 Go VRAM. LLaMA3:8b en quantization Q4 = ~4.7 Go.
Il rentre. Et il va vite.

---

## L'installation en 5 minutes

```bash
# 1. Ollama
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3:8b

# 2. Python
pip install langchain langchain-community langfuse

# 3. LangFuse
# Créer un compte sur cloud.langfuse.com → récupérer les clés API
```

---

## Le code — 20 lignes pour un agent observable

```python
from langchain_community.llms import Ollama
from langfuse.callback import CallbackHandler

# Connecter LangFuse
langfuse_handler = CallbackHandler(
    public_key="pk-lf-...",
    secret_key="sk-lf-...",
    host="https://cloud.langfuse.com"
)

# Instancier le LLM local
llm = Ollama(model="llama3:8b")

# Chaque appel est maintenant tracé automatiquement
response = llm.invoke(
    "Explique LLMOps en 3 lignes.",
    config={"callbacks": [langfuse_handler]}
)

print(response)
```

---

## Ce que LangFuse capture — en temps réel

Après ce seul appel, mon dashboard LangFuse montre :

- **La trace complète** : input exact → output exact
- **La latence** : combien de ms le modèle a mis pour répondre
- **Les tokens** : combien de tokens en input, combien en output
- **Le coût estimé** : même en local, on peut estimer ce que ça coûterait en API

*[screenshot dashboard LangFuse ici]*

---

## Pourquoi c'est important pour la sécurité

Dans mon programme de Master Sécurité des Systèmes Embarqués (UCAD), le LLM Security
consiste à *attaquer* des LLMs après avoir appris à les *construire*.

Dans le Lab 1 PortSwigger que j'ai résolu (Excessive Agency — OWASP LLM08),
j'ai exploité un LLM qui exécutait des commandes SQL sans contrôle.

LangFuse aurait détecté ça instantanément :
```
Trace anormale détectée :
  tool_call: "execute_sql"
  query: "DELETE FROM users WHERE username='carlos'"
  → ALERTE : opération destructrice non autorisée
```

**Construire le pipeline avant de l'attaquer, c'est l'avantage compétitif.**

---

## Ce que j'ai appris

**1.** LLMOps ≠ MLOps. Ce sont deux disciplines différentes avec des problèmes différents.

**2.** L'observabilité n'est pas optionnelle. C'est la fondation de tout le reste.

**3.** Un GPU de laptop suffit. LLaMA3:8b en Q4 sur 6 Go VRAM, c'est utilisable.

**4.** LangFuse est la meilleure option open source. Self-hostable, gratuit, framework-agnostic.

---

## Prochaine étape

**Prompt versioning** — comment versionner ses prompts comme du code,
faire des A/B tests, et détecter le drift de réponse.

---

*Code disponible sur [GitHub](https://github.com/Ngagne-Demba-Dia/AngeVirusLab-LLMOps)*
*Ngagne Demba Dia · Master Sécurité des Systèmes Embarqués · UCAD · Dakar, Sénégal*

---
*#LLMOps #LLaMA3 #Ollama #LangFuse #LangChain #OpenSource #ShadowBytes #UCAD #Dakar #Sénégal*
