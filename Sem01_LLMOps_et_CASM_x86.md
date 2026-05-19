# Semaine 1 — LLMOps Fondamentaux + C/ASM x86
### Shadow Bytes · Pilier 0 · Légère · 2h
*AngeVirus — UCAD · Dakar 2026*

---

## Plan de la semaine

| Partie | Durée | Contenu |
|---|---|---|
| **Partie 1 — LLMOps** | ~50 min | LLMOps vs MLOps vs AIOps — pipeline + notes |
| **Partie 2 — C/ASM x86** | ~70 min | Pointeurs → malloc/free → segfault → GDB |

**Livrables :**
- [ ] Notes pipeline LLMOps comparé à MLOps (en tes propres mots)
- [ ] 4 mini-projets C compilés et testés
- [ ] Segfault analysé dans GDB avec explication de la cause

---

# PARTIE 1 — LLMOps Fondamentaux (~50 min)

## Ce que tu dois retenir

> Un LLM en production a des problèmes que MLOps n'a jamais eu à gérer :
> hallucinations, prompt injection, coût par token, jailbreaks.
> **LLMOps est une discipline à part — pas un sous-ensemble de MLOps.**

---

## 1.1 Les trois disciplines — ne jamais confondre

### MLOps (2017)
Pour les modèles classiques : sklearn, XGBoost, régression.
- Drift = drift des **données** → retraining
- Métriques : accuracy, F1, AUC
- Pipeline : `données → train → deploy → monitor`

### AIOps
Monitoring IT avec du ML (Datadog avec du ML dedans).
Détecte des anomalies sur des logs/infra.
**N'a rien à voir avec le déploiement de LLMs génératifs.**

### LLMOps (2023+)
Pour les LLMs : GPT-4, Claude, LLaMA3.
- Drift = **prompt drift** (même prompt → réponses différentes)
- Métriques : faithfulness, hallucination rate, **token cost**, latence P95
- Pipeline :

```
User Input
    ↓
[Guardrails IN]     ← bloque prompt injection, PII, hors-sujet
    ↓
LLM / Agent         ← GPT-4, LLaMA3, Claude...
    ↓
[Guardrails OUT]    ← filtre hallucinations, données sensibles
    ↓
Réponse
    ↓
[Observabilité]     ← LangFuse trace tout : tokens, latence, coût
```

---

## 1.2 Tableau comparatif — à mémoriser

| | MLOps | AIOps | **LLMOps** |
|---|---|---|---|
| Modèle | Classique | Monitoring IT | **LLMs génératifs** |
| Drift | Data drift | Anomalies infra | **Prompt drift** |
| Métriques | Accuracy, F1 | MTTR | **Faithfulness, token cost, latence P95** |
| Versioning | Modèle + données | — | **Prompt + modèle + config** |
| Sécurité | Adversarial ML | — | **Prompt injection, jailbreak** |
| Outils | MLflow, DVC | Datadog | **LangFuse, LangSmith, NeMo** |

---

## 1.3 Les 4 nouveaux problèmes LLMOps

**Hallucination** — Le LLM invente des faits convaincants mais faux.
→ Fix : RAG avec sources vérifiables + garde-fous output.

**Prompt Drift** — Un mot changé dans le prompt peut tout changer silencieusement.
→ Chip Huyen : *"Prompt changes execute silently — no error messages when output quality degrades."*
→ Fix : versioning de prompts + tests automatiques.

**Coût token** — Chaque appel API coûte. GPT-4 = $0.624 pour 10k tokens input + 200 output.
→ Fix : tracker chaque token avec LangFuse, cacher les réponses répétées.

**Prompt Injection** — Un utilisateur manipule le LLM pour dépasser ses limites.
→ Connexion directe avec le Lab 1 Pilier 1 (Excessive Agency).
→ Fix : NeMo Guardrails + validation des inputs.

---

## 1.4 Connexion avec la suite du programme

```
Sem 1-2  → Tu comprends LLMOps théoriquement
Sem 3    → Tu déploies un vrai agent LLM local (Ollama + LLaMA3 + LangFuse)
Sem 6    → Tu construis le pipeline RAG complet
Sem 8    → Tu livres le projet final LLMOps
         ↓
Pilier 1 → Tu attaques exactement ce que tu as construit
```

---

## 1.5 Livrable Partie 1

Rédige **une page de notes** (format libre) avec :
- Ton propre schéma ASCII du pipeline LLMOps
- Le tableau comparatif en tes propres mots
- Un exemple de problème LLMOps que tu pourrais voir chez CCDOC

**Ressources pour cette partie :**
- `huyenchip.com/blog` → lire "Building LLM Applications for Production" (2023)
- `github.com/tensorchord/Awesome-LLMOps` → survole les catégories observability + prompt management

---

# PARTIE 2 — C / ASM x86 : Pointeurs, Mémoire, GDB (~70 min)

## Philosophie de la partie 2

> Avant d'exploiter un buffer overflow (Sem 4), tu dois comprendre
> comment C gère la mémoire. On va du plus simple au plus complexe :
> **pointeurs → malloc/free → segfault → analyser avec GDB.**

**Environnement nécessaire :**
- Linux (WSL sur Windows, ou VM Ubuntu)
- GCC : `sudo apt install gcc`
- GDB : `sudo apt install gdb`
- GDB extension pwndbg (recommandé) : `git clone https://github.com/pwndbg/pwndbg && cd pwndbg && ./setup.sh`

---

## Mini-projet 1 — Les pointeurs, c'est quoi ? (15 min)

### Concept
En C, chaque variable a une **adresse mémoire**.
Un pointeur est une variable qui **stocke une adresse**.

```
Variable normale :  int x = 42;
                    x est stocké quelque part en mémoire, disons à l'adresse 0xffe8

Pointeur :          int *p = &x;
                    p contient la valeur 0xffe8 (l'adresse de x)
                    *p donne la valeur à cette adresse, donc 42
```

### Code — mini_projet_1_pointeurs.c

```c
#include <stdio.h>

int main() {
    int x = 42;
    int *p = &x;   // p pointe vers x

    printf("Valeur de x         : %d\n", x);
    printf("Adresse de x        : %p\n", (void*)&x);
    printf("Valeur de p (adresse): %p\n", (void*)p);
    printf("Valeur pointée *p   : %d\n", *p);

    // Modifier x via le pointeur
    *p = 100;
    printf("x après *p = 100    : %d\n", x);

    return 0;
}
```

### Commandes
```bash
gcc -o mp1 mini_projet_1_pointeurs.c
./mp1
```

### Ce que tu dois observer
- L'adresse de `x` et la valeur de `p` sont **identiques**
- Modifier `*p` modifie directement `x` — c'est le même emplacement mémoire
- Les adresses ressemblent à `0x7ffd...` (stack) — retiens ça pour la suite

### Question à te poser
> Si je fais `p = p + 1`, à quelle adresse est-ce que je pointe maintenant ?
> Qu'est-ce qui se passe si je lis `*(p+1)` ?

---

## Mini-projet 2 — Stack vs Heap : malloc et free (20 min)

### Concept
Il y a deux zones mémoire principales en C :

```
MÉMOIRE D'UN PROCESSUS C

┌─────────────────────┐  ← haute adresse
│       Stack         │  Variables locales, paramètres de fonctions
│    (grandit ↓)      │  Libérées automatiquement à la fin de la fonction
├─────────────────────┤
│       Heap          │  malloc/calloc/realloc → tu gères toi-même
│    (grandit ↑)      │  DOIT être libéré avec free()
├─────────────────────┤
│   Code (texte)      │  Ton programme compilé
│   Données globales  │  Variables globales et statiques
└─────────────────────┘  ← basse adresse
```

**Règle d'or :** Tout ce que tu `malloc`, tu dois `free`. Sinon = fuite mémoire.

### Code — mini_projet_2_malloc.c

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main() {
    // --- STACK : allocation automatique ---
    int stack_var = 10;
    printf("[STACK] stack_var  adresse : %p\n", (void*)&stack_var);

    // --- HEAP : allocation manuelle ---
    int *heap_int = malloc(sizeof(int));        // alloue 4 octets sur le heap
    char *heap_str = malloc(50 * sizeof(char)); // alloue 50 octets

    if (heap_int == NULL || heap_str == NULL) {
        printf("Erreur malloc !\n");
        return 1;
    }

    *heap_int = 99;
    strcpy(heap_str, "Shadow Bytes");

    printf("[HEAP]  heap_int   adresse : %p  valeur : %d\n", (void*)heap_int, *heap_int);
    printf("[HEAP]  heap_str   adresse : %p  valeur : %s\n", (void*)heap_str, heap_str);

    // Toujours libérer la mémoire heap
    free(heap_int);
    free(heap_str);

    // DANGER — ne jamais utiliser après free
    // printf("%d", *heap_int);  // use-after-free → comportement indéfini

    printf("\nMémoire libérée proprement.\n");
    return 0;
}
```

### Commandes
```bash
gcc -o mp2 mini_projet_2_malloc.c
./mp2
```

### Ce que tu dois observer
- Les adresses stack (`0x7fff...`) sont différentes des adresses heap (`0x5555...` ou `0x000055...`)
- Stack = adresses hautes, Heap = adresses basses
- Ce pattern sera crucial pour comprendre les exploits : stack overflow vs heap overflow

### Ce qu'on ne fait PAS dans ce mini-projet (mais qu'on verra plus tard)
- Double free → crash
- Use-after-free → comportement indéfini, exploitable en Pilier 1
- Buffer overflow sur le heap → Sem 14

---

## Mini-projet 3 — Provoquer un Segfault volontairement (15 min)

### Concept
Un **Segmentation Fault** = le programme tente d'accéder à une zone mémoire
qui ne lui appartient pas. Le kernel le tue.

En exploitation, forcer un segfault est la première étape pour prouver qu'on contrôle
le flux d'exécution.

### Code — mini_projet_3_segfault.c

```c
#include <stdio.h>
#include <stdlib.h>

// Cas 1 : déréférencement de NULL
void segfault_null() {
    int *p = NULL;
    printf("Avant le crash (p = NULL)\n");
    *p = 42;  // SEGFAULT ici — écriture à l'adresse 0x0
}

// Cas 2 : dépassement de tableau (buffer overflow classique)
void segfault_overflow() {
    char buf[8];
    printf("Buffer de 8 octets. On écrit 200 octets...\n");
    for (int i = 0; i < 200; i++) {
        buf[i] = 'A';  // SEGFAULT après ~8-16 octets selon la config
    }
}

// Cas 3 : accès à un pointeur non initialisé
void segfault_uninit() {
    int *p;  // pointeur non initialisé → valeur aléatoire
    printf("Pointeur non initialisé : %p\n", (void*)p);
    *p = 42;  // SEGFAULT — adresse aléatoire probablement interdite
}

int main(int argc, char *argv[]) {
    if (argc < 2) {
        printf("Usage: ./mp3 [1|2|3]\n");
        printf("  1 = déréférencement NULL\n");
        printf("  2 = buffer overflow\n");
        printf("  3 = pointeur non initialisé\n");
        return 0;
    }

    int choix = atoi(argv[1]);
    if (choix == 1) segfault_null();
    if (choix == 2) segfault_overflow();
    if (choix == 3) segfault_uninit();

    return 0;
}
```

### Commandes
```bash
# Compiler SANS protections (pour voir le comportement brut)
gcc -o mp3 mini_projet_3_segfault.c -fno-stack-protector -z execstack

# Tester les trois cas
./mp3 1    # Segmentation fault (core dumped)
./mp3 2    # Segmentation fault (core dumped)
./mp3 3    # Segmentation fault (core dumped)
```

### Ce que tu dois observer
- Les 3 cas crashent, mais pour des raisons différentes
- Le message est le même : `Segmentation fault (core dumped)`
- Sans GDB, tu ne sais pas POURQUOI ça crash → c'est le problème du mini-projet 4

---

## Mini-projet 4 — Analyser le Segfault avec GDB (20 min)

### Concept
GDB (GNU Debugger) te permet de :
- Exécuter le programme pas à pas
- Voir l'état des registres au moment du crash
- Identifier exactement **quelle ligne** et **quelle adresse** ont causé le segfault

C'est l'outil de base pour tout reverse engineering et exploitation.

### Installation pwndbg (une seule fois)
```bash
# pwndbg améliore l'affichage de GDB (registres colorés, stack visible, etc.)
git clone https://github.com/pwndbg/pwndbg
cd pwndbg
./setup.sh
cd ..
```

### Commandes GDB essentielles

| Commande | Action |
|---|---|
| `gdb ./programme` | Lance GDB avec le programme |
| `run` ou `r` | Exécute le programme |
| `run arg1 arg2` | Exécute avec arguments |
| `backtrace` ou `bt` | Affiche la pile d'appels au moment du crash |
| `info registers` ou `i r` | Affiche tous les registres (EIP/RIP = adresse de l'instruction courante) |
| `list` ou `l` | Affiche le code source autour du crash |
| `print variable` ou `p` | Affiche la valeur d'une variable |
| `x/10x $esp` | Affiche 10 mots en hex à partir du registre ESP (stack pointer) |
| `quit` ou `q` | Quitter GDB |

### Analyse du Cas 1 — Déréférencement NULL

```bash
# Recompiler avec symboles de debug (flag -g)
gcc -g -o mp3_debug mini_projet_3_segfault.c -fno-stack-protector

# Lancer GDB
gdb ./mp3_debug
```

```
(gdb) run 1
Starting program: ./mp3_debug 1
Avant le crash (p = NULL)

Program received signal SIGSEGV, Segmentation fault.
segfault_null () at mini_projet_3_segfault.c:10
10          *p = 42;
```

```
(gdb) backtrace
#0  segfault_null () at mini_projet_3_segfault.c:10
#1  main (argc=2, argv=0x...) at mini_projet_3_segfault.c:37
```

```
(gdb) info registers
eip            0x...     → adresse de l'instruction qui a crashé
esp            0x...     → sommet de la stack
ebp            0x...     → base de la stack frame courante
```

```
(gdb) print p
$1 = (int *) 0x0     → p vaut NULL (0x0) — écriture à l'adresse 0 = interdit
```

### Analyse du Cas 2 — Buffer Overflow

```bash
gdb ./mp3_debug
```

```
(gdb) run 2
Starting program: ./mp3_debug 2
Buffer de 8 octets. On écrit 200 octets...

Program received signal SIGSEGV, Segmentation fault.
0x41414141 in ?? ()
```

> **NOTE CLÉ :** `0x41414141` = "AAAA" en ASCII.
> Tu viens d'écraser le registre EIP (qui pointe vers l'instruction suivante)
> avec tes 'A'. **C'est exactement le principe d'un buffer overflow.**
> Le CPU essaie d'exécuter le code à l'adresse 0x41414141 → ça n'existe pas → SEGFAULT.

```
(gdb) info registers
eip   0x41414141   → EIP = AAAA = tu contrôles où le programme "saute" après la fonction
```

> En Semaine 4, tu feras pareil mais au lieu de mettre 'A',
> tu mettras l'adresse d'une fonction de ton choix. C'est un exploit.

### Script complet d'analyse (à garder comme référence)

```bash
# Template d'analyse GDB d'un crash
gdb -q ./programme_crashant << 'EOF'
set pagination off
run [arguments]
backtrace
info registers
x/20x $esp
list
quit
EOF
```

---

## Récapitulatif Partie 2 — Ce que tu dois avoir compris

```
Mini-projet 1 : Un pointeur = une adresse mémoire
                *p = valeur à cette adresse
                &x = adresse de la variable x

Mini-projet 2 : Stack = automatique (locale à la fonction)
                Heap  = manuel (malloc / free)
                malloc sans free = fuite mémoire
                Les adresses stack ≠ adresses heap

Mini-projet 3 : Segfault = accès mémoire interdit
                3 causes communes : NULL deref, overflow, pointeur non init

Mini-projet 4 : GDB permet de voir EXACTEMENT où et pourquoi ça crash
                EIP (x86) / RIP (x64) = l'adresse de la prochaine instruction
                Écraser EIP avec 0x41414141 = tu contrôles le flux → exploit
```

---

## Connexion avec la suite

```
Sem 1 (aujourd'hui) → Tu comprends pointeurs, malloc, segfault, GDB
Sem 2               → Tu étudies la stack frame x86 en détail (registres, calling convention)
Sem 3               → Tu lis le désassemblage de ton propre code C avec objdump + GDB
Sem 4               → Tu écris ton premier buffer overflow intentionnel et tu contrôles EIP
Sem 8               → Tu construis un exploit complet : ret2win fonctionnel
```

---

## Ressources C/ASM x86

| Ressource | Quoi | Durée |
|---|---|---|
| **opensecuritytraining2.info** | "Introductory Intel x86" — cours universitaire complet | Référence |
| **pwn.college** | Labs interactifs x86 progressifs | Semaines suivantes |
| **CS:APP (Bryant & O'Hallaron)** | Chapitre 3 (Machine-Level Representation) | Référence |
| **guyinatuxedo/nightmare** | github.com/guyinatuxedo/nightmare — CTF pwn ordonné par thème | Sem 4+ |
| **pwndbg** | github.com/pwndbg/pwndbg — GDB avec interface claire | Maintenant |

---

## Livrable final Semaine 1

**Avant de passer à la Semaine 2, tu dois avoir :**

- [ ] Lu "Building LLM Applications for Production" (Chip Huyen) — 30 min
- [ ] Rédigé tes notes LLMOps (schéma pipeline + tableau comparatif)
- [ ] Compilé et testé les 4 mini-projets C
- [ ] Analysé le segfault du cas 2 (buffer overflow) dans GDB et vu `0x41414141` dans EIP
- [ ] Noté dans tes propres mots : pourquoi le cas 2 est la base d'un exploit

---

*Shadow Bytes Red Team · UCAD · Dakar — Pilier 0, Semaine 1*
*Sources : Chip Huyen Blog · Awesome-LLMOps · CS:APP · OpenSecurityTraining2 · pwndbg*
*Formation 100% open source — 0$*
