# Pilier 1 — LLM Security Offensive

> **PortSwigger Web Security Academy · LLM Attacks**
> Ngagne Demba Dia · AngeVirusLab · Shadow Bytes Red Team · UCAD · 2026

[![OWASP LLM Top 10](https://img.shields.io/badge/OWASP-LLM%20Top%2010-red.svg)](https://owasp.org/www-project-top-10-for-llm-applications/)

---

## Labs PortSwigger — LLM Attacks

| # | Lab | Niveau | Vulnérabilité | Status |
| --- | --- | --- | --- | --- |
| Lab 1 | [portswigger-lab1-excessive-agency](portswigger-lab1-excessive-agency/) | APPRENTI | OWASP LLM08 — Excessive Agency | ✅ Done |
| Lab 2 | [portswigger-lab2-api-vulnerabilities](portswigger-lab2-api-vulnerabilities/) | PRATICIEN | OS Command Injection via LLM API | ✅ Done |
| Lab 3 | portswigger-lab3-indirect-prompt-injection | PRATICIEN | Indirect Prompt Injection | ⏭ À reprendre |
| Lab 4 | — | APPRENTI | Exploiting AI agents — destructive actions | ✅ Done |

---

## Gandalf CTF

| # | Niveau | Status |
| --- | --- | --- |
| [gandalf-ctf](gandalf-ctf/) | Niveaux 1-7 | 🔜 En cours |

---

## Axes couverts

- **LLM08 — Excessive Agency** : outil `debug_sql` exposé → SQL injection via LLM proxy
- **CWE-78 — OS Command Injection** : paramètre email non sanitisé → injection shell
- **Indirect Prompt Injection** : injection de prompts via contenu tiers (blog posts, reviews)
- **AI Agent Exploitation** : manipulation d'un agent IA autonome pour effectuer des actions destructives

---

*Ngagne Demba Dia · AngeVirusLab · Shadow Bytes Red Team · UCAD · Dakar, 2026*
