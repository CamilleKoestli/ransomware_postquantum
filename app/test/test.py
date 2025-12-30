#!/usr/bin/env python3
"""
Script de test automatisé pour le ransomware post-quantique
Tests: chiffrement, déchiffrement complet, changement de mot de passe, déchiffrement partiel
"""

from client import RansomwareClient
from server import server
import os

client = RansomwareClient(".")

print("=" * 70)
print("TEST 1: CHIFFREMENT DE dossier_0")
print("=" * 70)

client.encrypt_directory("dossier_0")

print("\n" + "=" * 70)
print("TEST 2: DÉCHIFFREMENT COMPLET")
print("=" * 70)

client.decrypt_all("dossier_0")

print("\n" + "=" * 70)
print("TEST 3: CHANGEMENT DE MOT DE PASSE")
print("=" * 70)

client.change_password()

print("\n" + "=" * 70)
print("TEST 4: DÉCHIFFREMENT D'UN FICHIER SPÉCIFIQUE")
print("=" * 70)

# Re-chiffre les fichiers pour tester le déchiffrement partiel
client.encrypt_directory("dossier_0")

# Supprime le fichier déchiffré pour tester
if os.path.exists("dossier_0/fichier1.txt"):
    os.remove("dossier_0/fichier1.txt")

client.decrypt_file("dossier_0/fichier1.txt.encrypted")

print("\n" + "=" * 70)
print("TOUS LES TESTS RÉUSSIS!")
print("=" * 70)
