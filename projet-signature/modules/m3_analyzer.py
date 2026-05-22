"""Module 3 — Vulnerability Analysis
Analyse statique du filesystem extrait :
- Credentials hardcodés dans les fichiers de configuration
- Fichiers cachés (dotfiles)
- Fonctions dangereuses dans les binaires (strcpy, gets, sprintf...)
- Backdoors (nc, telnetd, dropbear)
- Binaires sans protections (NX, canary) via checksec
"""
import subprocess
import re
from pathlib import Path

DANGEROUS_FUNCS = ["strcpy", "gets", "sprintf", "strcat", "scanf", "system", "vsprintf", "strncpy"]

CRED_PATTERNS = [
    r"(?i)password\s*=\s*\S+",
    r"(?i)passwd\s*=\s*\S+",
    r"(?i)secret[_\-]?key\s*=\s*\S+",
    r"(?i)admin[_\-]?pass\s*=\s*\S+",
    r"(?i)default[_\-]?wifi[_\-]?pass\s*=\s*\S+",
    r"AngeVirus\{[^}]+\}",
]

BACKDOOR_PATTERNS = ["nc -lp", "nc -l", "netcat", "telnetd", "/bin/sh", "dropbear", "bind_shell"]

CONFIG_EXTS = [".conf", ".cfg", ".ini", ".json", ".xml", ".properties", ".env"]


def analyze_filesystem(root_dir: str) -> dict:
    root = Path(root_dir)

    report = {
        "credentials": [],
        "hidden_files": [],
        "dangerous_functions": [],
        "backdoors": [],
        "unprotected_binaries": [],
        "vulnerabilities": [],
    }

    # Credentials dans fichiers config
    for f in root.rglob("*"):
        if not f.is_file():
            continue
        if f.suffix.lower() in CONFIG_EXTS or f.name in ["passwd", "shadow", "httpd.conf"]:
            try:
                content = f.read_text(errors="ignore")
                for pattern in CRED_PATTERNS:
                    for match in re.findall(pattern, content):
                        report["credentials"].append({
                            "file": str(f.relative_to(root)),
                            "match": match.strip(),
                        })
            except Exception:
                pass

    # Fichiers cachés
    for f in root.rglob(".*"):
        if f.is_file():
            report["hidden_files"].append(str(f.relative_to(root)))

    # Analyse binaires
    elf_magic = b"\x7fELF"
    analyzed = 0
    for f in root.rglob("*"):
        if analyzed >= 50:
            break
        if not f.is_file():
            continue
        try:
            with open(f, "rb") as fh:
                magic = fh.read(4)
            if magic != elf_magic:
                continue
        except Exception:
            continue

        analyzed += 1

        # Fonctions dangereuses : strings + readelf -s (symboles ELF, cross-arch)
        strings_proc = subprocess.run(["strings", str(f)], capture_output=True, text=True)
        re_sym = subprocess.run(["readelf", "-s", str(f)], capture_output=True, text=True)
        combined = strings_proc.stdout + re_sym.stdout
        found_funcs = [fn for fn in DANGEROUS_FUNCS if fn in combined]
        if found_funcs:
            report["dangerous_functions"].append({
                "binary": str(f.relative_to(root)),
                "functions": found_funcs,
            })

        # Backdoors dans les strings du binaire
        found_bd = [p for p in BACKDOOR_PATTERNS if p in strings_proc.stdout]
        if found_bd:
            report["backdoors"].append({
                "binary": str(f.relative_to(root)),
                "patterns": found_bd,
            })

        # Protections stack : readelf -l (NX) + readelf -s (canary symbol)
        re_proc = subprocess.run(["readelf", "-l", str(f)], capture_output=True, text=True)
        has_nx = "GNU_STACK" in re_proc.stdout and "RWE" not in re_proc.stdout
        has_canary = "__stack_chk_fail" in re_sym.stdout or "__stack_chk_fail" in strings_proc.stdout
        if not has_canary or not has_nx:
            missing = []
            if not has_canary:
                missing.append("No canary")
            if not has_nx:
                missing.append("NX disabled")
            report["unprotected_binaries"].append({
                "binary": str(f.relative_to(root)),
                "missing": missing,
            })

    # Backdoors dans scripts
    for f in root.rglob("*.sh"):
        if not f.is_file():
            continue
        try:
            content = f.read_text(errors="ignore")
            found_bd = [p for p in BACKDOOR_PATTERNS if p in content]
            if found_bd:
                report["backdoors"].append({
                    "binary": str(f.relative_to(root)),
                    "patterns": found_bd,
                })
        except Exception:
            pass

    # Synthèse vulnérabilités
    if report["credentials"]:
        report["vulnerabilities"].append(f"Credentials hardcodés ({len(report['credentials'])} trouvés)")
    if report["hidden_files"]:
        report["vulnerabilities"].append(f"Fichiers cachés ({len(report['hidden_files'])} trouvés)")
    if report["dangerous_functions"]:
        report["vulnerabilities"].append(f"Fonctions dangereuses dans {len(report['dangerous_functions'])} binaires")
    if report["backdoors"]:
        report["vulnerabilities"].append(f"Backdoors dans {len(report['backdoors'])} fichiers")
    if report["unprotected_binaries"]:
        report["vulnerabilities"].append(f"{len(report['unprotected_binaries'])} binaires sans protections stack")

    return report
