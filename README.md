# Ransomware Post-Quantique

Projet académique pour le cours CAA 2024-2025 (Cryptographie Appliquée Avancée)

## Auteur

Camille Koestli - HEIG-VD

## Description

Implémentation d'un système de ransomware utilisant des techniques cryptographiques modernes et post-quantiques :

- **Chiffrement des fichiers** : AES-GCM 256 bits
- **Encapsulation des clés** : AES-GCM 256 bits
- **Dérivation de clés** : Argon2id
- **Génération de clés** : CRYSTALS-Kyber-1024 (ML-KEM)
- **Génération de mots de passe** : rockyou.txt (filtrage à la volée)

## Architecture

### Structure des fichiers

```
app/
├── src/
│   ├── config.py               # Configuration et constantes
│   ├── crypto_utils.py         # Utilitaires cryptographiques
│   ├── wordlist.py             # Génération de mots de passe
│   ├── rockyou.txt             # Wordlist (à télécharger, voir Installation)
│   ├── server.py               # Module serveur (gestion des clés)
│   ├── client.py               # Module client (chiffrement/déchiffrement)
│   ├── main.py                 # Interface utilisateur interactive
│   └── requirements.txt        # Dépendances Python
└── test/
    └── test.py                 # Tests automatisés
```

### Architecture cryptographique

```
┌─────────────────────────────────────────────────────────────┐
│                         SERVEUR                             │
│  - Génère le mot de passe aléatoire                        │
│  - Génère la paire de clés Kyber-1024                     │
│  - Gère les demandes de déchiffrement                      │
└─────────────────────────────────────────────────────────────┘
                            ▲  ▼
┌─────────────────────────────────────────────────────────────┐
│                         CLIENT                              │
│  - Dérive la Master Key (MK) avec Argon2                   │
│  - Génère la Root Key (RK) avec Kyber-1024                │
│  - Chiffre/déchiffre les fichiers avec AES-GCM             │
│  - Encapsule les clés avec AES-GCM                         │
│  - Stocke les métadonnées dans des fichiers .meta         │
└─────────────────────────────────────────────────────────────┘
```

### Flux de chiffrement

1. Le serveur génère un mot de passe aléatoire depuis rockyou.txt (ex: "dragon-shadow-matrix-secret")
2. Le client dérive une Master Key (MK) à partir du mot de passe avec Argon2
3. Le serveur génère une paire de clés Kyber-1024 (publique/secrète)
4. Le client génère la Root Key (RK) via encapsulation Kyber avec la clé publique
5. La RK est encapsulée avec la MK (AES-GCM) et stockée dans `rootkey.bin`
6. Pour chaque fichier :
   - Une clé de fichier aléatoire est générée
   - Le fichier est chiffré avec AES-GCM
   - La clé de fichier est encapsulée avec la RK (AES-GCM)
   - Les métadonnées (ciphertext, nonce, tag) sont stockées dans un fichier `.meta`

### Flux de déchiffrement

**Déchiffrement complet :**

1. Le serveur envoie le mot de passe et les paramètres Argon2
2. Le client dérive la MK avec Argon2
3. Le client déchiffre la RK avec la MK
4. Tous les fichiers sont déchiffrés avec leurs clés respectives

**Déchiffrement partiel :**

1. Le client envoie la clé encapsulée du fichier au serveur
2. Le serveur désencapsule la clé avec la RK
3. Le client déchiffre uniquement ce fichier

## Installation

### Avec environnement virtuel (recommandé)

```bash
# Créer l'environnement virtuel
python3 -m venv venv

# Activer l'environnement virtuel
# Sur Linux/Mac:
source venv/bin/activate
# Sur Windows:
# venv\Scripts\activate

# Installer les dépendances
pip install --upgrade pip
pip install -r app/src/requirements.txt

# Pour désactiver l'environnement virtuel quand vous avez terminé:
deactivate
```

### Télécharger la wordlist rockyou.txt

Le projet utilise la wordlist rockyou.txt pour générer des mots de passe. Téléchargez-la et placez-la dans `app/src/` :

```bash
# Télécharger rockyou.txt
cd app/src
wget https://github.com/brannondorsey/naive-hashcat/releases/download/data/rockyou.txt

# Ou avec curl
curl -L -o rockyou.txt https://github.com/brannondorsey/naive-hashcat/releases/download/data/rockyou.txt
```

**Note:** Le fichier rockyou.txt fait ~134 MB. Le code filtre automatiquement les mots (4-10 caractères, alphanumériques) lors du chargement.

### Installation globale (non recommandé)

```bash
# Installer les dépendances directement sur le système
pip install -r app/src/requirements.txt
```

## Utilisation

**Important:** N'oubliez pas d'activer l'environnement virtuel avant d'exécuter les scripts :
```bash
source venv/bin/activate  # Linux/Mac
# ou venv\Scripts\activate sur Windows
```

### Interface interactive

```bash
cd app/src
python main.py
```

Menu disponible :

1. Chiffrer un dossier
2. Déchiffrer tout
3. Déchiffrer un fichier spécifique
4. Déchiffrer un dossier spécifique
5. Changer le mot de passe
6. Quitter

### Tests automatisés

```bash
# Activer l'environnement virtuel
source venv/bin/activate

# Aller dans le répertoire des tests
cd app/test

# Lancer tous les tests
python test.py
```

## Fonctionnalités

### 1. Chiffrement de dossiers

Chiffre récursivement tous les fichiers d'un dossier :

- Génère une clé unique par fichier
- Écrase le fichier original avec le contenu chiffré (garde le même nom)
- Crée un fichier `.meta` avec les métadonnées de chiffrement
- Ignore les fichiers Python et les fichiers déjà chiffrés

### 2. Déchiffrement complet

Déchiffre tous les fichiers avec le mot de passe du serveur :

- Récupère le mot de passe et les paramètres Argon2
- Dérive la Master Key
- Déchiffre la Root Key
- Restaure tous les fichiers

### 3. Déchiffrement partiel

Déchiffre un fichier ou un dossier spécifique :

- Demande au serveur de désencapsuler la clé du fichier
- Ne nécessite pas le mot de passe complet

### 4. Changement de mot de passe

Permet de changer le mot de passe sans re-chiffrer tous les fichiers :

- Génère un nouveau mot de passe aléatoire
- Re-encapsule la Root Key avec la nouvelle Master Key
- Met à jour `rootkey.bin`

## Fichiers générés

### rootkey.bin

Contient la Root Key encapsulée et les paramètres Argon2 :

```json
{
  "wrapped_rk_ciphertext": "base64...",
  "wrapped_rk_nonce": "base64...",
  "wrapped_rk_tag": "base64...",
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

### fichier.meta

Contient les métadonnées de chiffrement pour chaque fichier :

```json
{
  "wrapped_key_ciphertext": "base64...",
  "wrapped_key_nonce": "base64...",
  "wrapped_key_tag": "base64...",
  "nonce": "base64...",
  "tag": "base64..."
}
```

## Paramètres cryptographiques

### Tailles de clés

- Clé de fichier : 256 bits (32 octets)
- Master Key (MK) : 256 bits (32 octets)
- Root Key (RK) : 256 bits (32 octets)

### Paramètres Argon2

```python
time_cost = 2          # Itérations
memory_cost = 65536    # 64 MB
parallelism = 4        # Threads
hash_len = 32          # 256 bits
```

### AES-GCM

- Taille de clé : 256 bits
- Nonce : 96 bits (12 octets)
- Tag : 128 bits (16 octets)

## Sécurité

### Points forts

- ✅ Utilisation d'algorithmes standards et éprouvés (AES-GCM, Argon2, Kyber)
- ✅ Clés de 256 bits partout (niveau de sécurité : 128 bits post-quantique)
- ✅ Argon2id pour la dérivation de clés (résistant au GPU/ASIC)
- ✅ CRYSTALS-Kyber-1024 pour la génération de la Root Key (post-quantique)
- ✅ AES-GCM pour le chiffrement et l'encapsulation (AEAD)
- ✅ Génération de clés avec `secrets` (CSPRNG)
- ✅ Clé unique par fichier (isolation)

### Limitations (contexte éducatif)

- ⚠️ Communication client-serveur simulée localement (pas de réseau)
- ⚠️ Pas de vérification d'intégrité de `rootkey.bin`
- ⚠️ Métadonnées stockées en JSON/base64 (format lisible, augmente la taille des données)

## Tests

Pour lancer tous les tests :

```bash
# Activer le venv
$ source venv/bin/activate
$ cd app/test
$ python test.py
```

Le script de test exécute automatiquement :

**Test 1 : Chiffrement de dossier**
- Chiffre tous les fichiers de `dossier_0/`
- Écrase chaque fichier avec son contenu chiffré
- Crée les fichiers `.meta` correspondants

**Test 2 : Déchiffrement complet**
- Récupère le mot de passe du serveur
- Déchiffre tous les fichiers
- Restaure les fichiers originaux

**Test 3 : Changement de mot de passe**
- Génère un nouveau mot de passe
- Re-encapsule la Root Key
- Vérifie que la nouvelle clé fonctionne

**Test 4 : Déchiffrement partiel**
- Déchiffre un seul fichier spécifique
- Utilise la désencapsulation côté serveur

## Contexte académique

Ce projet a été développé dans un cadre purement éducatif pour :

- Comprendre les mécanismes des ransomwares
- Appliquer les concepts de cryptographie moderne
- Explorer la cryptographie post-quantique
- Pratiquer les bonnes pratiques de sécurité

**Ne jamais utiliser ce code à des fins malveillantes.**

