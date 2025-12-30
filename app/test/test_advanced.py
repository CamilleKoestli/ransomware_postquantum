#!/usr/bin/env python3
"""
Tests avancés: changement de mot de passe, déchiffrement partiel, mode urgence
"""

from client import RansomwareClient
from server import server
import os

client = RansomwareClient(".")

# Initialise le serveur d'abord
print("=" * 70)
print("INITIALISATION: CHIFFREMENT DE dossier_0")
print("=" * 70)

client.encrypt_directory("dossier_0")

print("\n" + "=" * 70)
print("TEST 3: CHANGEMENT DE MOT DE PASSE")
print("=" * 70)

client.change_password()

print("\n" + "=" * 70)
print("TEST 4: DÉCHIFFREMENT D'UN FICHIER SPÉCIFIQUE")
print("=" * 70)

# Supprime le fichier déchiffré pour tester
if os.path.exists("dossier_0/fichier_0.1.txt"):
    os.remove("dossier_0/fichier_0.1.txt")

client.decrypt_file("dossier_0/fichier_0.1.txt.encrypted")

print("\n" + "=" * 70)
print("TEST 5: MODE URGENCE (BACKDOOR)")
print("=" * 70)

# Supprime les fichiers déchiffrés pour tester le mode urgence
for root, dirs, files in os.walk("dossier_0"):
    for f in files:
        if not f.endswith((".encrypted", ".meta")):
            filepath = os.path.join(root, f)
            if os.path.exists(filepath):
                os.remove(filepath)
                print(f"Supprimé: {filepath}")

client.emergency_decrypt_all("dossier_0")

print("\n" + "=" * 70)
print("TOUS LES TESTS AVANCÉS RÉUSSIS!")
print("=" * 70)
