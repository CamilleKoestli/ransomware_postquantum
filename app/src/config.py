"""
Configuration et constantes
"""

# Tailles clés
KEY_SIZE = 32  # 256 bits

# Paramètres Argon2
ARGON2_TIME_COST = 2
ARGON2_MEMORY_COST = 65536  # 64 MB
ARGON2_PARALLELISM = 4
ARGON2_HASH_LEN = 32  # 256 bits
ARGON2_SALT_LEN = 16  # 128 bits

# Extensions fichiers
KEY_EXTENSION = ".key"
ROOT_KEY_EXTENSION = ".root_key"
ENC_EXTENSION = ".enc"
META_EXTENSION = ".meta"  # legacy
ROOTKEY_FILENAME = "rootkey.bin"

# Fichiers à ne pas chiffrer
EXCLUDED_FILES = {
    "requirements.txt",
    "config.py",
    "crypto_utils.py",
    "client.py",
    "server.py",
    "wordlist.py",
    "main.py",
    ROOTKEY_FILENAME,
}

# Extensions à ne pas chiffrer
EXCLUDED_EXTENSIONS = {
    ".py",
    ".pyc",
    KEY_EXTENSION,
    ROOT_KEY_EXTENSION,
    ENC_EXTENSION,
    META_EXTENSION,
}

# Dossiers à ignorer
EXCLUDED_DIRS = {
    ".",
    "..",
    ".git",
    "__pycache__",
    ".venv",
    "venv",
}
