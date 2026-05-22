#!/bin/bash
# Lab22 — Analyse firmware IoT step by step

echo "════════════════════════════════════════"
echo "  Lab22 — Firmware IoT Analysis"
echo "════════════════════════════════════════"

echo ""
echo "── Step 1 : Identification (file + binwalk) ──"
file firmware.bin
binwalk firmware.bin

echo ""
echo "── Step 2 : Extraction ──"
binwalk -e --run-as=root firmware.bin 2>/dev/null || binwalk -e firmware.bin
ls _firmware.bin.extracted/ 2>/dev/null || ls _firmware.bin.extracted* 2>/dev/null

echo ""
echo "── Step 3 : Montage SquashFS ──"
SQUASH=$(find _firmware.bin.extracted -name "*.squashfs" 2>/dev/null | head -1)
[ -z "$SQUASH" ] && SQUASH=$(find _firmware.bin.extracted -type f 2>/dev/null | head -1)
unsquashfs -d squashfs-root "$SQUASH" 2>/dev/null && echo "[+] Extrait dans squashfs-root/"

echo ""
echo "── Step 4 : Reconnaissance ──"
echo "[passwd]"
cat squashfs-root/etc/passwd 2>/dev/null

echo ""
echo "[config files]"
find squashfs-root/ -name "*.conf" -exec echo "==> {}" \; -exec cat {} \; 2>/dev/null

echo ""
echo "── Step 5 : Recherche flags & secrets ──"
echo "[fichiers cachés]"
find squashfs-root/ -name ".*" -type f 2>/dev/null -exec cat {} \;

echo ""
echo "[strings dans binaires]"
strings squashfs-root/bin/httpd 2>/dev/null | grep -i "angevirus\|flag\|pass\|secret\|key"

echo ""
echo "[grep récursif 'AngeVirus']"
grep -r "AngeVirus" squashfs-root/ 2>/dev/null

echo ""
echo "════════════════════════════════════════"
echo "  Analyse terminée"
echo "════════════════════════════════════════"
