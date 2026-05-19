# Références — C / ASM x86 : Pointeurs, Mémoire & GDB
### Shadow Bytes · Pilier 0
*AngeVirus — UCAD · Dakar 2026*

---

## 1. Livres — Les Références Absolues

### 1.1 Computer Systems: A Programmer's Perspective (CS:APP)
**Auteurs :** Randal E. Bryant & David R. O'Hallaron
**Édition :** 3e édition (2015)

Le livre de référence pour comprendre comment un ordinateur fonctionne vraiment.
Écrit par deux professeurs de Carnegie Mellon University.

**Chapitres prioritaires pour ce cours :**

| Chapitre | Titre | Pertinence |
|---|---|---|
| **Chapitre 2** | Representing and Manipulating Information | Représentation binaire, entiers, débordement |
| **Chapitre 3** | Machine-Level Representation of Programs | ⭐ C → ASM x86, registres, stack, calling convention |
| **Chapitre 6** | The Memory Hierarchy | Cache, mémoire, latence |
| **Chapitre 9** | Virtual Memory | Espace adresse virtuel, segmentation, pages |

> **Chapitre 3 est le plus important** pour ce cours.
> Il explique exactement comment le compilateur traduit le C en ASM,
> comment la stack est organisée, et comment les fonctions s'appellent.

**Où le trouver :** PDF disponible librement en cherchant "CS:APP 3rd edition PDF"
**Site officiel :** csapp.cs.cmu.edu (labs disponibles gratuitement)

---

### 1.2 Hacking: The Art of Exploitation
**Auteur :** Jon Erickson
**Édition :** 2e édition (2008) — No Starch Press

Le livre qui connecte directement la programmation C, l'assembleur x86,
et l'exploitation. Écrit pour les hackers, pas les académiciens.

**Chapitres prioritaires :**

| Chapitre | Titre | Pertinence |
|---|---|---|
| **Chapitre 1** | Introduction | Pensée hacker |
| **Chapitre 2** | Programming | C, pointeurs, mémoire — la base |
| **Chapitre 3** | Exploitation | Buffer overflow, format string, heap |
| **Chapitre 4** | Networking | Sockets C |
| **Chapitre 5** | Shellcode | Écrire du shellcode x86 |

> **Chapitre 2 et 3 couvrent exactement ce cours.**
> Le livre vient avec un LiveCD pour pratiquer dans un environnement
> sans protections modernes — idéal pour apprendre les bases.

**Niveau :** Débutant → Intermédiaire
**Où le trouver :** No Starch Press (payant) ou recherche PDF

---

### 1.3 The C Programming Language (K&R)
**Auteurs :** Brian Kernighan & Dennis Ritchie
**Édition :** 2e édition (1988)

Écrit par le créateur du langage C. Court, dense, précis.
Pas un tutoriel moderne — c'est la référence originale.

**Chapitres prioritaires :**

| Chapitre | Titre | Pertinence |
|---|---|---|
| **Chapitre 5** | Pointers and Arrays | ⭐ Pointeurs complets |
| **Chapitre 7** | Input and Output | stdin, stdout, fichiers |
| **Chapitre 8** | The UNIX System Interface | Bas niveau UNIX, mémoire |

> À lire après avoir pratiqué avec les mini-projets.
> Ce livre clarifie des subtilités que les tutoriels modernes n'expliquent jamais.

---

### 1.4 Low-Level Programming
**Auteur :** Igor Zhirkov (2017) — Apress

Moderne, progressif, couvre C et ASM x86-64 ensemble.
Explique comment C se traduit en assembleur pas à pas.

**Points forts :**
- Couvre x86-64 (le standard actuel, pas x86 32 bits vieilli)
- Exercices pratiques à chaque chapitre
- Exemples réels de vulnérabilités

---

## 2. Cours en Ligne Gratuits

### 2.1 OpenSecurityTraining2 — Introductory Intel x86
**URL :** opensecuritytraining2.info/IntroX86.html
**Durée :** ~30 heures

Le cours universitaire gratuit le plus complet sur x86.
Créé par des professionnels de la sécurité, utilisé dans des universités américaines.

**Modules à suivre dans l'ordre :**

| Module | Contenu | Priorité |
|---|---|---|
| 1 | Introduction, architecture IA-32 | ⭐⭐⭐ |
| 2 | Registres, flags, modes d'adressage | ⭐⭐⭐ |
| 3 | Instructions de base (MOV, ADD, SUB...) | ⭐⭐⭐ |
| 4 | Stack et calling convention | ⭐⭐⭐ |
| 5 | Fonctions, prologue/épilogue | ⭐⭐⭐ |
| 6 | Buffer overflows | ⭐⭐⭐ |

> **C'est la ressource principale pour la partie ASM de ce programme.**
> Les slides sont disponibles gratuitement + vidéos YouTube associées.

---

### 2.2 CS:APP Labs — Carnegie Mellon University
**URL :** csapp.cs.cmu.edu/3e/labs.html
**Coût :** 0$

Les labs officiels du livre CS:APP, disponibles sans acheter le livre.

| Lab | Contenu | Semaine programme |
|---|---|---|
| **Data Lab** | Manipulation bits et entiers | Sem 1-2 |
| **Bomb Lab** | Reverse engineering avec GDB | Sem 2-3 |
| **Attack Lab** | Buffer overflow et ROP | Sem 4-8 |
| **Cache Lab** | Performance mémoire | Référence |

> **Bomb Lab et Attack Lab** sont les plus pertinents pour le Pilier 0.
> Bomb Lab : tu dois désassembler un programme pour trouver les "mots de passe".
> Attack Lab : tu construis de vrais exploits step by step.

---

### 2.3 pwn.college
**URL :** pwn.college
**Coût :** 0$

Plateforme universitaire (Arizona State University) de challenges progressifs.
Chaque module est un cours + labs interactifs dans un environnement sécurisé.

**Modules dans l'ordre pour ce cours :**

| Module | Contenu | Semaine |
|---|---|---|
| **Program Misuse** | Comportement des programmes, shell | Sem 1 |
| **Debugging Refresher** | GDB, pwndbg, analyse | Sem 1-2 |
| **Assembly Crash Course** | x86-64 ASM de zéro | Sem 2 |
| **Reverse Engineering** | Lire et comprendre le binaire | Sem 2-3 |
| **Memory Errors** | Buffer overflow, stack smashing | Sem 4 |
| **Shellcode Injection** | Écrire et injecter du shellcode | Sem 5-6 |
| **Return Oriented Programming** | ROP chains | Sem 12 |

> **pwn.college est la meilleure plateforme pratique disponible.**
> Chaque niveau est un binaire réel à exploiter avec des hints progressifs.
> Gratuit, créé par des professeurs de sécurité, reconnu mondialement.

---

### 2.4 Azeria Labs — ARM et ASM
**URL :** azeria-labs.com
**Coût :** 0$

Référence pour ARM mais les articles sur les concepts de base
(stack frame, calling convention, GDB) s'appliquent aussi à x86.

**Articles utiles pour ce cours :**
- "Introduction to ARM Assembly Basics" → concepts valables en x86 aussi
- "Debugging with GDB" → guide GDB complet avec exemples
- "Stack and Functions" → calling convention expliquée visuellement

---

### 2.5 LiveOverflow — YouTube
**URL :** youtube.com/@LiveOverflow
**Coût :** 0$

La meilleure chaîne YouTube pour l'exploitation binaire.
Format : solve de CTF en temps réel avec explications détaillées.

**Playlists prioritaires :**

| Playlist | Contenu | Quand regarder |
|---|---|---|
| **"Binary Exploitation / Memory Corruption"** | Buffer overflow, GDB, exploits | Sem 1-4 |
| **"How do computers work?"** | Architecture bas niveau | Sem 1 |
| **"CTF - Capture The Flag"** | Solve de challenges réels | Sem 6+ |

> Commence par la série "Binary Exploitation" —
> la vidéo "buffer overflow" de LiveOverflow est regardée par tous les pwners débutants.

---

### 2.6 John Hammond — YouTube
**URL :** youtube.com/@_JohnHammond
**Coût :** 0$

Solve de CTF accessibles, bien expliqués. Bon complément à LiveOverflow
pour voir différentes approches sur les mêmes problèmes.

---

## 3. Outils — Documentation Officielle

### 3.1 GDB Documentation
**URL :** sourceware.org/gdb/documentation/

| Document | Contenu |
|---|---|
| GDB User Manual | Référence complète de toutes les commandes |
| GDB Quick Reference Card | PDF 2 pages — toutes les commandes essentielles |

**Commande GDB la plus utile à retenir :**
```
(gdb) help [commande]    ← affiche l'aide de n'importe quelle commande
```

---

### 3.2 pwndbg — Extension GDB
**URL :** github.com/pwndbg/pwndbg
**Documentation :** pwndbg.readthedocs.io

Rend GDB lisible : registres colorés, stack automatiquement affichée,
contexte visuel à chaque step.

**Commandes pwndbg supplémentaires :**
```
context          ← affiche registres + stack + code en une fois
stack 20         ← affiche les 20 premiers éléments de la stack
telescope $esp   ← affiche stack avec déréférencement automatique
checksec         ← affiche les protections du binaire (ASLR, NX, PIE, canary)
cyclic 100       ← génère un pattern de 100 octets pour trouver l'offset EIP
cyclic -l 0x61616175  ← trouve à quelle position est cette valeur dans le pattern
```

---

### 3.3 pwntools
**URL :** docs.pwntools.com
**Installation :** `pip install pwntools`

Framework Python pour écrire des exploits. À partir de la Semaine 4.

```python
from pwn import *

# Connexion au programme
p = process('./programme_vulnerable')

# Construire un payload
payload = b'A' * 40          # padding
payload += p32(0x08048420)   # adresse de win() en little-endian

# Envoyer et interagir
p.sendline(payload)
p.interactive()
```

---

### 3.4 checksec
**Installation :** `pip install checksec.py` ou inclus dans pwntools

Analyse les protections d'un binaire avant d'attaquer :

```bash
checksec ./programme

# Output typique :
    Arch:     amd64-64-little
    RELRO:    Partial RELRO
    Stack:    No canary found    ← pas de canary → overflow possible
    NX:       NX disabled        ← stack exécutable → shellcode possible
    PIE:      No PIE             ← adresses fixes → pas d'ASLR
```

**Signification des protections :**

| Protection | Rôle | Contournement (futur) |
|---|---|---|
| **Stack Canary** | Valeur sentinelle avant l'adresse de retour — crash si modifiée | Leak du canary (Sem 9) |
| **NX / DEP** | Stack non exécutable — ne peut pas exécuter du shellcode | ROP chains (Sem 12) |
| **PIE** | Adresses aléatoires à chaque exécution | Leak d'adresse (Sem 9) |
| **RELRO** | Section GOT en lecture seule | Full RELRO = GOT overwrite impossible |
| **ASLR** | Randomisation du heap/stack/libs | Brute force ou leak |

---

## 4. Plateformes de Pratique

### 4.1 pwn.college ⭐ (principale)
**URL :** pwn.college
Cours + labs intégrés, environnement Docker sécurisé.
Commence par : Debugging Refresher → Assembly → Memory Errors.

### 4.2 crackme.one
**URL :** crackme.one
Challenges de reverse engineering classés par difficulté.
Commence par les niveaux "easy" en x86/x64.

### 4.3 HackTheBox — PWN Track
**URL :** app.hackthebox.com
Challenges de pwn classés par difficulté. Commence par "Very Easy".
Les binaires HTB représentent des vulnérabilités réalistes.

### 4.4 picoCTF — Binary Exploitation
**URL :** picoctf.org
CTF permanent créé par Carnegie Mellon (les mêmes que CS:APP).
Parfait pour les débutants — hints disponibles, niveaux très progressifs.

### 4.5 Exploit Education
**URL :** exploit.education
VMs préconfigurées avec des binaires vulnérables classiques.
- **Phoenix** : progression linéaire stack overflow → heap → format string
- **Nebula** : exploitation Linux niveau débutant

### 4.6 nightmare — guyinatuxedo (GitHub)
**URL :** github.com/guyinatuxedo/nightmare
Collection de write-ups CTF organisés par technique d'exploitation.
Excellente référence pour comprendre comment les challenges sont résolus.

---

## 5. Cheatsheets à Garder Sous la Main

### 5.1 Registres x86 / x86-64

```
x86 (32 bits)    x86-64 (64 bits)   Rôle
EAX              RAX                Accumulateur, valeur de retour
EBX              RBX                Usage général
ECX              RCX                Compteur
EDX              RDX                Données
ESI              RSI                Source Index (src en string ops)
EDI              RDI                Destination Index + 1er arg (64 bits)
ESP              RSP                Stack Pointer (sommet de stack)
EBP              RBP                Base Pointer (base du frame)
EIP              RIP                Instruction Pointer ← le plus important
```

### 5.2 Calling Convention x86 (cdecl)

```
Appelant (caller) :
  1. Pousse les arguments sur la stack (de droite à gauche)
  2. CALL instruction (pousse EIP + saute)

Appelé (callee) — Prologue :
  PUSH EBP        ← sauvegarde le vieux EBP
  MOV EBP, ESP    ← EBP = ESP (début du nouveau frame)
  SUB ESP, N      ← réserve N octets pour les variables locales

Appelé (callee) — Épilogue :
  MOV ESP, EBP    ← restaure ESP
  POP EBP         ← restaure l'ancien EBP
  RET             ← POP EIP (retour à l'appelant)
```

### 5.3 Layout de la Stack lors d'un appel de fonction

```
Adresses hautes
┌──────────────────┐
│  arg2            │  ← poussé en premier (cdecl = droite à gauche)
├──────────────────┤
│  arg1            │
├──────────────────┤
│  adresse retour  │  ← EIP sauvegardé par CALL ← CIBLE du buffer overflow
├──────────────────┤
│  saved EBP       │  ← EBP sauvegardé par le prologue
├──────────────────┤  ← EBP pointe ici après le prologue
│  variable locale │
│  variable locale │
│  buf[32]         │  ← commence ici (adresses basses)
└──────────────────┘  ← ESP pointe ici
Adresses basses
```

### 5.4 GDB Quick Reference

```bash
gdb ./prog              # lancer
run [args]              # exécuter
r < input.txt           # avec stdin

b main                  # breakpoint
b *0x08048420           # breakpoint sur adresse
b fichier.c:42          # breakpoint sur ligne

n                       # next (pas à pas, sans entrer)
s                       # step (pas à pas, entre dans les fonctions)
c                       # continue
finish                  # terminer la fonction courante

i r                     # info registers
i r eip                 # juste EIP
bt                      # backtrace
p variable              # print
p/x variable            # print en hex
p *pointeur             # valeur pointée

x/10x $esp              # 10 mots hex depuis ESP
x/20x 0x08048000        # 20 mots à une adresse
x/s $rdi                # string à l'adresse dans RDI
x/i $eip                # instruction à EIP
disas main              # désassembler main

q                       # quit
```

---

## 6. Ordre d'apprentissage Recommandé

```
SEMAINE 1 (maintenant)
  Lire   → CS:APP Chapitre 3 sections 3.1-3.4 (intro x86, registres)
  Cours  → OpenSecurityTraining2 Modules 1-2
  Labs   → Mini-projets MP1 à MP5 du cours
  Vidéo  → LiveOverflow "How does a Buffer Overflow work?" (YouTube)

SEMAINE 2
  Lire   → CS:APP Chapitre 3 sections 3.7 (Procedures = calling convention)
  Cours  → OpenSecurityTraining2 Modules 3-4
  Labs   → pwn.college "Debugging Refresher" + "Assembly Crash Course"
  Vidéo  → LiveOverflow "Buffer Overflow series" (3-4 vidéos)

SEMAINE 3
  Lire   → Hacking: The Art of Exploitation Chapitre 2
  Labs   → CS:APP Bomb Lab (reverse avec GDB)
  Pratique → 2 challenges crackme.one niveau easy

SEMAINE 4
  Lire   → Hacking: The Art of Exploitation Chapitre 3
  Labs   → CS:APP Attack Lab + pwn.college "Memory Errors"
  Projet → Premier exploit ret2win complet
```

---

*Shadow Bytes Red Team · UCAD · Dakar — Références Pilier 0*
*Toutes les ressources listées sont gratuites sauf mention contraire*
