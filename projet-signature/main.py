#!/usr/bin/env python3
"""
AI-Assisted Embedded Hardware Attack Framework
Ngagne Demba Dia · AngeVirusLab · Master Sécurité des Systèmes Embarqués · UCAD · 2026

Usage:
    python main.py --firmware firmware.bin
    python main.py --firmware firmware.bin --skip-llm
    python main.py --firmware firmware.bin --skip-extract --json
"""
import argparse
import json
import sys
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.rule import Rule

from modules.m1_extractor import extract_firmware
from modules.m2_detector import detect_architecture
from modules.m3_analyzer import analyze_filesystem
from modules.m4_llm import explain_with_llm

console = Console()


def print_banner():
    console.print(Rule("[bold red]AI-Assisted Embedded Hardware Attack Framework[/bold red]"))
    console.print("[dim]Ngagne Demba Dia · AngeVirusLab · Master Sécurité des Systèmes Embarqués · UCAD · 2026[/dim]\n")


def main():
    parser = argparse.ArgumentParser(description="AI-Assisted Embedded Hardware Attack Framework")
    parser.add_argument("--firmware", required=True, help="Chemin vers le firmware binaire")
    parser.add_argument("--skip-extract", action="store_true",
                        help="Sauter l'extraction (utilise squashfs-root/ existant)")
    parser.add_argument("--skip-llm", action="store_true", help="Sauter l'analyse LLM")
    parser.add_argument("--json", action="store_true", dest="json_out", help="Sortie JSON brute")
    args = parser.parse_args()

    print_banner()

    # ── Module 1 — Extraction ──────────────────────────────────────────────
    console.print("[bold cyan]▶ Module 1 — Firmware Extraction[/bold cyan]")

    if args.skip_extract:
        root_guess = str(Path(args.firmware).parent / "squashfs-root")
        extraction = {
            "firmware": args.firmware,
            "size": Path(args.firmware).stat().st_size if Path(args.firmware).exists() else 0,
            "components": [],
            "binwalk_output": "",
            "extracted_dir": None,
            "squashfs_root": root_guess,
        }
        console.print(f"[yellow]  Skip — utilisation de {root_guess}[/yellow]")
    else:
        try:
            extraction = extract_firmware(args.firmware)
        except FileNotFoundError as e:
            console.print(f"[red]  ✗ {e}[/red]")
            sys.exit(1)

        console.print(f"[green]  ✓ Firmware : {extraction['size']:,} bytes[/green]")
        for comp in extraction.get("components", []):
            console.print(f"  [dim]{comp}[/dim]")

        if extraction.get("squashfs_root"):
            console.print(f"[green]  ✓ Filesystem extrait : {extraction['squashfs_root']}[/green]")
        else:
            console.print("[red]  ✗ Extraction SquashFS échouée — vérifier binwalk/unsquashfs[/red]")
            sys.exit(1)

    # ── Module 2 — Architecture Detection ─────────────────────────────────
    console.print("\n[bold cyan]▶ Module 2 — Architecture Detection[/bold cyan]")
    arch = detect_architecture(extraction["squashfs_root"])

    console.print(f"[green]  ✓ Architecture dominante : [bold]{arch['dominant_arch']}[/bold][/green]")
    for a, count in arch.get("arch_distribution", {}).items():
        console.print(f"  [dim]{a} : {count} binaire(s)[/dim]")
    console.print(f"  [dim]Binaires analysés : {arch['binaries_analyzed']}[/dim]")

    # ── Module 3 — Vulnerability Analysis ─────────────────────────────────
    console.print("\n[bold cyan]▶ Module 3 — Vulnerability Analysis[/bold cyan]")
    vuln = analyze_filesystem(extraction["squashfs_root"])
    vuln["firmware_size"] = extraction.get("size", 0)

    table = Table(title="Rapport de vulnérabilités", border_style="red")
    table.add_column("Catégorie", style="bold")
    table.add_column("Trouvés", justify="right", style="red")
    table.add_row("Credentials hardcodés", str(len(vuln["credentials"])))
    table.add_row("Fichiers cachés", str(len(vuln["hidden_files"])))
    table.add_row("Binaires avec fonctions dangereuses", str(len(vuln["dangerous_functions"])))
    table.add_row("Backdoors", str(len(vuln["backdoors"])))
    table.add_row("Binaires sans protections stack", str(len(vuln["unprotected_binaries"])))
    console.print(table)

    if vuln["credentials"]:
        console.print("\n  [bold red]Credentials :[/bold red]")
        for c in vuln["credentials"][:5]:
            console.print(f"    [dim]{c['file']}[/dim] → [yellow]{c['match']}[/yellow]")

    if vuln["backdoors"]:
        console.print("\n  [bold red]Backdoors :[/bold red]")
        for b in vuln["backdoors"][:5]:
            console.print(f"    [dim]{b['binary']}[/dim] → [yellow]{', '.join(b['patterns'])}[/yellow]")

    # ── Module 4 — LLM Analysis ───────────────────────────────────────────
    if not args.skip_llm:
        console.print("\n[bold cyan]▶ Module 4 — LLM-Assisted Analysis[/bold cyan]")
        console.print("  [dim]Connexion à Ollama (llama3.1:8b)...[/dim]")
        explanation = explain_with_llm(arch, vuln)
        console.print(Panel(explanation, title="[bold green]Analyse LLM[/bold green]", border_style="green"))

    # ── JSON output ───────────────────────────────────────────────────────
    if args.json_out:
        report = {
            "extraction": {k: v for k, v in extraction.items() if k != "binwalk_output"},
            "architecture": arch,
            "vulnerabilities": vuln,
        }
        print(json.dumps(report, indent=2, ensure_ascii=False))

    console.print(Rule("[bold green]Analyse terminée[/bold green]"))


if __name__ == "__main__":
    main()
