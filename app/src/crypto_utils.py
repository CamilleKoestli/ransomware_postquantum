"""
Module utilitaire pour les opérations cryptographiques
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
    Génère clé aléatoire

    Args:
        size: Taille clé de 32

    Returns:
        Clé aléatoire
    """
    return secrets.token_bytes(size)


def generate_random_salt(size: int = config.ARGON2_SALT_LEN) -> bytes:
    """
    Génère salt aléatoire

    Args:
        size: Taille sel

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
    Dérive clé à partir d'un mot de passe

    Args:
        password: Mdp en clair
        salt: Sel
        time_cost: Nombre d'itérations
        memory_cost: Mémoire
        parallelism: Nombre threads
        hash_len: Longueur hash

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
        type=Type.ID 
    )

    return key


def encrypt_aes_gcm(data: bytes, key: bytes) -> Tuple[bytes, bytes]:
    """
    Chiffre données avec AES-GCM 256 bits

    Args:
        data: Données à chiffrer
        key: Clé de chiffrement (32 octets)

    Returns:
        Tuple (ciphertext_with_tag, nonce)
    """
    if len(key) != config.KEY_SIZE:
        raise ValueError(f"La clé doit faire {config.KEY_SIZE} octets")

    nonce = secrets.token_bytes(12)
    aesgcm = AESGCM(key)
    ciphertext_with_tag = aesgcm.encrypt(nonce, data, None)
    return ciphertext_with_tag, nonce


def decrypt_aes_gcm(ciphertext_with_tag: bytes, key: bytes, nonce: bytes) -> bytes:
    """
    Déchiffre données avec AES-GCM 256 bits

    Args:
        ciphertext_with_tag: Données chiffrées avec tag en suffixe (16 octets)
        key: Clé de déchiffrement (32 octets)
        nonce: Nonce utilisé pour le chiffrement (12 octets)

    Returns:
        Données déchiffrées
    """
    if len(key) != config.KEY_SIZE:
        raise ValueError(f"La clé doit faire {config.KEY_SIZE} octets")

    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ciphertext_with_tag, None)


def wrap_key_aes_gcm(key_to_wrap: bytes, wrapping_key: bytes) -> Tuple[bytes, bytes]:
    """
    Encapsule clé avec AES-GCM 256 bits

    Args:
        key_to_wrap: Clé à encapsuler
        wrapping_key: Clé d'encapsulation (32 octets)

    Returns:
        Tuple (ciphertext_with_tag, nonce)
    """
    if len(wrapping_key) != config.KEY_SIZE:
        raise ValueError(f"[ENCAPSULATION] La clé doit faire {config.KEY_SIZE} octets")

    return encrypt_aes_gcm(key_to_wrap, wrapping_key)


def unwrap_key_aes_gcm(ciphertext_with_tag: bytes, wrapping_key: bytes, nonce: bytes) -> bytes:
    """
    Désencapsule une clé avec AES-GCM 256 bits

    Args:
        ciphertext_with_tag: Clé encapsulée avec tag en suffixe
        wrapping_key: Clé de désencapsulation (32 octets)
        nonce: Nonce utilisé pour l'encapsulation (12 octets)

    Returns:
        Clé désencapsulée
    """
    if len(wrapping_key) != config.KEY_SIZE:
        raise ValueError(f"[DESENCAPSULATION] La clé doit faire {config.KEY_SIZE} octets")

    return decrypt_aes_gcm(ciphertext_with_tag, wrapping_key, nonce)


def generate_kyber_keypair() -> Tuple[bytes, bytes]:
    """
    Génère paire de clés CRYSTALS-Kyber

    Returns:
        Tuple (public_key, secret_key)
    """
    public_key, secret_key = generate_keypair()
    return public_key, secret_key


def kyber_encapsulate(public_key: bytes) -> Tuple[bytes, bytes]:
    """
    Encapsule secret partagé avec CRYSTALS-Kyber

    Args:
        public_key: Clé publique Kyber

    Returns:
        Tuple (ciphertext, shared_secret)
    """
    ciphertext, shared_secret = encrypt(public_key)

    # Vérifie taille secret
    if len(shared_secret) != config.KEY_SIZE:
        raise ValueError(f"[ENCAPSULATION] Le secret partagé doit faire {config.KEY_SIZE} octets, obtenu: {len(shared_secret)}")

    return ciphertext, shared_secret


def kyber_decapsulate(secret_key: bytes, ciphertext: bytes) -> bytes:
    """
    Désencapsule secret partagé avec CRYSTALS-Kyber

    Args:
        secret_key: Clé secrète Kyber
        ciphertext: Ciphertext Kyber

    Returns:
        Secret partagé de 32 octets (Root Key)
    """
    shared_secret = decrypt(secret_key, ciphertext)

    # Vérifie taille secret
    if len(shared_secret) != config.KEY_SIZE:
        raise ValueError(f"[DESENCAPSULATION] Le secret partagé doit faire {config.KEY_SIZE} octets, obtenu: {len(shared_secret)}")

    return shared_secret
