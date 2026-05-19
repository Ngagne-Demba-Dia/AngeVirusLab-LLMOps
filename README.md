# AngeVirusLab — LLMSecOps Programme

> **Ngagne Demba Dia · Master Sécurité des Systèmes Embarqués · UCAD · Dakar**
> AngeVirus · Shadow Bytes Red Team · CCDOC · 2026

[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![AWS](https://img.shields.io/badge/AWS-Cloud%20Offensif-orange.svg)](https://aws.amazon.com)
[![OWASP](https://img.shields.io/badge/OWASP-LLM%20Top%2010-red.svg)](https://owasp.org/www-project-top-10-for-llm-applications/)
[![PortSwigger](https://img.shields.io/badge/PortSwigger-LLM%20Attacks-blueviolet.svg)](https://portswigger.net)

---

## Présentation

Programme **LLMSecOps** de 31 semaines couvrant l'ensemble du spectre de la sécurité des systèmes IA :
des fondations LLMOps jusqu'à l'offensive Cloud AWS et la sécurité des systèmes embarqués NVIDIA.

> Paper global : [paper.md](paper.md)

---

## Vue d'ensemble du programme

| Pilier | Thème | Semaines | Statut |
| --- | --- | --- | --- |
| **Pilier 0** | LLMOps Foundations | 1–8 | ✅ Done |
| **Pilier 1** | LLM Security Offensive | 9–14 | ✅ Done |
| **Pilier 2** | Cloud Offensif AWS | 15–22 | ✅ Done |
| **Pilier 3** | Embarqué NVIDIA | 23–31 | 🔜 À venir |

---

## Pilier 0 — LLMOps Foundations (Semaines 1–8)

Déploiement et sécurisation d'un LLM en production — 100% open source, 0$ tooling, GPU local.

**Stack :** Ollama · LLaMA3.1:8b · LangChain · LangFuse 4.x · ChromaDB · RAGAS · Prometheus · Grafana

| # | Lab | Description | Score |
| --- | --- | --- | --- |
| Week 1-2 | [local-llm-agent](pilier-0-llmops/local-llm-agent/) | Agent LLM local (3 outils) + tracing LangFuse complet | ✅ Done |
| Week 3-4 | [prompt-tracker](pilier-0-llmops/prompt-tracker/) | Versioning prompts + A/B testing + détection hallucination | ✅ Done |
| Week 5 | [llm-guardrails](pilier-0-llmops/llm-guardrails/) | InputRail + OutputRail — anti-injection regex (OWASP LLM01/02) | ✅ Done |
| Week 6 | [rag-pipeline](pilier-0-llmops/rag-pipeline/) | RAG complet : ChromaDB · 3387 chunks · RAGAS eval | ✅ Done |
| Week 7 | [monitoring](pilier-0-llmops/monitoring/) | Prometheus + Grafana + LangFuse exporter — 5 métriques | ✅ Done |
| Week 8 | [final-project](pilier-0-llmops/final-project/) | Secure RAG Pipeline : Guardrails + RAG + LangFuse — **8/8** | ✅ Done |

**Résultat clé — Secure RAG Pipeline :**

```text
User Input → INPUT RAIL → RAG → LLM → OUTPUT RAIL → LangFuse → Grafana
```

- 5 menaces bloquées (injection, jailbreak, malware) — zéro token consommé
- Latence P95 : 43 030 ms · Tokens moy. : 729/req · Error Rate : 0%

---

## Pilier 1 — LLM Security Offensive (Semaines 9–14)

Labs PortSwigger Web Security Academy — LLM Attacks. Réalisés directement sur la plateforme.

| Lab | Niveau | Vulnérabilité | Statut |
| --- | --- | --- | --- |
| Exploitation des API LLM avec autonomie excessive | APPRENTI | OWASP LLM08 — Excessive Agency | ✅ Done |
| Exploitation des vulnérabilités dans les API LLM | PRATICIEN | OS Command Injection via LLM | ✅ Done |
| Injection indirecte de prompt | PRATICIEN | Indirect Prompt Injection | ✅ Done |
| Exploitation d'agents IA — actions destructives | APPRENTI | AI Agent Manipulation | ✅ Done |

**Axes couverts :** Excessive Agency · OS Command Injection · Indirect Prompt Injection · AI Agent Exploitation

---

## Pilier 2 — Cloud Offensif AWS (Semaines 15–22)

Labs offensifs AWS : mauvaises configurations S3, escalade de privilèges IAM, SSRF vers IMDS, exfiltration de données.

### flaws.cloud — Niveaux 1 à 6

> Write-up complet : [pilier-2-cloud-aws/flaws-cloud/](pilier-2-cloud-aws/flaws-cloud/)

| Level | Vulnérabilité | Impact |
| --- | --- | --- |
| 1 | Bucket S3 public — aucune auth | Lecture sans credentials |
| 2 | ACL "authenticated users" = tout compte AWS | Lecture avec credentials quelconques |
| 3 | `.git/` exposé → credentials dans l'historique | Accès complet au compte flaws.cloud |
| 4 | EC2 snapshot public → mot de passe en clair | Auth HTTP Basic sur site protégé |
| 5 | SSRF proxy nginx → IMDS 169.254.169.254 | Credentials IAM temporaires → listing bucket level6 |
| 6 | SecurityAudit + list_apigateways → Lambda | Invocation Lambda via API Gateway → URL finale |

### CloudGoat — IAM Privilege Escalation by Attachment

> Write-up complet : [pilier-2-cloud-aws/cloudgoat-iam-privesc/](pilier-2-cloud-aws/cloudgoat-iam-privesc/)

**Vecteur :** `iam:PassRole` + `ec2:RunInstances` → swap de rôle instance profile → IMDS → credentials admin temporaires

### CloudGoat — Cloud Breach S3

> Write-up complet : [pilier-2-cloud-aws/cloudgoat-cloud-breach-s3/](pilier-2-cloud-aws/cloudgoat-cloud-breach-s3/)

**Vecteur :** SSRF via Host header → IMDS → `S3FullAccess` → exfiltration données bancaires (SSN + passwords en clair)

---

## Pilier 3 — Embarqué NVIDIA (Semaines 23–31)

> 🔜 À venir — Sécurité des systèmes embarqués NVIDIA : firmware, side-channel, Jetson

---

## Hardware

```text
CPU : AMD Ryzen 7 5800H @ 3.2 GHz
RAM : 40 GB DDR4
GPU : NVIDIA GeForce RTX 3060 Laptop (6 GB VRAM) — CUDA 12.4
OS  : WSL2 Ubuntu sur Windows 11 Pro
```

---

**Ngagne Demba Dia** — AngeVirus
Master Sécurité des Systèmes Embarqués · UCAD · CCDOC · Dakar, Sénégal

[![GitHub](https://img.shields.io/badge/GitHub-Ngagne--Demba--Dia-black?logo=github)](https://github.com/Ngagne-Demba-Dia)
