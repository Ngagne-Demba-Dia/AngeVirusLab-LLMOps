"""Module 2 — Architecture Detection
Détecte l'architecture des binaires ELF dans le filesystem extrait.
Supporte : x86-32, x86-64, ARM32, ARM64, MIPSEL, MIPS big-endian.
"""
import subprocess
from pathlib import Path

ARCH_SIGNATURES = {
    "MIPSEL": ["MIPS, MIPS32", "MIPS LSB", "mipsel"],
    "MIPS-BE": ["MIPS MSB", "MIPS, MIPS32 rel2", "mipseb"],
    "ARM32": ["ARM, EABI", "ARM32", "ARM, version"],
    "ARM64": ["ARM aarch64", "AArch64"],
    "x86-64": ["x86-64", "AMD x86-64"],
    "x86-32": ["Intel 80386", "i386"],
}

ELF_MAGIC = b"\x7fELF"


def _is_elf(path: Path) -> bool:
    try:
        with open(path, "rb") as f:
            return f.read(4) == ELF_MAGIC
    except Exception:
        return False


def detect_architecture(root_path: str) -> dict:
    root = Path(root_path)
    candidates = []

    if root.is_file():
        candidates = [root]
    else:
        # Cherche dans les dossiers système classiques
        for d in ["bin", "sbin", "usr/bin", "usr/sbin", "lib", "pwnable"]:
            candidates.extend((root / d).glob("*") if (root / d).exists() else [])
        # Fallback global
        if not candidates:
            candidates = [p for p in root.rglob("*") if p.is_file()]

    candidates = [p for p in candidates if p.is_file() and _is_elf(p)][:30]

    arch_counts: dict[str, int] = {}
    binary_details = []

    for binary in candidates:
        proc = subprocess.run(["file", str(binary)], capture_output=True, text=True)
        output = proc.stdout

        detected = "Unknown"
        for arch, sigs in ARCH_SIGNATURES.items():
            if any(sig in output for sig in sigs):
                detected = arch
                break

        arch_counts[detected] = arch_counts.get(detected, 0) + 1
        binary_details.append({"binary": binary.name, "arch": detected, "file_output": output.strip()})

    dominant = max(arch_counts, key=arch_counts.get) if arch_counts else "Unknown"

    return {
        "dominant_arch": dominant,
        "arch_distribution": arch_counts,
        "binaries_analyzed": len(candidates),
        "binary_details": binary_details[:10],
    }
