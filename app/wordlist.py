"""
Génération de mots de passe aléatoires pour le ransomware
"""

import secrets

# Liste de mots simples pour générer des mots de passe faciles à tester
WORD_LIST = [
    "pomme", "soleil", "chat", "bleu", "vert",
    "rouge", "maison", "jardin", "fleur", "arbre",
    "eau", "feu", "terre", "air", "ciel",
    "lune", "etoile", "mer", "montagne", "riviere",
    "chien", "oiseau", "poisson", "lion", "tigre",
    "livre", "table", "chaise", "porte", "fenetre",
]


def generate_random_password(num_words: int = 4, separator: str = "-") -> str:
    """
    Génère un mot de passe aléatoire composé de mots simples

    Args:
        num_words: Nombre de mots à utiliser (défaut: 4)
        separator: Séparateur entre les mots (défaut: "-")

    Returns:
        Mot de passe généré (ex: "pomme-soleil-chat-bleu")
    """
    words = [secrets.choice(WORD_LIST) for _ in range(num_words)]
    password = separator.join(words)
    return password


if __name__ == "__main__":
    # Test de génération de mots de passe
    print("Exemples de mots de passe générés:")
    for i in range(5):
        print(f"  {i+1}. {generate_random_password()}")
