#!/bin/bash
# Lab22 BONUS — Analyse DVRF (Damn Vulnerable Router Firmware) v0.3
# Source : https://github.com/praetorian-inc/DVRF
# Prérequis : binwalk, unsquashfs, strings, wget

set -e

DVRF_URL="https://github.com/praetorian-inc/DVRF/raw/master/Firmware/DVRF_v03.bin"
DVRF_BIN="DVRF_v03.bin"

echo "════════════════════════════════════════════════════════"
echo "  Lab22 BONUS — DVRF Real Firmware Analysis"
echo "════════════════════════════════════════════════════════"

# ── Step 0 : Téléchargement ──────────────────────────────
if [ ! -f "$DVRF_BIN" ]; then
    echo "[*] Téléchargement DVRF_v03.bin (~7 MB)..."
    wget -q --show-progress "$DVRF_URL" -O "$DVRF_BIN"
    echo "[+] Téléchargé : $(du -h $DVRF_BIN | cut -f1)"
else
    echo "[*] DVRF_v03.bin déjà présent : $(du -h $DVRF_BIN | cut -f1)"
fi

# ── Step 1 : Identification ──────────────────────────────
echo ""
echo "── Step 1 : Identification ──"
file "$DVRF_BIN"
echo ""
binwalk "$DVRF_BIN"

# ── Step 2 : Extraction ──────────────────────────────────
echo ""
echo "── Step 2 : Extraction ──"
rm -rf "_${DVRF_BIN}.extracted" dvrf-root/
binwalk -e "$DVRF_BIN" 2>/dev/null || binwalk -e --run-as=root "$DVRF_BIN"
echo "[+] Contenu extrait :"
ls "_${DVRF_BIN}.extracted/" 2>/dev/null || ls _DVRF* 2>/dev/null | head -20

# ── Step 3 : Extraction SquashFS ─────────────────────────
echo ""
echo "── Step 3 : SquashFS ──"
SQUASH=$(find "_${DVRF_BIN}.extracted" -name "*.squashfs" 2>/dev/null | head -1)
[ -z "$SQUASH" ] && SQUASH=$(find "_${DVRF_BIN}.extracted" -type f -size +100k 2>/dev/null | head -1)
echo "[*] SquashFS : $SQUASH"
unsquashfs -d dvrf-root "$SQUASH" 2>/dev/null && echo "[+] Extrait dans dvrf-root/"

# ── Step 4 : Filesystem reconnaissance ───────────────────
echo ""
echo "── Step 4 : Structure filesystem ──"
ls -la dvrf-root/ 2>/dev/null
echo ""
echo "[etc/]"
ls dvrf-root/etc/ 2>/dev/null | head -30

# ── Step 5 : Credentials ─────────────────────────────────
echo ""
echo "── Step 5 : Credentials ──"
echo "[passwd]"
cat dvrf-root/etc/passwd 2>/dev/null || echo "(absent)"
echo ""
echo "[shadow]"
cat dvrf-root/etc/shadow 2>/dev/null || echo "(absent/protégé)"
echo ""
echo "[config files contenant 'pass' ou 'key']"
grep -ri "password\|passwd\|secret\|key\s*=" dvrf-root/etc/ 2>/dev/null | head -20

# ── Step 6 : Fichiers cachés ─────────────────────────────
echo ""
echo "── Step 6 : Fichiers cachés ──"
find dvrf-root/ -name ".*" -type f 2>/dev/null | head -20

# ── Step 7 : Backdoors ───────────────────────────────────
echo ""
echo "── Step 7 : Backdoors / scripts suspects ──"
find dvrf-root/ -name "*.sh" -o -name "*.cgi" 2>/dev/null | head -30
echo ""
echo "[grep nc/netcat/telnet dans scripts]"
grep -rl "nc\b\|netcat\|telnetd\|dropbear" dvrf-root/ 2>/dev/null | head -10

# ── Step 8 : Binaires vulnérables ────────────────────────
echo ""
echo "── Step 8 : Binaires MIPSEL ──"
find dvrf-root/ -type f -name "*.cgi" -o -name "pwnable" 2>/dev/null | head -10
TARGETS=$(find dvrf-root/ -path "*/pwnable/*" -type f 2>/dev/null | head -5)
for t in $TARGETS; do
    echo ""
    echo "==> $t"
    file "$t" 2>/dev/null
    strings "$t" 2>/dev/null | grep -i "flag\|secret\|pass\|overflow\|gets\|strcpy" | head -10
done

# ── Step 9 : Strings globaux suspects ────────────────────
echo ""
echo "── Step 9 : Strings suspects (binaires MIPS) ──"
find dvrf-root/bin dvrf-root/sbin dvrf-root/usr/bin 2>/dev/null -type f | head -5 | while read b; do
    echo "==> $b"
    strings "$b" 2>/dev/null | grep -i "admin\|root\|pass\|default" | head -5
done

echo ""
echo "════════════════════════════════════════════════════════"
echo "  Analyse DVRF terminée"
echo "════════════════════════════════════════════════════════"
