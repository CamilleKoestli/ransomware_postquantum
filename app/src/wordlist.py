"""
Génération de mots de passe aléatoires avec rockyou.txt
"""

import secrets
from pathlib import Path

# Option 1: rockyou.txt
ROCKYOU_PATH = Path(__file__).parent / "rockyou.txt"

# Option 2: rockyou_filtered.txt liste simple de ~100 mots pour tests
# ROCKYOU_PATH = Path(__file__).parent / "rockyou_filtered.txt"

# Cache mots chargés
_WORD_CACHE = None
_CACHE_SIZE = 50000


def _load_rockyou_words():
    """
    Charge mots depuis rockyou.txt

    Filtre uniquement les mots de 8-15 caractères

    Returns:
        Liste de mots ok
    """
    global _WORD_CACHE

    if _WORD_CACHE is not None:
        return _WORD_CACHE

    if not ROCKYOU_PATH.exists():
        raise FileNotFoundError(
            f"rockyou.txt introuvable à {ROCKYOU_PATH}. "
        )

    # Filtre mots
    valid_words = []
    with open(ROCKYOU_PATH, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            word = line.strip()
            # 8-15 caractères
            if 8 <= len(word) <= 15 and word.isprintable() and len(word) > 0:
                valid_words.append(word)

            # Stop si on a assez de mots
            if len(valid_words) >= _CACHE_SIZE * 2:
                break

    # Choix aléatoire de CACHE_SIZE mots
    if len(valid_words) > _CACHE_SIZE:
        words = secrets.SystemRandom().sample(valid_words, _CACHE_SIZE)
    else:
        words = valid_words

    _WORD_CACHE = words
    print(f"[WL] {len(words)} mots en cache")

    return words


def generate_random_password() -> str:
    """
    Génère mdp aléatoire avec mots de rockyou.txt

    Sélectionne un seul mot

    Returns:
        Mdp généré
    """
    word_list = _load_rockyou_words()
    password = secrets.choice(word_list)
    return password
