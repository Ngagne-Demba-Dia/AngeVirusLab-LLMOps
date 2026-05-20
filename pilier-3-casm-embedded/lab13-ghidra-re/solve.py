#!/usr/bin/env python3
"""
Lab 13 — Ghidra RE Crackme
Solve : décode le XOR 0x13 pour retrouver le mot de passe,
        puis le soumet au binaire et affiche le FLAG.
"""
from pwn import *

# --- Décodage offline (émule check()) ---
encoded = [0x40, 0x7b, 0x72, 0x77, 0x7c, 0x64,
           0x51, 0x6a, 0x67, 0x76, 0x60]
password = ''.join(chr(b ^ 0x13) for b in encoded)
log.info(f"Mot de passe retrouvé : {password}")

# --- Soumission ---
p = process('./target')
p.recvuntil(b'Password : ')
p.sendline(password.encode())

output = p.recvall(timeout=2)
log.success(output.decode().strip())
