#!/usr/bin/env python3
"""
Tests: chiffrement, déchiffrement complet, changement de mot de passe, déchiffrement fichier/dossier spécifique
"""

import sys
import shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from client import RansomwareClient

TEST_DIR = Path(__file__).parent
DOSSIER = TEST_DIR / "dossier_0"

# Contenu initial des fichiers de test
INITIAL_FILES = {
    DOSSIER / "fichier0_1.txt": "Contenu fichier 0.1",
    DOSSIER / "fichier0_2.txt": "Contenu fichier 0.2",
    DOSSIER / "sous_dossier" / "fichier1_1.txt": "Contenu fichier 1.1",
    DOSSIER / "sous_dossier" / "fichier1_2.txt": "Contenu fichier 1.2",
}


def setup():
    """Remet dossier test à état initial."""
    # Supprime tous
    for f in DOSSIER.rglob("*.enc"):
        f.unlink()
    for f in DOSSIER.rglob("*.key"):
        f.unlink()
    for f in DOSSIER.rglob("*.root_key"):
        f.unlink()
    rootkey = TEST_DIR / "rootkey.bin"
    if rootkey.exists():
        rootkey.unlink()

    # Recrée fichiers plaintext
    for path, content in INITIAL_FILES.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)


setup()

client = RansomwareClient(str(TEST_DIR))

print("-" * 70)
print("TEST 1: CHIFFREMENT DE dossier_0")

client.encrypt_directory(str(DOSSIER))

print("\n" + "-" * 70)
print("TEST 2: DÉCHIFFREMENT COMPLET")

client.decrypt_all(str(DOSSIER))

print("\n" + "-" * 70)
print("TEST 3: CHANGEMENT DE MOT DE PASSE")

client.change_password()

print("\n" + "-" * 70)
print("TEST 4: DÉCHIFFREMENT D'UN FICHIER")

# Rechiffre le dossier
client.encrypt_directory(str(DOSSIER))

# Déchiffre un seul fichier (dans sous_dossier → utilise .root_key)
client.decrypt_file(str(DOSSIER / "sous_dossier" / "fichier1_1.txt"))

print("\n" + "-" * 70)
print("TOUS LES TESTS OK")
