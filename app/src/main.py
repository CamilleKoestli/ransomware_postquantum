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
    print("MENU PRINCIPAL")
    print("-" * 60)
    print("1. Chiffrer un dossier")
    print("2. Déchiffrer tout (avec mot de passe serveur)")
    print("3. Déchiffrer un fichier spécifique")
    print("4. Déchiffrer un dossier spécifique")
    print("5. Changer le mot de passe")
    print("6. Quitter")
    print("-" * 60)


def get_input(prompt: str, default: str = None) -> str:
    """
    Demande une entrée utilisateur avec valeur par défaut optionnelle

    Args:
        prompt: Message à afficher
        default: Valeur par défaut si l'utilisateur appuie sur Entrée

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

        choice = input("Votre choix: ").strip()

        try:
            if choice == "1":
                # Chiffrer un dossier
                print("\n--- CHIFFREMENT D'UN DOSSIER ---")
                path = get_input("Chemin du dossier à chiffrer", ".")

                if not os.path.exists(path):
                    print(f"Erreur: Le dossier '{path}' n'existe pas")
                    continue

                confirm = input(f"ATTENTION: Tous les fichiers de '{path}' seront chiffrés. Continuer? (oui/non): ")
                if confirm.lower() not in ['oui', 'o', 'yes', 'y']:
                    print("Opération annulée.")
                    continue

                client.encrypt_directory(path)

            elif choice == "2":
                # Déchiffrer tout
                print("\n--- DÉCHIFFREMENT COMPLET ---")
                path = get_input("Chemin du dossier à déchiffrer", ".")

                if not os.path.exists(path):
                    print(f"Erreur: Le dossier '{path}' n'existe pas")
                    continue

                client.decrypt_all(path)

            elif choice == "3":
                # Déchiffrer un fichier
                print("\n--- DÉCHIFFREMENT D'UN FICHIER ---")
                file_path = get_input("Chemin du fichier à déchiffrer")

                if not file_path:
                    print("Erreur: Veuillez spécifier un chemin de fichier")
                    continue

                client.decrypt_file(file_path)

            elif choice == "4":
                # Déchiffrer un dossier
                print("\n--- DÉCHIFFREMENT D'UN DOSSIER ---")
                folder_path = get_input("Chemin du dossier à déchiffrer", ".")

                if not os.path.exists(folder_path):
                    print(f"Erreur: Le dossier '{folder_path}' n'existe pas")
                    continue

                client.decrypt_folder(folder_path)

            elif choice == "5":
                # Changer mdp
                print("\n--- CHANGEMENT DE MOT DE PASSE ---")
                confirm = input("Voulez-vous vraiment changer le mot de passe? (oui/non): ")
                if confirm.lower() not in ['oui', 'o', 'yes', 'y']:
                    print("Opération annulée.")
                    continue

                client.change_password()

            elif choice == "6":
                # Quitter
                print("\nAu revoir!")
                sys.exit(0)

            else:
                print("Choix invalide.")

        except KeyboardInterrupt:
            print("\n\nInterruption. Au revoir!")
            sys.exit(0)

        except Exception as e:
            print(f"\nERREUR : {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()
