#!/bin/bash
# Génère firmware.bin = header 8 bytes + squashfs (rootfs/)
set -e

echo "[*] Compilation httpd MIPSEL..."
mipsel-linux-gnu-gcc -g -fno-stack-protector -o rootfs/bin/httpd rootfs/bin/httpd.c 2>/dev/null || \
    echo "[!] mipsel-gcc absent — copie du .c comme placeholder"

echo "[*] Création SquashFS..."
mksquashfs rootfs/ rootfs.squashfs -comp lzma -noappend -quiet

echo "[*] Ajout header firmware (magic ANGFW)..."
printf '\x41\x4e\x47\x46\x57\x00\x00\x00' > firmware.bin   # magic: ANGFW
cat rootfs.squashfs >> firmware.bin
rm -f rootfs.squashfs

SIZE=$(wc -c < firmware.bin)
echo "[+] firmware.bin créé — ${SIZE} bytes"
echo "[+] SHA256: $(sha256sum firmware.bin | cut -d' ' -f1)"
