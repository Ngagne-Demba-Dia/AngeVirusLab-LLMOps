# AngeVirusLab — LLMSecOps & Sécurité des Systèmes Embarqués

> **Ngagne Demba Dia · AngeVirus**
> Master Sécurité des Systèmes Embarqués · UCAD · Dakar · 2026

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![AWS](https://img.shields.io/badge/AWS-Cloud%20Offensif-orange.svg)
![ARM](https://img.shields.io/badge/Arch-ARM%2FMIPS%2Fx86-green.svg)
![Labs](https://img.shields.io/badge/Labs-23%20complétés-brightgreen.svg)

---

## Présentation

Programme de spécialisation **LLMSecOps** de 31 semaines couvrant l'ensemble du spectre de la sécurité des systèmes IA et embarqués : fondations LLMOps, attaque offensive des LLMs, exploitation Cloud AWS, et sécurité des systèmes embarqués (x86 / ARM / MIPS / Firmware IoT).

> Paper technique global : [paper.md](paper.md)

---

## Statut global

| Pilier | Thème | Semaines | Statut |
|---|---|---|---|
| **Pilier 0** | LLMOps Foundations | 1–8 | ✅ Terminé |
| **Pilier 1** | LLM Security Offensive | 9–14 | ✅ Terminé |
| **Pilier 2** | Cloud Offensif AWS + ARM | 15–22 | ✅ Terminé |
| **Pilier 3** | Embarqué MIPS + Firmware IoT | 23–31 | ✅ Terminé |
| **Projet final** | AI-Assisted Embedded Attack Framework | — | 🔜 En cours |

---

## Pilier 0 — LLMOps Foundations (Semaines 1–8)

Déploiement et sécurisation d'un LLM en production — 100% open source, 0$ tooling.

**Stack :** Ollama · LLaMA3.1:8b · LangChain · LangFuse · ChromaDB · RAGAS · Prometheus · Grafana

| Lab | Description | Statut |
|---|---|---|
| [local-llm-agent](pilier-0-llmops/local-llm-agent/) | Agent LLM 3 outils + tracing LangFuse complet | ✅ |
| [prompt-tracker](pilier-0-llmops/prompt-tracker/) | Versioning prompts + A/B testing + détection hallucination | ✅ |
| [llm-guardrails](pilier-0-llmops/llm-guardrails/) | InputRail + OutputRail — anti-injection (OWASP LLM01/02) | ✅ |
| [rag-pipeline](pilier-0-llmops/rag-pipeline/) | RAG complet : ChromaDB · 3387 chunks · RAGAS eval | ✅ |
| [monitoring](pilier-0-llmops/monitoring/) | Prometheus + Grafana + LangFuse — 5 métriques clés | ✅ |
| [final-project](pilier-0-llmops/final-project/) | Secure RAG Pipeline : Guardrails + RAG + LangFuse 8/8 | ✅ |

**Architecture finale :**
```
User Input → INPUT RAIL → RAG → LLM → OUTPUT RAIL → LangFuse → Grafana
```
5 menaces bloquées · Latence P95 : 43 030 ms · Error Rate : 0%

---

## Pilier 1 — LLM Security Offensive (Semaines 9–14)

Labs PortSwigger Web Security Academy — OWASP LLM Top 10.

| Lab | Vulnérabilité | Statut |
|---|---|---|
| Excessive Agency | OWASP LLM08 — actions autonomes non contrôlées | ✅ |
| OS Command Injection via LLM | Injection commandes système via API LLM | ✅ |
| Indirect Prompt Injection | Manipulation via documents externes | ✅ |
| AI Agent Exploitation | Actions destructives sur agent IA | ✅ |

---

## Pilier 2 — Cloud Offensif AWS + ARM (Semaines 15–22)

### Cloud AWS

| Lab | Technique | Statut |
|---|---|---|
| [flaws.cloud niveaux 1–6](pilier-2-cloud-aws/flaws-cloud/) | S3 public · ACL · git leak · snapshot · SSRF IMDS · Lambda | ✅ |
| [CloudGoat IAM privesc](pilier-2-cloud-aws/cloudgoat-iam-privesc/) | PassRole + RunInstances → IMDS → credentials admin | ✅ |
| [CloudGoat cloud_breach_s3](pilier-2-cloud-aws/cloudgoat-cloud-breach-s3/) | SSRF Host header → IMDS → S3FullAccess → exfiltration | ✅ |

### C/ASM — ARM32

| Lab | Technique | OFFSET | Statut |
|---|---|---|---|
| [Lab18](pilier-3-casm-embedded/lab18-arm-intro-qemu/) | ARM ret2win — QEMU + GDB-multiarch | 76 | ✅ |
| [Lab19](pilier-3-casm-embedded/lab19-arm-rop/) | ARM ROP — pop_r0_pc + system@plt | 76 | ✅ |
| [Lab20](pilier-3-casm-embedded/lab20-arm-ret2libc/) | ARM ret2syscall SVC#0 — chain R7/R0/R1/R2 | 68 | ✅ |

---

## Pilier 3 — Embarqué MIPS + Firmware IoT (Semaines 23–31)

### C/ASM — x86 (Labs 01–13)

| Lab | Technique | Statut |
|---|---|---|
| Lab01 | x86 mémoire + GDB — pointeurs, segfault, stack frame | ✅ |
| Lab02 | Buffer overflow basique — EIP dans GDB | ✅ |
| Lab03 | ret2win — padding + EIP override | ✅ |
| Lab04 | Format string — %x leak, %n write | ✅ |
| Lab05 | ROP ret2libc | ✅ |
| Lab06 | ASLR bypass | ✅ |
| Lab07 | PIE bypass | ✅ |
| Lab08 | Stack canary bypass via format string leak | ✅ |
| Lab09 | Full combo NX + Canary + PIE + ASLR | ✅ |
| Lab10 | ret2syscall execve direct | ✅ |
| Lab11 | mprotect ROP + shellcode injection | ✅ |
| Lab12 | Privilege escalation syscall chaining (setregid) | ✅ |
| Lab13 | Ghidra RE — XOR crackme, password recovery | ✅ |

### Rust Red Team (Labs 14–17)

| Lab | Technique | Statut |
|---|---|---|
| [Lab14](pilier-3-casm-embedded/lab14-rust-revshell/) | Reverse shell Rust — TcpStream + fd redirect | ✅ |
| [Lab15](pilier-3-casm-embedded/lab15-rust-process-injection/) | Process injection via ptrace (Rust) | ✅ |
| [Lab16](pilier-3-casm-embedded/lab16-rust-amsi-bypass/) | AMSI bypass — patch AmsiScanBuffer (Windows) | ✅ |
| [Lab17](pilier-3-casm-embedded/lab17-rust-shellcode-loader/) | Shellcode loader — mmap RWX + transmute | ✅ |

### MIPS + Firmware IoT (Labs 21–23)

| Lab | Technique | OFFSET | Statut |
|---|---|---|---|
| [Lab21](pilier-3-casm-embedded/lab21-mips-rop/) | MIPS ret2win — $ra overflow, O32 ABI quirks | 68 | ✅ |
| [Lab22](pilier-3-casm-embedded/lab22-firmware-iot/) | Firmware IoT — binwalk, SquashFS, 3 flags, backdoor | — | ✅ |
| [Lab23](pilier-3-casm-embedded/lab23-mips-httpd-bof/) | httpd parse_auth() strcpy overflow — firmware → exploit | 68 | ✅ |

### Consolidation

| Document | Contenu | Statut |
|---|---|---|
| [Comparatif x86/ARM/MIPS](pilier-3-casm-embedded/sem30-comparatif-architectures/) | Registres · ABI · OFFSET · quirks · 23 labs synthétisés | ✅ |

---

## Projet final — AI-Assisted Embedded Attack Framework

Projet signature qui ferme la boucle sur les 4 piliers :

| Module | Description | Source |
|---|---|---|
| Module 1 — Firmware extraction | binwalk · Ghidra · angr | Lab22 |
| Module 2 — Architecture detection | ARM / MIPS / x86 auto-detect | Labs 18–23 |
| Module 3 — Exploit analysis | BoF · ROP · syscall chain | Labs 01–23 |
| Module 4 — LLM-assisted explanation | RAG local + LangFuse + guardrails | Pilier 0 |

---

## Hardware

```
CPU : AMD Ryzen 7 5800H @ 3.2 GHz
RAM : 40 GB DDR4
GPU : NVIDIA GeForce RTX 3060 Laptop (6 GB VRAM) — CUDA 12.4
OS  : WSL2 Ubuntu sur Windows 11 Pro
```

---

**Ngagne Demba Dia** — AngeVirus
Master Sécurité des Systèmes Embarqués · UCAD · CCDOC · Dakar, Sénégal

[![GitHub](https://img.shields.io/badge/GitHub-Ngagne--Demba--Dia-black?logo=github)](https://github.com/Ngagne-Demba-Dia)
