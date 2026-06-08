#!/usr/bin/env python3
"""
Tests: chiffrement, déchiffrement complet, changement de mot de passe, déchiffrement fichier/dossier spécifique
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from client import RansomwareClient

client = RansomwareClient(".")

print("-" * 70)
print("TEST 1: CHIFFREMENT DE dossier_0")

client.encrypt_directory("dossier_0")

print("\n" + "-" * 70)
print("TEST 2: DÉCHIFFREMENT COMPLET")

client.decrypt_all("dossier_0")

print("\n" + "-" * 70)
print("TEST 3: CHANGEMENT DE MOT DE PASSE")

client.change_password()

print("\n" + "-" * 70)
print("TEST 4: DÉCHIFFREMENT D'UN FICHIER")

# Rechiffre le dossier
client.encrypt_directory("dossier_0")

# Déchiffre un seul fichier
client.decrypt_file("dossier_0/fichier2.txt")

print("\n" + "-" * 70)
print("TOUS LES TESTS OK")
