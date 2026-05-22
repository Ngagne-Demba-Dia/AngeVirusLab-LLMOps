"""Module 1 — Firmware Extraction
Utilise binwalk pour identifier et extraire les composants du firmware.
Supporte SquashFS, LZMA, gzip, headers custom (ANGFW, TRX, BIN).
"""
import subprocess
from pathlib import Path


def extract_firmware(firmware_path: str) -> dict:
    firmware = Path(firmware_path)
    if not firmware.exists():
        raise FileNotFoundError(f"Firmware non trouvé : {firmware_path}")

    result = {
        "firmware": str(firmware),
        "size": firmware.stat().st_size,
        "binwalk_output": "",
        "components": [],
        "extracted_dir": None,
        "squashfs_root": None,
    }

    # Identification
    proc = subprocess.run(["binwalk", str(firmware)], capture_output=True, text=True)
    result["binwalk_output"] = proc.stdout
    for line in proc.stdout.splitlines():
        if line and line[0].isdigit():
            result["components"].append(line.strip())

    # Extraction
    subprocess.run(
        ["binwalk", "-e", str(firmware)],
        capture_output=True, text=True,
        cwd=str(firmware.parent)
    )

    extracted = firmware.parent / f"_{firmware.name}.extracted"
    if extracted.exists():
        result["extracted_dir"] = str(extracted)

        squashfs_files = list(extracted.glob("*.squashfs"))
        if squashfs_files:
            squashfs = squashfs_files[0]
            root_dir = firmware.parent / "squashfs-root"
            if not root_dir.exists():
                subprocess.run(
                    ["unsquashfs", "-d", str(root_dir), str(squashfs)],
                    capture_output=True
                )
            if root_dir.exists():
                result["squashfs_root"] = str(root_dir)
        else:
            # Cherche un dossier squashfs-root déjà présent
            existing = firmware.parent / "squashfs-root"
            if existing.exists():
                result["squashfs_root"] = str(existing)

    return result
