# LLMSecOps — Sécurité offensive des systèmes IA et embarqués

**Ngagne Demba Dia**
Master Sécurité des Systèmes Embarqués · UCAD · Dakar · 2026
AngeVirusLab · CCDOC

---

## Résumé

Ce document présente un programme de spécialisation de 31 semaines couvrant quatre domaines de la sécurité offensive : les pipelines LLMOps et leur instrumentation, l'exploitation offensive des LLMs (OWASP Top 10), l'attaque des infrastructures Cloud AWS, et l'exploitation des systèmes embarqués sur architectures x86, ARM32 et MIPSEL. L'ensemble des 23 labs pratiques réalisés est documenté avec les techniques, les erreurs rencontrées et les leçons retenues.

---

## 1. Introduction

La convergence entre les Large Language Models (LLMs) et les systèmes embarqués crée une nouvelle surface d'attaque : des modèles d'IA déployés en périphérie du réseau (edge AI), dans des firmwares IoT, sur des microcontrôleurs ARM, pilotent des infrastructures critiques avec des garanties de sécurité insuffisantes.

Ce programme adopte une approche offensive en quatre piliers :

```text
Pilier 0 : Construire un pipeline LLMOps sécurisé
Pilier 1 : Attaquer les LLMs (prompt injection, excessive agency)
Pilier 2 : Exploiter les mauvaises configurations Cloud AWS
Pilier 3 : Analyser et exploiter les systèmes embarqués (x86 → ARM → MIPS → Firmware)
```

Chaque pilier alimente le suivant : comprendre comment construire un LLM en production (Pilier 0) permet de mieux l'attaquer (Pilier 1). Comprendre les surfaces IAM cloud (Pilier 2) permet de voir comment un modèle Bedrock hérite de ces mauvaises configurations. Maîtriser l'exploitation embarquée (Pilier 3) permet de concevoir un framework d'analyse assisté par LLM (projet final).

---

## 2. Pilier 0 — LLMOps Foundations

### 2.1 Objectif

Déployer un pipeline LLM en production avec observabilité complète, versioning de prompts, guardrails anti-injection, et évaluation RAG. Stack 100% open source.

### 2.2 Architecture finale

```text
User Input
    │
    ▼ InputRail (regex + NeMo)
    │
    ▼ RAG Retriever (ChromaDB k=4, MiniLM-L12-v2)
    │
    ▼ LLaMA3.1:8b via Ollama
    │
    ▼ OutputRail (hallucination filter)
    │
    ▼ LangFuse (traces, métriques, coût token)
    │
    ▼ Prometheus + Grafana (5 métriques : latence P95, token cost, error rate, throughput, cache hit)
```

### 2.3 Résultats mesurés

| Métrique | Valeur |
| --- | --- |
| Menaces bloquées par les rails | 5 / 5 |
| Tokens consommés sur attaques bloquées | 0 |
| Latence P95 | 43 030 ms |
| Tokens moyens par requête | 729 |
| Error rate | 0 % |
| Faithfulness RAGAS (CAN Bus) | 1.00 |

### 2.4 Vulnérabilités identifiées sur le pipeline RAG

- **LLM02** : le RAG peut propager des contenus dangereux si le corpus n'est pas filtré à l'ingestion
- **LLM06** : des données sensibles ingérées dans ChromaDB sont récupérables via des questions ciblées
- **LLM10** : RAG Poisoning — injection d'un document malveillant dans le vectorstore pour manipuler les réponses du LLM

---

## 3. Pilier 1 — LLM Security Offensive

### 3.1 OWASP LLM Top 10 — Labs PortSwigger

| Lab | Vulnérabilité | Technique |
| --- | --- | --- |
| Excessive Agency | LLM08 | Le LLM exécute des actions autonomes non autorisées (suppression compte Carlos) |
| OS Command Injection | LLM01 | Injection via l'API newsletter → exécution commandes système |
| Indirect Prompt Injection | LLM01 | Manipulation du LLM via des documents tiers injectés dans le contexte |
| AI Agent Exploitation | LLM08 | Actions destructives déclenchées par manipulation de l'agent |

### 3.2 Leçon principale

Un LLM avec des outils (function calling) hérite de tous les privilèges de ces outils. Sans guardrails ni validation des actions, l'Excessive Agency (LLM08) est la vulnérabilité la plus critique des agents IA en production.

---

## 4. Pilier 2 — Cloud Offensif AWS

### 4.1 Surface d'attaque AWS

```text
S3 mal configuré → lecture sans auth
IAM PassRole + RunInstances → escalade admin via instance profile
SSRF vers 169.254.169.254 → credentials IAM temporaires
Lambda via API Gateway → exécution de code sans auth directe
```

### 4.2 Vecteurs exploités

**flaws.cloud (6 niveaux) :**

| Niveau | Vecteur | Impact |
| --- | --- | --- |
| 1 | Bucket S3 public | Lecture anonyme |
| 2 | ACL "authenticated users" | Lecture avec n'importe quel compte AWS |
| 3 | `.git/` exposé → credentials dans historique | Accès complet au compte |
| 4 | EC2 snapshot public → mot de passe en clair | Authentification HTTP |
| 5 | SSRF nginx → IMDS `169.254.169.254` | Credentials IAM → accès bucket level 6 |
| 6 | `SecurityAudit` + `list_apigateways` → Lambda | Invocation sans auth directe |

**CloudGoat IAM privesc :**
Vecteur : `iam:PassRole` + `ec2:RunInstances` → swap instance profile → IMDS → credentials admin temporaires

**CloudGoat cloud_breach_s3 :**
Vecteur : SSRF via Host header → IMDS → `S3:FullAccess` → exfiltration de données bancaires (SSN + passwords en clair)

### 4.3 Connexion LLM ↔ Cloud

Les modèles Bedrock et SageMaker héritent directement des mauvaises configurations IAM. Un rôle SageMaker avec `S3:*` non restreint expose tous les buckets du compte à quiconque peut déclencher une inférence.

---

## 5. Pilier 3 — Sécurité des Systèmes Embarqués

### 5.1 Progression architecturale

```text
x86-32 (Labs 01–13) → ARM32 (Labs 18–20) → MIPSEL (Labs 21–23)
```

La même technique fondamentale (stack overflow → contrôle du registre de retour) s'applique dans les trois architectures. Les différences sont dans l'ABI, les instructions spécifiques et les outils.

### 5.2 x86-32 — Labs 01 à 13

**Techniques maîtrisées :**

| Technique | Lab | Description |
| --- | --- | --- |
| ret2win | Lab03 | Écraser EIP avec adresse de win() |
| Format string | Lab04 | `%x` leak stack, `%n` write en mémoire |
| ROP ret2libc | Lab05 | Gadgets `pop ret` + `system("/bin/sh")` |
| ASLR bypass | Lab06 | Leak adresse → calcul offset libc |
| PIE bypass | Lab07 | Leak adresse base → positions relatives |
| Canary bypass | Lab08 | Format string leak du canary → overflow |
| Full combo | Lab09 | NX + Canary + PIE + ASLR simultanément |
| ret2syscall | Lab10 | `int 0x80` : EAX=11, EBX=&binsh, ECX=EDX=0 |
| mprotect ROP | Lab11 | Rendre stack exécutable → shellcode direct |
| Privilege escalation | Lab12 | `setregid` via ROP chain → shell SUID |
| Ghidra RE | Lab13 | Décompilation, XOR 0x13, recovery password |

### 5.3 Rust Red Team — Labs 14 à 17

Développement d'outils offensifs en Rust : reverse shell TCP, process injection via ptrace, AMSI bypass (Windows), shellcode loader avec mmap RWX. Rust élimine les erreurs mémoire à la compilation tout en permettant un contrôle bas niveau équivalent au C.

### 5.4 ARM32 — Labs 18 à 20

**Différences clés vs x86 :**

- Le registre de retour est `LR` (R14), sauvegardé par `push {r4, r7, lr}` et restauré par `pop {r4, r7, pc}`
- Le mode Thumb (instructions 16-bit) exige LSB=1 dans les adresses des gadgets
- Le syscall utilise `SVC #0` avec le numéro dans `R7` (pas dans l'instruction)
- `gdb-multiarch` + `qemu-arm -L /usr/arm-linux-gnueabihf` pour l'émulation

**Lab20 — ret2syscall SVC#0 (OFFSET=68) :**

```python
chain = p32(pop_r7_pc)    + p32(11)         +   # R7 = execve
        p32(pop_r0_pc)    + p32(binsh_addr) +   # R0 = &"/bin/sh"
        p32(pop_r1_r2_pc) + p32(0) + p32(0) +   # R1=R2=NULL
        p32(do_svc)                               # SVC #0
```

### 5.5 MIPSEL — Labs 21 à 23

**Différences clés vs ARM :**

- `$ra` ($31) = registre de retour, sauvegardé par `sw $ra, 92($sp)`
- O32 ABI : 16 bytes d'arg area réservés + sauvegarde `$gp` à sp+16 → buffer commence à sp+24
- Branch delay slot : l'instruction après `jr $ra` s'exécute avant le saut
- `$ra` loop : `jr $ra` ne modifie pas `$ra` → win() boucle à l'infini → utiliser `recvline()` pas `recvall()`
- `qemu-mipsel -L /usr/mipsel-linux-gnu` + `mipsel-linux-gnu-objdump`

**OFFSET universel : 68 pour buf[64] dans les 3 architectures**

Ce n'est pas une coïncidence — l'ABI de chaque architecture aligne le buffer et le registre de retour de façon similaire pour ce cas.

### 5.6 Firmware IoT — Lab 22

Analyse du firmware fictif `AngeRouter v2.1` (MIPSEL, SquashFS + header custom `ANGFW`) :

| Vulnérabilité | Localisation | Impact |
| --- | --- | --- |
| Credentials en clair | `/etc/config/httpd.conf` | Compromission admin |
| Fichier caché | `/var/.secret` | Exfiltration flag |
| Secret hardcodé | `bin/httpd` (strings) | Reverse engineering trivial |
| Backdoor nc | `/usr/share/backdoor.sh` | RCE port 31337 |
| strcpy overflow | `parse_auth()` dans httpd | Stack smashing → RCE |
| Hash MD5 faible | `/etc/passwd` (support) | Bruteforce |

**Pipeline d'analyse :**

```bash
binwalk firmware.bin          # détection SquashFS offset 0x8
binwalk -e firmware.bin       # extraction automatique
unsquashfs *.squashfs         # décompression filesystem
strings bin/httpd | grep flag # flags dans binaires
find . -name ".*" -type f     # fichiers cachés
```

### 5.7 Lab 23 — Exploitation du firmware (parse_auth overflow)

Continuité directe du Lab22 : le binaire `httpd` extrait du firmware est exploité via son `strcpy` dans `parse_auth()`.

```c
void parse_auth(const char *input) {
    char buf[64];
    strcpy(buf, input);   /* overflow : input non borné */
}
```

Résultat : `OFFSET=68`, `$ra` → `win()`, flag obtenu via pwntools + qemu-mipsel.

---

## 6. Comparatif x86 / ARM / MIPS

| Élément | x86-32 | ARM32 | MIPSEL |
| --- | --- | --- | --- |
| Registre retour | EIP (sur stack) | LR (R14) | $ra ($31) |
| Sauvegarde | implicite via `call` | `push {lr}` | `sw $ra, N($sp)` |
| Restauration | `ret` | `pop {pc}` | `jr $ra` |
| Syscall | `int 0x80` (EAX=nr) | `SVC #0` (R7=nr) | `syscall` ($v0=nr) |
| Nr execve | 11 | 11 | 4011 |
| OFFSET buf[64] | 68 | 68 | 68 |
| Gadgets ROP | `pop reg; ret` | `pop {reg, pc}` | `lw $a0; jr $ra` |
| Émulateur | natif | qemu-arm | qemu-mipsel |
| Objdump | `objdump -d` | `objdump -d` | `mipsel-linux-gnu-objdump -d` |

---

## 7. Projet final — AI-Assisted Embedded Attack Framework

### 7.1 Concept

Un framework qui combine l'analyse statique de firmware, la détection d'architecture, l'identification automatique de vulnérabilités, et l'explication assistée par LLM. Il ferme la boucle entre les 4 piliers.

### 7.2 Architecture

```text
Firmware binaire (entrée)
        │
        ▼ Module 1 — Extraction
    binwalk → SquashFS → filesystem
        │
        ▼ Module 2 — Détection architecture
    file + readelf → ARM / MIPS / x86
        │
        ▼ Module 3 — Analyse vulnérabilités
    strings → credentials hardcodés
    Ghidra/angr → fonctions dangereuses (strcpy, gets, sprintf)
    checksec → protections actives
        │
        ▼ Module 4 — Explication LLM
    RAG local (LLaMA3.1 + ChromaDB)
    + LangFuse tracing
    + guardrails OWASP
        │
        ▼ Rapport structuré (vulnérabilités + vecteurs d'exploitation)
```

### 7.3 Valeur ajoutée

Ce framework automatise en 4 minutes ce qui prenait 2 heures manuellement en Lab22, et produit une explication en langage naturel compréhensible par une équipe non spécialisée.

---

## 8. Leçons techniques retenues

**1. L'OFFSET ne se devine pas, il se calcule.**
Lire le prologue de la fonction vulnérable dans objdump. La position du registre de retour moins la position du buffer donne l'OFFSET exact.

**2. Les ABI créent des surprises invisibles.**
En MIPS O32, 16 bytes d'arg area + sauvegarde de `$gp` font que le buffer ne commence pas à sp+0 mais à sp+24. Sans lire l'ABI, cyclic révèle l'OFFSET mais ne l'explique pas.

**3. QEMU user-mode neutralise ASLR.**
Les adresses sont fixes dans tous les labs émulés. En conditions réelles, un leak est obligatoire avant tout ret2win.

**4. La méthode est universelle, la syntaxe change.**
`b'A' * 68 + p32(win_addr)` fonctionne sur x86, ARM et MIPS. C'est le même exploit, compilé pour trois ISAs différents.

**5. Un LLM avec des outils est une surface d'attaque.**
Excessive Agency (OWASP LLM08) est la vulnérabilité la plus critique des agents. Chaque outil donné au LLM doit être traité comme un vecteur potentiel.

**6. Cloud + LLM = IAM².**
Les mauvaises configurations IAM AWS se propagent aux modèles Bedrock. La sécurité d'un LLM cloud dépend autant de la politique IAM que du modèle lui-même.

---

## 9. Stack technique complète

### Outils PWN / Reverse Engineering

| Outil | Usage |
| --- | --- |
| GDB + pwndbg | Debugging dynamique, registres, breakpoints |
| GDB-multiarch | Debug cross-architecture (ARM, MIPS) |
| Ghidra | Décompilation statique x86 / ARM / MIPS |
| pwntools | Scripting exploits, cyclic, p32/p64 |
| ROPgadget | Recherche gadgets ROP |
| binwalk | Extraction et analyse firmwares IoT |
| objdump / mipsel-linux-gnu-objdump | Désassemblage cross-architecture |
| QEMU user-mode | Émulation ARM32, MIPSEL |
| checksec | Analyse protections (NX, canary, PIE, ASLR) |

### Outils LLMOps

| Outil | Usage |
| --- | --- |
| Ollama + LLaMA3.1:8b | LLM local GPU |
| LangChain | Orchestration, RAG, agents |
| LangFuse | Tracing, métriques, observabilité |
| ChromaDB | Vectorstore local |
| RAGAS | Évaluation RAG (faithfulness, relevancy) |
| NeMo Guardrails | Guardrails LLM (input/output rails) |
| Prometheus + Grafana | Monitoring production |

---

Ngagne Demba Dia · AngeVirusLab · Master Sécurité des Systèmes Embarqués · UCAD · Dakar, 2026
