# Cours Complet — C / ASM x86 : Pointeurs, Mémoire & GDB
### Shadow Bytes · Pilier 0 · Semaine 1
*AngeVirus — UCAD · Dakar 2026*

---

## Objectif du cours

À la fin de ce cours, tu seras capable de :
- Expliquer comment C gère la mémoire (stack, heap, segments)
- Utiliser les pointeurs sans te perdre
- Allouer et libérer de la mémoire dynamiquement
- Provoquer et identifier un segfault
- Analyser un crash avec GDB et lire l'état des registres

> **Pourquoi c'est crucial pour la sécurité ?**
> 90% des vulnérabilités classiques (buffer overflow, use-after-free, format string)
> exploitent une mauvaise gestion de la mémoire en C.
> Comprendre la mémoire = comprendre comment les exploits fonctionnent.

---

## Environnement requis

```bash
# Linux (WSL sur Windows, ou VM Ubuntu)
sudo apt update
sudo apt install gcc gdb python3 git -y

# pwndbg — rend GDB lisible (registres colorés, stack visible)
git clone https://github.com/pwndbg/pwndbg
cd pwndbg && ./setup.sh && cd ..

# Vérifier
gcc --version
gdb --version
```

---

# MODULE 1 — La Mémoire en C

## 1.1 Comment un programme C est organisé en mémoire

Quand tu lances un programme C, le système d'exploitation lui alloue un espace mémoire
divisé en plusieurs **segments** :

```
ADRESSES HAUTES
┌─────────────────────────────┐
│         STACK               │  ← Variables locales, paramètres, adresses de retour
│      (grandit ↓)            │     Gérée automatiquement par le compilateur
│                             │
│   ...espace libre...        │
│                             │
│         HEAP                │  ← malloc(), calloc() — tu gères toi-même
│      (grandit ↑)            │     DOIT être libéré avec free()
├─────────────────────────────┤
│   BSS (variables globales   │  ← Variables globales non initialisées (int x;)
│    non initialisées)        │
├─────────────────────────────┤
│   DATA (variables globales  │  ← Variables globales initialisées (int x = 5;)
│    initialisées)            │     Chaînes de caractères littérales
├─────────────────────────────┤
│   TEXT (code)               │  ← Ton programme compilé (instructions machine)
│                             │     Lecture seule — écrire ici = SEGFAULT
└─────────────────────────────┘
ADRESSES BASSES
```

**Ce que tu dois retenir :**

| Segment | Contenu | Durée de vie | Gestion |
|---|---|---|---|
| Stack | Variables locales, paramètres | Fin de la fonction | Automatique |
| Heap | malloc/calloc | Jusqu'à free() | **Manuelle** |
| Data/BSS | Variables globales | Tout le programme | Automatique |
| Text | Code machine | Tout le programme | Non modifiable |

---

## 1.2 La Stack en détail

La stack fonctionne comme une **pile de plateaux** au restaurant :
- On ajoute un plateau en haut (`PUSH`)
- On enlève toujours depuis le haut (`POP`)

Chaque appel de fonction crée un **stack frame** (un "plateau") qui contient :
- Les paramètres de la fonction
- L'adresse de retour (où continuer après la fonction)
- Les variables locales

```c
void fonctionB() {
    int y = 20;     // y est sur la stack, dans le frame de fonctionB
}                   // frame de fonctionB détruit ici → y n'existe plus

void fonctionA() {
    int x = 10;     // x est sur la stack, dans le frame de fonctionA
    fonctionB();    // nouveau frame empilé au-dessus
}                   // frame de fonctionA détruit ici → x n'existe plus

int main() {
    fonctionA();
    return 0;
}
```

```
Pendant l'exécution de fonctionB :

┌──────────────────┐  ← ESP (Stack Pointer) pointe ici
│  Frame fonctionB │
│  y = 20          │
│  ret addr → A    │  ← adresse pour revenir dans fonctionA
├──────────────────┤
│  Frame fonctionA │
│  x = 10          │
│  ret addr → main │  ← adresse pour revenir dans main
├──────────────────┤
│  Frame main      │
│  ...             │
└──────────────────┘
```

> **Note sécurité :** L'**adresse de retour** est stockée sur la stack.
> Si tu écrases cette adresse avec un buffer overflow → tu contrôles où le CPU saute.
> C'est le principe de base de tout exploit stack-based.

---

## 1.3 Mini-projet 1 — Observer la Stack

**Objectif :** Voir que les variables locales ont des adresses proches, et comprendre
que la stack grandit vers le bas.

```c
// mp1_stack.c
#include <stdio.h>

void fonctionB(int param) {
    int local_b = 200;
    printf("\n[fonctionB]\n");
    printf("  param   @ %p = %d\n", (void*)&param, param);
    printf("  local_b @ %p = %d\n", (void*)&local_b, local_b);
}

void fonctionA() {
    int local_a1 = 10;
    int local_a2 = 20;
    printf("\n[fonctionA]\n");
    printf("  local_a1 @ %p = %d\n", (void*)&local_a1, local_a1);
    printf("  local_a2 @ %p = %d\n", (void*)&local_a2, local_a2);
    fonctionB(99);
}

int main() {
    int local_main = 1;
    printf("\n[main]\n");
    printf("  local_main @ %p = %d\n", (void*)&local_main, local_main);
    fonctionA();
    return 0;
}
```

```bash
gcc -o mp1 mp1_stack.c
./mp1
```

**Ce que tu dois observer :**
- Les adresses de `main` sont plus hautes que celles de `fonctionA`
- Les adresses de `fonctionA` sont plus hautes que celles de `fonctionB`
- La stack **grandit vers le bas** (adresses décroissantes)
- `local_a1` et `local_a2` ont des adresses très proches (4 octets d'écart = taille d'un `int`)

---

# MODULE 2 — Les Pointeurs

## 2.1 Le concept fondamental

Un pointeur est une variable qui contient **une adresse mémoire**.

```
MÉMOIRE :

Adresse    Valeur
0x1000  →  42      ← int x = 42;
0x1004  →  0x1000  ← int *p = &x;  (p contient l'adresse de x)
```

**La syntaxe :**

```c
int x = 42;      // variable entière
int *p;          // déclaration d'un pointeur vers un int
p = &x;          // p = adresse de x  ("&" = "adresse de")
printf(*p);      // *p = valeur à l'adresse stockée dans p ("*" = "déréférencer")
```

**Les deux opérateurs :**

| Opérateur | Nom | Signification | Exemple |
|---|---|---|---|
| `&` | "adresse de" | Donne l'adresse d'une variable | `p = &x` |
| `*` | "déréférencement" | Accède à la valeur à cette adresse | `*p = 42` |

---

## 2.2 Mini-projet 2 — Les pointeurs de base

```c
// mp2_pointeurs.c
#include <stdio.h>

int main() {
    // --- Pointeur simple ---
    int x = 42;
    int *p = &x;

    printf("=== Pointeur simple ===\n");
    printf("x         = %d\n", x);
    printf("&x        = %p  (adresse de x)\n", (void*)&x);
    printf("p         = %p  (valeur de p = adresse de x)\n", (void*)p);
    printf("*p        = %d  (valeur à l'adresse p)\n", *p);

    // Modifier x via le pointeur
    *p = 100;
    printf("Après *p = 100 : x = %d\n\n", x);

    // --- Plusieurs pointeurs, même variable ---
    int y = 7;
    int *p1 = &y;
    int *p2 = &y;   // deux pointeurs pointent sur la même variable

    printf("=== Deux pointeurs, même variable ===\n");
    printf("*p1 = %d  *p2 = %d\n", *p1, *p2);
    *p1 = 99;
    printf("Après *p1 = 99 : *p2 = %d (même adresse !)\n\n", *p2);

    // --- Pointeur de pointeur ---
    int  z   = 5;
    int *pp  = &z;    // pointeur vers z
    int **ppp = &pp;  // pointeur vers le pointeur pp

    printf("=== Pointeur de pointeur ===\n");
    printf("z    = %d\n", z);
    printf("*pp  = %d  (valeur de z via pp)\n", *pp);
    printf("**ppp= %d  (valeur de z via ppp)\n", **ppp);

    return 0;
}
```

```bash
gcc -o mp2 mp2_pointeurs.c
./mp2
```

**Ce que tu dois comprendre après ce mini-projet :**
- `p` et `&x` ont la même valeur (même adresse)
- `*p` et `x` donnent le même résultat (même emplacement mémoire)
- Modifier via `*p` modifie directement `x`

---

## 2.3 Arithmétique des pointeurs

Quand tu fais `p + 1`, tu ne vas pas à l'adresse suivante en octets.
Tu avances de **la taille du type pointé**.

```c
int *p;    // p + 1 avance de 4 octets (taille d'un int)
char *c;   // c + 1 avance de 1 octet  (taille d'un char)
long *l;   // l + 1 avance de 8 octets (taille d'un long sur 64 bits)
```

```
MÉMOIRE (int *p pointe sur tableau[0]) :

Adresse   Valeur   Accès
0x100  →  10       p[0]  ou *p
0x104  →  20       p[1]  ou *(p+1)
0x108  →  30       p[2]  ou *(p+2)
0x10C  →  40       p[3]  ou *(p+3)
```

---

## 2.4 Mini-projet 3 — Pointeurs et Tableaux

```c
// mp3_arithmetique.c
#include <stdio.h>

int main() {
    int tab[] = {10, 20, 30, 40, 50};
    int *p = tab;   // p pointe sur le premier élément (tab == &tab[0])

    printf("=== Arithmétique des pointeurs ===\n");
    printf("Taille d'un int : %zu octets\n\n", sizeof(int));

    for (int i = 0; i < 5; i++) {
        printf("tab[%d] : adresse=%p  valeur=%d  (via pointeur : %d)\n",
               i, (void*)(p+i), tab[i], *(p+i));
    }

    printf("\n=== Notation tableau vs pointeur ===\n");
    printf("tab[2]    = %d\n", tab[2]);
    printf("*(p+2)    = %d  (identique)\n", *(p+2));
    printf("*(tab+2)  = %d  (identique aussi)\n", *(tab+2));
    printf("p[2]      = %d  (identique aussi)\n", p[2]);

    // Différence entre adresses
    printf("\n=== Différence d'adresses ===\n");
    printf("p+1 - p = %ld  (en nombre d'éléments)\n", (p+1) - p);
    printf("Adresse p   = %p\n", (void*)p);
    printf("Adresse p+1 = %p\n", (void*)(p+1));
    printf("Différence en octets = %ld\n", (char*)(p+1) - (char*)p);

    return 0;
}
```

```bash
gcc -o mp3 mp3_arithmetique.c
./mp3
```

---

## 2.5 Pointeurs et fonctions

En C, les arguments sont **passés par valeur** (une copie est faite).
Pour modifier une variable depuis une fonction, il faut passer **son adresse**.

```c
// Sans pointeur — ne fonctionne pas
void doubler_raté(int n) {
    n = n * 2;   // modifie la copie locale, pas l'original
}

// Avec pointeur — fonctionne
void doubler_ok(int *n) {
    *n = *n * 2;  // modifie la valeur à l'adresse reçue
}
```

---

## 2.6 Mini-projet 4 — Passage par référence

```c
// mp4_fonctions.c
#include <stdio.h>

// Ne modifie PAS l'original
void swap_rate(int a, int b) {
    int temp = a;
    a = b;
    b = temp;
    printf("[swap_raté]  a=%d b=%d (dans la fonction)\n", a, b);
}

// Modifie l'original via les pointeurs
void swap_ok(int *a, int *b) {
    int temp = *a;
    *a = *b;
    *b = temp;
}

// Retourne plusieurs valeurs via des pointeurs
void min_max(int *tab, int taille, int *min, int *max) {
    *min = tab[0];
    *max = tab[0];
    for (int i = 1; i < taille; i++) {
        if (tab[i] < *min) *min = tab[i];
        if (tab[i] > *max) *max = tab[i];
    }
}

int main() {
    // Test swap
    int x = 5, y = 10;
    printf("Avant swap : x=%d y=%d\n", x, y);

    swap_rate(x, y);
    printf("Après swap_raté : x=%d y=%d (inchangés !)\n", x, y);

    swap_ok(&x, &y);
    printf("Après swap_ok   : x=%d y=%d (échangés)\n\n", x, y);

    // Test min_max
    int tab[] = {34, 7, 92, 1, 55, 18};
    int min_val, max_val;
    min_max(tab, 6, &min_val, &max_val);
    printf("Tableau : {34, 7, 92, 1, 55, 18}\n");
    printf("Min = %d  Max = %d\n", min_val, max_val);

    return 0;
}
```

```bash
gcc -o mp4 mp4_fonctions.c
./mp4
```

---

# MODULE 3 — Allocation Dynamique : malloc et free

## 3.1 Pourquoi malloc ?

La stack a des limites :
- Taille fixée à la compilation (ou presque)
- Libérée à la fin de la fonction — tu ne peux pas retourner un tableau local

Le heap te permet d'allouer **la quantité que tu veux**, **quand tu veux**, et de la garder
aussi longtemps que tu en as besoin.

## 3.2 Les fonctions d'allocation

```c
#include <stdlib.h>

// malloc — alloue N octets, non initialisé (contient des données aléatoires)
void *malloc(size_t taille);

// calloc — alloue N éléments de taille T, initialisé à zéro
void *calloc(size_t nb_elements, size_t taille_element);

// realloc — redimensionne une allocation existante
void *realloc(void *ptr, size_t nouvelle_taille);

// free — libère la mémoire allouée
void free(void *ptr);
```

**Règles absolues :**
1. Toujours vérifier que malloc ne retourne pas NULL
2. Tout malloc doit avoir un free correspondant
3. Ne jamais free deux fois le même pointeur (double free)
4. Ne jamais utiliser un pointeur après free (use-after-free)

---

## 3.3 Mini-projet 5 — malloc et free

```c
// mp5_malloc.c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main() {
    // --- Allouer un entier sur le heap ---
    int *p_int = malloc(sizeof(int));
    if (p_int == NULL) { perror("malloc"); return 1; }
    *p_int = 42;
    printf("[INT]    adresse=%p  valeur=%d\n", (void*)p_int, *p_int);
    free(p_int);

    // --- Allouer un tableau ---
    int taille = 5;
    int *tableau = malloc(taille * sizeof(int));
    if (tableau == NULL) { perror("malloc"); return 1; }

    for (int i = 0; i < taille; i++)
        tableau[i] = (i + 1) * 10;

    printf("[TABLEAU] ");
    for (int i = 0; i < taille; i++)
        printf("%d ", tableau[i]);
    printf("\n");
    free(tableau);

    // --- calloc : initialisé à zéro ---
    int *zeros = calloc(5, sizeof(int));
    if (zeros == NULL) { perror("calloc"); return 1; }
    printf("[CALLOC] ");
    for (int i = 0; i < 5; i++)
        printf("%d ", zeros[i]);  // tous à 0 garanti
    printf("\n");
    free(zeros);

    // --- Allouer une chaîne ---
    char *nom = malloc(50 * sizeof(char));
    if (nom == NULL) { perror("malloc"); return 1; }
    strcpy(nom, "AngeVirus - Shadow Bytes");
    printf("[STRING] %s  (adresse=%p)\n", nom, (void*)nom);
    free(nom);

    // --- realloc : agrandir ---
    int *buf = malloc(3 * sizeof(int));
    buf[0] = 1; buf[1] = 2; buf[2] = 3;
    buf = realloc(buf, 6 * sizeof(int));  // agrandir à 6
    if (buf == NULL) { perror("realloc"); return 1; }
    buf[3] = 4; buf[4] = 5; buf[5] = 6;
    printf("[REALLOC] ");
    for (int i = 0; i < 6; i++) printf("%d ", buf[i]);
    printf("\n");
    free(buf);

    printf("\nTout libéré proprement.\n");
    return 0;
}
```

```bash
gcc -o mp5 mp5_malloc.c
./mp5
```

---

## 3.4 Mini-projet 6 — Les erreurs classiques (à NE PAS faire en prod)

```c
// mp6_erreurs_memoire.c
// Ce fichier DOCUMENTE les erreurs — compiler et tester avec valgrind
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// ERREUR 1 : fuite mémoire (memory leak)
void fuite_memoire() {
    int *p = malloc(sizeof(int));
    *p = 42;
    printf("[LEAK] alloué mais jamais libéré (fuite mémoire)\n");
    // free(p);  ← oublié
}

// ERREUR 2 : buffer overflow heap
void overflow_heap() {
    char *buf = malloc(8);
    printf("[OVERFLOW] écriture de 20 octets dans un buffer de 8\n");
    strcpy(buf, "AAAAAAAAAAAAAAAAAAA");  // 19 chars + \0 = overflow
    free(buf);
}

// ERREUR 3 : use-after-free
void use_after_free() {
    int *p = malloc(sizeof(int));
    *p = 99;
    free(p);
    printf("[UAF] valeur après free : %d (comportement indéfini)\n", *p);
    // *p peut valoir n'importe quoi — ou faire crasher
}

// ERREUR 4 : double free
void double_free() {
    int *p = malloc(sizeof(int));
    free(p);
    // free(p);  ← décommente pour voir le crash (double free)
    printf("[DOUBLE FREE] décommenter la 2ème ligne free() pour tester\n");
}

int main() {
    fuite_memoire();
    overflow_heap();
    use_after_free();
    double_free();
    return 0;
}
```

```bash
gcc -o mp6 mp6_erreurs_memoire.c

# Analyser avec valgrind (détecte les fuites et erreurs mémoire)
sudo apt install valgrind -y
valgrind --leak-check=full ./mp6
```

**Ce que valgrind va te montrer :**
```
LEAK SUMMARY:
   definitely lost: 4 bytes in 1 blocks    ← fuite mémoire détectée
```

> **Note sécurité :** Use-after-free et double-free sont des vulnérabilités critiques.
> En Pilier 1 (Sem 14), tu apprendras à les exploiter pour obtenir l'exécution de code.

---

# MODULE 4 — Segmentation Fault

## 4.1 Qu'est-ce qu'un Segfault ?

Un **Segmentation Fault** survient quand ton programme essaie d'accéder à une zone
mémoire qui ne lui est pas autorisée. Le kernel envoie le signal `SIGSEGV` et tue le processus.

**Les causes les plus fréquentes :**

| Cause | Exemple | Pourquoi ça crash |
|---|---|---|
| Déréférencement NULL | `int *p = NULL; *p = 1;` | Adresse 0x0 interdite |
| Buffer overflow (stack) | Écrire au-delà d'un tableau local | Écrase des données critiques |
| Buffer overflow (heap) | Écrire au-delà d'un malloc | Corrompt les métadonnées heap |
| Pointeur non initialisé | `int *p; *p = 1;` | Adresse aléatoire, probablement interdite |
| Use-after-free | Lire/écrire après free() | La mémoire a été réaffectée |
| Écriture dans le segment text | `*(void**)func = 0;` | Segment text = read-only |

---

## 4.2 Mini-projet 7 — Provoquer des Segfaults

```c
// mp7_segfaults.c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// CAS 1 : déréférencement de NULL
void cas1_null() {
    int *p = NULL;
    printf("[CAS 1] Tentative d'écriture à l'adresse NULL (0x0)\n");
    *p = 42;  // SIGSEGV
}

// CAS 2 : buffer overflow sur la stack
void cas2_stack_overflow() {
    char buf[8];
    printf("[CAS 2] Buffer de 8 octets, écriture de 200 octets...\n");
    memset(buf, 'A', 200);  // SIGSEGV (après avoir écrasé l'adresse de retour)
}

// CAS 3 : pointeur non initialisé
void cas3_uninit() {
    int *p;  // valeur aléatoire !
    printf("[CAS 3] Pointeur non initialisé : %p\n", (void*)p);
    *p = 42;  // SIGSEGV (adresse aléatoire)
}

// CAS 4 : dépassement de tableau
void cas4_oob() {
    int tab[5] = {1, 2, 3, 4, 5};
    printf("[CAS 4] Accès à tab[1000] (hors limites)\n");
    printf("tab[1000] = %d\n", tab[1000]);  // probablement SIGSEGV
}

// CAS 5 : écriture dans une chaîne littérale (segment text)
void cas5_readonly() {
    char *s = "Shadow Bytes";  // stockée dans le segment text (read-only)
    printf("[CAS 5] Écriture dans une chaîne littérale\n");
    s[0] = 'X';  // SIGSEGV — segment text = read-only
}

int main(int argc, char *argv[]) {
    if (argc < 2) {
        printf("Usage: ./mp7 [1|2|3|4|5]\n");
        printf("  1 = NULL deref\n");
        printf("  2 = stack overflow\n");
        printf("  3 = pointeur non initialisé\n");
        printf("  4 = accès hors tableau\n");
        printf("  5 = écriture read-only\n");
        return 0;
    }

    int c = atoi(argv[1]);
    if (c == 1) cas1_null();
    if (c == 2) cas2_stack_overflow();
    if (c == 3) cas3_uninit();
    if (c == 4) cas4_oob();
    if (c == 5) cas5_readonly();

    return 0;
}
```

```bash
gcc -g -o mp7 mp7_segfaults.c -fno-stack-protector
./mp7 1   # Segmentation fault
./mp7 2   # Segmentation fault
./mp7 5   # Segmentation fault
```

---

# MODULE 5 — GDB : Analyser les Crashes

## 5.1 Les registres x86 essentiels

Avant d'utiliser GDB, tu dois connaître les registres :

```
REGISTRES GÉNÉRAUX (x86 32 bits)
EAX  — Accumulateur   : résultats d'opérations, valeur de retour des fonctions
EBX  — Base           : usage général
ECX  — Compteur       : boucles, compteur
EDX  — Données        : opérations, extension de EAX

REGISTRES DE PILE
ESP  — Stack Pointer  : pointe vers le SOMMET de la stack (adresse la plus basse)
EBP  — Base Pointer   : pointe vers la BASE du stack frame courant

REGISTRE CRITIQUE
EIP  — Instruction Pointer : adresse de la PROCHAINE instruction à exécuter
       ← C'est celui qu'on veut contrôler dans un exploit !

REGISTRE D'ÉTAT
EFLAGS — Drapeaux     : résultat des comparaisons (zero flag, carry flag, etc.)

EN 64 BITS : les mêmes mais avec R au lieu de E (RAX, RBX, RSP, RBP, RIP)
```

---

## 5.2 Commandes GDB essentielles

```bash
# Lancer GDB
gdb ./programme
gdb ./programme core       # analyser un core dump

# Démarrage
run                        # (r) lancer le programme
run arg1 arg2              # lancer avec arguments
run < input.txt            # rediriger stdin

# Exécution pas à pas
next                       # (n) exécuter une ligne (sans entrer dans les fonctions)
step                       # (s) exécuter une ligne (entre dans les fonctions)
continue                   # (c) continuer jusqu'au prochain breakpoint ou crash
finish                     # terminer la fonction courante et remonter

# Breakpoints
break main                 # (b) breakpoint sur la fonction main
break fichier.c:42         # breakpoint à la ligne 42
break *0x08048420          # breakpoint à une adresse mémoire
info breakpoints           # lister les breakpoints
delete 1                   # supprimer le breakpoint numéro 1

# Inspecter l'état
info registers             # (i r) tous les registres
print variable             # (p) valeur d'une variable
print /x variable          # valeur en hexadécimal
print *pointeur            # valeur pointée
backtrace                  # (bt) pile d'appels
frame 1                    # passer au frame numéro 1

# Inspecter la mémoire
x/10x $esp                 # afficher 10 mots (4 octets) en hex à partir de ESP
x/20x 0x08048000           # afficher 20 mots à une adresse
x/s $rdi                   # afficher une chaîne à l'adresse dans RDI
x/i $eip                   # afficher l'instruction à EIP (désassemblage)

# Désassemblage
disassemble main            # désassembler la fonction main
disassemble                 # désassembler la fonction courante

# Quitter
quit                        # (q)
```

---

## 5.3 Mini-projet 8 — Analyser le CAS 1 (NULL deref) avec GDB

```bash
# Recompiler avec symboles de debug
gcc -g -o mp7_debug mp7_segfaults.c -fno-stack-protector

# Lancer GDB
gdb -q ./mp7_debug
```

**Session GDB complète :**

```
(gdb) run 1
Starting program: ./mp7_debug 1
[CAS 1] Tentative d'écriture à l'adresse NULL (0x0)

Program received signal SIGSEGV, Segmentation fault.
cas1_null () at mp7_segfaults.c:9
9           *p = 42;
```

```
(gdb) backtrace
#0  cas1_null () at mp7_segfaults.c:9
#1  0x... in main (argc=2, argv=0x...) at mp7_segfaults.c:45

→ Le crash est dans cas1_null(), appelée depuis main()
```

```
(gdb) info registers
eax   0x0   0          ← EAX = 0 (peut être le résultat d'une opération)
ebp   0x...            ← Base pointer du frame courant
esp   0x...            ← Sommet de la stack
eip   0x...            ← Adresse de l'instruction qui a crashé
```

```
(gdb) print p
$1 = (int *) 0x0       ← p = NULL = adresse 0 → interdit d'écrire là
```

```
(gdb) x/i $eip
=> 0x...: mov DWORD PTR [eax], 0x2a
   ↑ L'instruction était : écrire 42 (0x2a) à l'adresse dans EAX (= 0x0)
```

---

## 5.4 Mini-projet 9 — Analyser le CAS 2 (Buffer Overflow) avec GDB

**C'est le plus important — tu vas voir EIP écrasé avec 'A'.**

```bash
gdb -q ./mp7_debug
```

```
(gdb) run 2
Starting program: ./mp7_debug 2
[CAS 2] Buffer de 8 octets, écriture de 200 octets...

Program received signal SIGSEGV, Segmentation fault.
0x41414141 in ?? ()
```

> **MOMENT CLÉ :** `0x41 = 'A'` en ASCII.
> `0x41414141 = "AAAA"`.
> EIP a été **écrasé** par tes 'A'. Le CPU essaie d'exécuter le code
> à l'adresse 0x41414141 — cette adresse n'existe pas → SEGFAULT.

```
(gdb) info registers
eip   0x41414141   0x41414141    ← EIP = AAAA → tu contrôles le flux d'exécution !
esp   0x41414141   0x41414141    ← ESP aussi écrasé
```

```
(gdb) backtrace
#0  0x41414141 in ?? ()
Cannot access memory at address 0x41414145
```

**Ce que ça signifie pour la sécurité :**
```
buf[8]  ← 8 octets de données utilisateur
        ← ...données de stack (saved EBP, etc.)
EIP     ← si tu mets ici l'adresse d'une fonction qui t'intéresse
           → le programme va EXÉCUTER cette fonction

En Sem 4 : au lieu de 'A', tu mettras l'adresse de win()
→ Premier exploit stack overflow complet.
```

---

## 5.5 Mini-projet 10 — Programme complet d'analyse GDB

```c
// mp10_analyse.c — programme avec plusieurs fonctions à analyser
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// Fonction secrète — l'objectif d'un exploit ret2win
void win() {
    printf("*** Bravo ! Tu as redirigé l'exécution vers win() ***\n");
    printf("*** En vrai, ici ce serait : system('/bin/sh') ***\n");
}

// Fonction vulnérable
void vulnerable(char *input) {
    char buf[32];
    strcpy(buf, input);  // pas de vérification de taille → overflow possible
    printf("Tu as entré : %s\n", buf);
}

int main(int argc, char *argv[]) {
    printf("Adresse de win()       : %p\n", (void*)win);
    printf("Adresse de vulnerable(): %p\n", (void*)vulnerable);

    if (argc < 2) {
        printf("Usage: ./mp10 <input>\n");
        return 0;
    }

    vulnerable(argv[1]);
    return 0;
}
```

```bash
gcc -g -o mp10 mp10_analyse.c -fno-stack-protector -z execstack -no-pie

# Utilisation normale
./mp10 "Hello"

# Afficher les adresses
./mp10 "x"

# Dans GDB — analyser la structure
gdb -q ./mp10
```

**Session GDB d'analyse :**

```
(gdb) break vulnerable
Breakpoint 1 at 0x...: file mp10_analyse.c, line 16.

(gdb) run "AAAA"
Breakpoint 1, vulnerable (input=0x... "AAAA") at mp10_analyse.c:16

(gdb) info registers
   → voir ESP, EBP, EIP au début de la fonction

(gdb) x/20x $esp
   → voir le contenu de la stack (buf, saved EBP, return address)

(gdb) next
(gdb) next
   → avancer jusqu'au strcpy

(gdb) x/20x $esp
   → voir "AAAA" copié dans buf sur la stack

(gdb) print &buf
   → adresse de buf dans la stack

(gdb) continue
   → programme continue normalement

(gdb) quit
```

---

## Récapitulatif — Ce que tu maîtrises maintenant

```
MODULE 1 — Mémoire
  ✓ Stack : variables locales, frames, grandit vers le bas
  ✓ Heap  : malloc/free, grandit vers le haut
  ✓ Text  : code compilé, read-only
  ✓ Adresses heap (0x5555...) ≠ adresses stack (0x7fff...)

MODULE 2 — Pointeurs
  ✓ &x     = adresse de x
  ✓ *p     = valeur à l'adresse p
  ✓ p+1    = avance de sizeof(type) octets
  ✓ tab[i] = *(tab+i)  (tableau = pointeur)
  ✓ Passage par référence = passer &variable à la fonction

MODULE 3 — malloc/free
  ✓ malloc() : allouer, vérifier NULL, libérer avec free()
  ✓ calloc() : initialisé à zéro
  ✓ realloc() : redimensionner
  ✓ Erreurs : leak, overflow heap, use-after-free, double free

MODULE 4 — Segfault
  ✓ SIGSEGV = accès mémoire interdit
  ✓ 5 causes : NULL deref, stack overflow, uninit ptr, OOB, write read-only
  ✓ Sans GDB : impossible de savoir pourquoi

MODULE 5 — GDB
  ✓ EIP/RIP = adresse de la prochaine instruction (le registre clé)
  ✓ ESP/RSP = sommet de la stack
  ✓ EBP/RBP = base du frame courant
  ✓ backtrace : pile d'appels au moment du crash
  ✓ x/10x $esp : voir le contenu de la stack
  ✓ 0x41414141 dans EIP = tu contrôles le flux d'exécution → base d'un exploit
```

---

## Progression vers la Semaine 4

```
Sem 1 (maintenant)
  → Tu comprends mémoire, pointeurs, malloc, segfault, GDB
  → Tu as vu EIP écrasé avec 0x41414141

Sem 2
  → Stack frame en détail : calling convention x86, prologue/épilogue
  → Tu lis le désassemblage de tes propres programmes

Sem 3
  → Agent LLM local avec LangFuse (partie LLMOps intense)
  → Mapping C → ASM avec objdump

Sem 4
  → Buffer overflow intentionnel : tu calcules exactement combien de 'A' pour atteindre EIP
  → Tu remplaces EIP par l'adresse de win()
  → Premier exploit fonctionnel
```

---

## Ressources pour aller plus loin

| Ressource | Contenu | Niveau |
|---|---|---|
| **opensecuritytraining2.info** — "Introductory Intel x86" | Cours universitaire complet x86 | Débutant |
| **CS:APP** (Bryant & O'Hallaron) — Chapitre 3 | Machine-Level Representation | Débutant/Intermédiaire |
| **pwn.college** — "Program Misuse" + "Debugging Refresher" | Labs interactifs GDB | Débutant |
| **guyinatuxedo/nightmare** (GitHub) | Write-ups CTF ordonnés par technique | Intermédiaire |
| **pwndbg** (GitHub) | Extension GDB indispensable | Tous niveaux |
| **LiveOverflow** (YouTube) | Vidéos binary exploitation | Débutant/Intermédiaire |

---

*Shadow Bytes Red Team · UCAD · Dakar — Pilier 0, Semaine 1 — C/ASM x86*
*Formation 100% open source — 0$*
