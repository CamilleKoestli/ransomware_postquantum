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

## Architecture

### Structure des fichiers

```
app/
├── config.py           # Configuration et constantes
├── crypto_utils.py     # Utilitaires cryptographiques
├── wordlist.py         # Génération de mots de passe
├── server.py           # Module serveur (gestion des clés)
├── client.py           # Module client (chiffrement/déchiffrement)
├── main.py             # Interface utilisateur interactive
├── test.py             # Tests automatisés de base
├── test_advanced.py    # Tests avancés
└── requirements.txt    # Dépendances Python
```

### Architecture cryptographique

```
┌─────────────────────────────────────────────────────────────┐
│                         SERVEUR                             │
│  - Génère le mot de passe aléatoire                        │
│  - Génère la paire de clés Kyber-1024                     │
│  - Gère les demandes de déchiffrement                      │
│  - Stocke la clé de secours (backdoor)                     │
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

1. Le serveur génère un mot de passe aléatoire (ex: "pomme-soleil-chat-bleu")
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
6. Mode urgence (backdoor)
7. Quitter

### Tests automatisés

```bash
# Activer l'environnement virtuel
source venv/bin/activate

# Aller dans le répertoire des tests
cd app/test

# Tests de base (chiffrement + déchiffrement)
python test.py

# Tests avancés (changement de mot de passe, déchiffrement partiel, mode urgence)
python test_advanced.py
```

## Fonctionnalités

### 1. Chiffrement de dossiers

Chiffre récursivement tous les fichiers d'un dossier :

- Génère une clé unique par fichier
- Crée des fichiers `.encrypted` et `.meta`
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

### 5. Mode urgence (backdoor)

Déchiffre tous les fichiers en cas de problème :

- Utilise une clé de secours générée au démarrage
- Permet de récupérer les fichiers même si la MK/RK est corrompue
- À usage de debug/récupération uniquement

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
  "original_name": "fichier.txt",
  "wrapped_key_ciphertext": "base64...",
  "wrapped_key_nonce": "base64...",
  "wrapped_key_tag": "base64...",
  "wrapped_key_backdoor_ciphertext": "base64...",
  "wrapped_key_backdoor_nonce": "base64...",
  "wrapped_key_backdoor_tag": "base64...",
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
- ⚠️ Backdoor pour récupération (non recommandé en production)
- ⚠️ Fichiers originaux non supprimés (pour faciliter les tests)
- ⚠️ Pas de vérification d'intégrité de `rootkey.bin`
- ⚠️ Stockage des métadonnées en clair (augmente la taille des données)

## Tests

### Test 1 : Chiffrement et déchiffrement de base

```bash
# Activer le venv
$ source venv/bin/activate
$ cd app/test
$ python test.py
```

Résultat attendu :

- 4 fichiers chiffrés dans `dossier_0/`
- Création de `.encrypted` et `.meta`
- Déchiffrement réussi avec restauration complète

### Test 2 : Changement de mot de passe

```bash
$ source venv/bin/activate
$ cd app/test
$ python test_advanced.py
```

Vérifie que :

- Le nouveau mot de passe fonctionne
- La Root Key reste valide
- Le déchiffrement fonctionne toujours

### Test 3 : Déchiffrement partiel

Vérifie le déchiffrement d'un seul fichier sans le mot de passe complet.

### Test 4 : Mode urgence

Vérifie que la backdoor permet de récupérer les fichiers en cas de problème.

## Contexte académique

Ce projet a été développé dans un cadre purement éducatif pour :

- Comprendre les mécanismes des ransomwares
- Appliquer les concepts de cryptographie moderne
- Explorer la cryptographie post-quantique
- Pratiquer les bonnes pratiques de sécurité

**Ne jamais utiliser ce code à des fins malveillantes.**

