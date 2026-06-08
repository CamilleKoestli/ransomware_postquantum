# Ransomware Post-Quantique

Projet académique pour le cours ICR 2026 (Industrial Cryptography)

## Auteur

Camille Koestli - HES-SO

## Description

Implémentation d'un ransomware résistant aux ordinateurs quantiques :

- **Chiffrement des fichiers** : AES-GCM 256 bits
- **Encapsulation des clés** : AES-GCM 256 bits
- **Dérivation de clés** : Argon2id
- **Génération de la Root Key** : CRYSTALS-Kyber-1024 (ML-KEM, niveau 5 NIST)
- **Génération de mots de passe** : wordlist `rockyou.txt` (8-15 caractères)

## Architecture

### Structure des fichiers

```
app/
├── src/
│   ├── config.py               # Configuration et constantes
│   ├── crypto_utils.py         # Utilitaires cryptographiques
│   ├── wordlist.py             # Génération de mots de passe
│   ├── rockyou.txt             # Wordlist pour les mots de passe
│   ├── server.py               # Module serveur (gestion des clés)
│   ├── client.py               # Module client (chiffrement/déchiffrement)
│   ├── main.py                 # Interface utilisateur interactive
│   └── requirements.txt        # Dépendances Python
└── test/
    ├── test.py                 # Tests automatisés
    └── dossier_0/              # Dossier de test (recréé automatiquement)
        ├── fichier0_1.txt
        ├── fichier0_2.txt
        └── sous_dossier/
            ├── fichier1_1.txt
            └── fichier1_2.txt
```

### Hiérarchie des clés

```
Mot de passe (8-15 chars)
       │
    Argon2id
       │
    Master Key (MK, 256 bits)
       │
       ├── encapsule ──► Root Key (RK, 256 bits)  ◄── Kyber-1024
       │                        │
       │          ┌─────────────┼─────────────┐
       │          │             │             │
       │     folder_key    file_key_A    file_key_B
       │     (256 bits)    (256 bits)    (256 bits)
       │          │
       │     fichier.key  (chiffré avec parent_key)
       │     fichier.root_key  (chiffré avec RK, pour déchiffrement individuel)
       │
    rootkey.bin  (wrapped_rk + kyber_ciphertext + sel + params Argon2)
```

### Flux de chiffrement

1. Le serveur génère un mot de passe aléatoire (8-15 chars, depuis `rockyou.txt`) et une paire de clés Kyber
2. Le client dérive la **Master Key (MK)** avec Argon2id (mot de passe + sel)
3. Le client génère la **Root Key (RK)** via encapsulation Kyber avec la clé publique du serveur
4. La RK est encapsulée avec la MK (AES-GCM) et stockée dans `rootkey.bin`
5. Pour chaque item du dossier (récursif) :
   - **Sous-dossier** : génère une `folder_key`, sauvegarde `dossier.key` (chiffré avec `parent_key`) et `dossier.root_key` (chiffré avec RK, si hors niveau racine)
   - **Fichier** : génère une `file_key`, sauvegarde `fichier.enc` (`nonce || ciphertext`), `fichier.key` (chiffré avec `parent_key`) et `fichier.root_key` (chiffré avec RK, si hors niveau racine)

### Flux de déchiffrement

**Déchiffrement complet ou d'un sous-dossier (`decrypt_all`) :**

1. Le serveur renvoie le mot de passe et les paramètres Argon2
2. Le client dérive la MK, puis désencapsule la RK depuis `rootkey.bin`
3. Déchiffrement récursif : pour chaque item, préfère `.root_key` + RK si disponible, sinon `.key` + `parent_key`. Ce mécanisme permet de déchiffrer un sous-dossier directement sans remonter toute la hiérarchie.

**Déchiffrement d'un fichier individuel (`decrypt_file`) :**

1. Le client envoie le fichier `.root_key` (ou `.key` si niveau racine) et le `kyber_ciphertext` au serveur
2. Le serveur reconstruit la RK via désencapsulation Kyber et retourne la `file_key` en clair
3. Le client déchiffre le fichier `.enc` avec la `file_key`

**Changement de mot de passe (`change_password`) :**

1. Le client génère un nouveau mot de passe et sel
2. Le serveur désencapsule la RK via Kyber, la réencapsule avec la nouvelle MK
3. `rootkey.bin` est mis à jour — les fichiers `.enc` ne sont pas rechiffrés

## Fichiers générés lors du chiffrement

### `rootkey.bin`

```json
{
  "wrapped_rk_ciphertext": "base64...",
  "wrapped_rk_nonce": "base64...",
  "kyber_ciphertext": "base64...",
  "salt": "base64...",
  "argon2_params": {
    "time_cost": 2,
    "memory_cost": 65536,
    "parallelism": 4,
    "hash_len": 32
  }
}
```

### `fichier.enc`

Fichier binaire : `nonce (12 octets) || ciphertext_with_tag`

### `fichier.key` / `dossier.key`

```json
{
  "ciphertext": "base64...",
  "nonce": "base64..."
}
```

Clé du fichier/dossier chiffrée avec la clé parente (`parent_key`).

### `fichier.root_key` / `dossier.root_key`

Même format que `.key`, mais la clé est chiffrée avec la Root Key. Créé uniquement pour les items hors du niveau racine du dossier chiffré. Permet le déchiffrement individuel via le serveur.

## Installation

```bash
# Créer et activer l'environnement virtuel
python3 -m venv venv
source venv/bin/activate        # Linux/Mac
# venv\Scripts\activate         # Windows

# Installer les dépendances
pip install --upgrade pip
pip install -r app/src/requirements.txt
```

### Télécharger la wordlist `rockyou.txt`

```bash
cd app/src
wget https://github.com/brannondorsey/naive-hashcat/releases/download/data/rockyou.txt
```

## Utilisation

```bash
source venv/bin/activate
cd app/src
python main.py
```

Menu disponible :

```
1. Chiffrer un dossier
2. Déchiffrer un dossier ou sous-dossier
3. Déchiffrer un fichier
4. Changer le mot de passe
5. Quitter
```

## Paramètres cryptographiques

| Paramètre | Valeur |
|-----------|--------|
| Taille des clés (MK, RK, file_key, folder_key) | 256 bits |
| Nonce AES-GCM | 96 bits (12 octets) |
| Tag AES-GCM | 128 bits (16 octets) |
| Salt Argon2id | 128 bits (16 octets) |
| Argon2id time_cost | 2 |
| Argon2id memory_cost | 65536 KB (64 MB) |
| Argon2id parallelism | 4 |
| Kyber | ML-KEM-1024 (niveau 5 NIST) |
| Niveau de sécurité post-quantique | 128 bits |

## Tests

Le script de test se remet automatiquement dans un état propre avant chaque exécution (supprime les artefacts de chiffrement et recrée les fichiers plaintext).

```bash
# Depuis la racine du projet
source venv/bin/activate
python app/test/test.py
```

| Test | Description |
|------|-------------|
| Test 1 | Chiffrement récursif hiérarchique de `dossier_0` (4 fichiers) |
| Test 2 | Déchiffrement complet via `decrypt_all()` |
| Test 3 | Changement de mot de passe sans rechiffrement |
| Test 4 | Rechiffrement + déchiffrement d'un seul fichier via `decrypt_file()` |
