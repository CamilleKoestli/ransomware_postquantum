"""
Utilitaires cryptographiques pour le ransomware post-quantique
Utilise cryptography pour AES-GCM, argon2 pour la dérivation de clés
"""

import os
import secrets
from typing import Tuple

from argon2 import PasswordHasher
from argon2.low_level import Type, hash_secret_raw
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from pqcrypto.kem.ml_kem_1024 import generate_keypair, encrypt, decrypt

import config


def generate_random_key(size: int = config.KEY_SIZE) -> bytes:
    """
    Génère une clé aléatoire sécurisée

    Args:
        size: Taille de la clé en octets (défaut: 32 pour 256 bits)

    Returns:
        Clé aléatoire de la taille spécifiée
    """
    return secrets.token_bytes(size)


def generate_random_salt(size: int = config.ARGON2_SALT_LEN) -> bytes:
    """
    Génère un salt aléatoire pour Argon2

    Args:
        size: Taille du salt en octets

    Returns:
        Salt aléatoire
    """
    return secrets.token_bytes(size)


def derive_key_argon2(
    password: str,
    salt: bytes,
    time_cost: int = config.ARGON2_TIME_COST,
    memory_cost: int = config.ARGON2_MEMORY_COST,
    parallelism: int = config.ARGON2_PARALLELISM,
    hash_len: int = config.ARGON2_HASH_LEN
) -> bytes:
    """
    Dérive une clé à partir d'un mot de passe avec Argon2id

    Args:
        password: Mot de passe en clair
        salt: Salt pour la dérivation
        time_cost: Nombre d'itérations
        memory_cost: Mémoire utilisée en KB
        parallelism: Nombre de threads parallèles
        hash_len: Longueur du hash en octets

    Returns:
        Clé dérivée
    """
    password_bytes = password.encode('utf-8')

    key = hash_secret_raw(
        secret=password_bytes,
        salt=salt,
        time_cost=time_cost,
        memory_cost=memory_cost,
        parallelism=parallelism,
        hash_len=hash_len,
        type=Type.ID  # Argon2id (recommandé)
    )

    return key


def encrypt_aes_gcm(data: bytes, key: bytes) -> Tuple[bytes, bytes, bytes]:
    """
    Chiffre des données avec AES-GCM 256 bits

    Args:
        data: Données à chiffrer
        key: Clé de chiffrement (32 octets)

    Returns:
        Tuple (ciphertext, nonce, tag)
        Le tag est inclus dans le ciphertext retourné par AESGCM
    """
    if len(key) != config.KEY_SIZE:
        raise ValueError(f"La clé doit faire {config.KEY_SIZE} octets")

    # Génère un nonce aléatoire de 96 bits (12 octets) - recommandé pour GCM
    nonce = secrets.token_bytes(12)

    # Crée l'objet AESGCM
    aesgcm = AESGCM(key)

    # Chiffre (le tag est automatiquement ajouté à la fin du ciphertext)
    ciphertext = aesgcm.encrypt(nonce, data, None)

    # Extrait le tag (16 derniers octets)
    tag = ciphertext[-16:]
    ciphertext_without_tag = ciphertext[:-16]

    return ciphertext_without_tag, nonce, tag


def decrypt_aes_gcm(ciphertext: bytes, key: bytes, nonce: bytes, tag: bytes) -> bytes:
    """
    Déchiffre des données chiffrées avec AES-GCM 256 bits

    Args:
        ciphertext: Données chiffrées (sans le tag)
        key: Clé de déchiffrement (32 octets)
        nonce: Nonce utilisé pour le chiffrement (12 octets)
        tag: Tag d'authentification (16 octets)

    Returns:
        Données déchiffrées

    Raises:
        cryptography.exceptions.InvalidTag si le tag est invalide
    """
    if len(key) != config.KEY_SIZE:
        raise ValueError(f"La clé doit faire {config.KEY_SIZE} octets")

    # Crée l'objet AESGCM
    aesgcm = AESGCM(key)

    # Reconstruit le ciphertext complet avec le tag
    full_ciphertext = ciphertext + tag

    # Déchiffre et vérifie le tag
    plaintext = aesgcm.decrypt(nonce, full_ciphertext, None)

    return plaintext


def wrap_key_aes_gcm(key_to_wrap: bytes, wrapping_key: bytes) -> Tuple[bytes, bytes, bytes]:
    """
    Encapsule une clé avec AES-GCM 256 bits

    Args:
        key_to_wrap: Clé à encapsuler
        wrapping_key: Clé d'encapsulation (32 octets)

    Returns:
        Tuple (ciphertext, nonce, tag)
    """
    if len(wrapping_key) != config.KEY_SIZE:
        raise ValueError(f"La clé d'encapsulation doit faire {config.KEY_SIZE} octets")

    # Utilise la fonction encrypt_aes_gcm existante
    return encrypt_aes_gcm(key_to_wrap, wrapping_key)


def unwrap_key_aes_gcm(ciphertext: bytes, wrapping_key: bytes, nonce: bytes, tag: bytes) -> bytes:
    """
    Désencapsule une clé avec AES-GCM 256 bits

    Args:
        ciphertext: Clé encapsulée
        wrapping_key: Clé de désencapsulation (32 octets)
        nonce: Nonce utilisé pour l'encapsulation (12 octets)
        tag: Tag d'authentification (16 octets)

    Returns:
        Clé désencapsulée

    Raises:
        cryptography.exceptions.InvalidTag si le tag est invalide
    """
    if len(wrapping_key) != config.KEY_SIZE:
        raise ValueError(f"La clé de désencapsulation doit faire {config.KEY_SIZE} octets")

    # Utilise la fonction decrypt_aes_gcm existante
    return decrypt_aes_gcm(ciphertext, wrapping_key, nonce, tag)


def generate_kyber_keypair() -> Tuple[bytes, bytes]:
    """
    Génère une paire de clés CRYSTALS-Kyber-1024

    Returns:
        Tuple (public_key, secret_key)
        - public_key: Clé publique Kyber (utilisée pour l'encapsulation)
        - secret_key: Clé secrète Kyber (utilisée pour la désencapsulation)
    """
    public_key, secret_key = generate_keypair()
    return public_key, secret_key


def kyber_encapsulate(public_key: bytes) -> Tuple[bytes, bytes]:
    """
    Encapsule un secret partagé avec CRYSTALS-Kyber-1024

    Args:
        public_key: Clé publique Kyber

    Returns:
        Tuple (ciphertext, shared_secret)
        - ciphertext: Ciphertext Kyber (à transmettre pour la désencapsulation)
        - shared_secret: Secret partagé de 32 octets (Root Key)
    """
    ciphertext, shared_secret = encrypt(public_key)

    # Vérifie que le secret partagé fait bien 32 octets (256 bits)
    if len(shared_secret) != config.KEY_SIZE:
        raise ValueError(f"Le secret partagé Kyber doit faire {config.KEY_SIZE} octets, obtenu: {len(shared_secret)}")

    return ciphertext, shared_secret


def kyber_decapsulate(secret_key: bytes, ciphertext: bytes) -> bytes:
    """
    Désencapsule un secret partagé avec CRYSTALS-Kyber-1024

    Args:
        secret_key: Clé secrète Kyber
        ciphertext: Ciphertext Kyber

    Returns:
        Secret partagé de 32 octets (Root Key)

    Raises:
        ValueError si la désencapsulation échoue
    """
    shared_secret = decrypt(secret_key, ciphertext)

    # Vérifie que le secret partagé fait bien 32 octets (256 bits)
    if len(shared_secret) != config.KEY_SIZE:
        raise ValueError(f"Le secret partagé Kyber doit faire {config.KEY_SIZE} octets, obtenu: {len(shared_secret)}")

    return shared_secret


# Fonction obsolète - la Root Key est maintenant générée via Kyber
# def generate_root_key() -> bytes:
#     """
#     [OBSOLÈTE] Génère une Root Key (RK) de 256 bits
#
#     Note: Cette fonction est obsolète. Utilisez kyber_encapsulate() à la place.
#     La Root Key est maintenant générée via CRYSTALS-Kyber-1024.
#
#     Returns:
#         Root Key de 32 octets
#     """
#     return generate_random_key(config.KEY_SIZE)
