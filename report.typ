#let titre = "CAA mini projet - Ransomware post quantique"
#let auteurs = ("Camille Koestli",)
#let header_titre = "CAA - mini projet"
#let header_auteurs = "Koestli"
#let project(
  title: "",
  subtitle: "",
  group: "",
  authors: (),
  nameAuthors: (),
  date: "",
  logo: "HEIG-VD_logo.png",
  body,
) = {
  set page(numbering: "1", number-align: center)
  set text(font: "New Computer Modern", lang: "fr")
  show math.equation: set text(weight: 400)
  set page(header: [
    #header_auteurs
    #h(1fr)
    #header_titre\
    ---————————————————————————————————————--------------])

  // Title page.
  v(0.6fr)
  if logo != none {
    align(right, image(logo, width: 26%))
  }
  v(9.6fr)

  align(center, text(1em, "---————————————————————————————————————---"))
  v(0.2em)
  align(center, text(2em, weight: 700, title))
  v(0.2em)
  align(center, text(1em, "---————————————————————————————————————---"))
  v(1fr)

  //subtitle
  align(center, text(1.2em, subtitle))
  align(center, text(1.1em, group))
  v(10fr)
  v(1em)

  //date
  text(1.1em, date)

  // Author information.
  pad(
    top: 0.7em,
    right: 20%,
    grid(
      columns: (1fr,) * calc.min(3, authors.len()),
      gutter: 1.2em,
      ..authors.map(author => align(start, strong(author))),
    ),
  )

  v(2.4fr)
  pagebreak()

  // Table des matières
  show outline.entry.where(level: 1): it => {
    v(0.8em, weak: true)
    strong(it)
  }

  outline(
    title: [Table des matières],
    indent: auto,
  )
  pagebreak()

  // Main body.
  set par(justify: true)
  set heading(numbering: "1.1.")

  body
}

#show: project.with(
  title: titre,
  authors: auteurs,
  date: datetime.today().display("[day].[month].[year]"),
)

= Consigne
Les consignes sont disponibles dans le document #link("mini_project_2526.pdf")[`mini_project_2526.pdf`].

= Niveau de sécurité choisi

Le système implémente un niveau de sécurité de 128 bits post-quantique, ce qui est le niveau 5 NIST. Cela permet une protection robuste contre les attaques classiques et quantiques.

== Choix des algorithmes

*AES-256-GCM* pour le chiffrement symétrique des clés et des fichiers :
- Les clés sont de 256 bits ce qui offre 128 bits de sécurité post-quantique et donc est résistant à l'algorithme de Grover
- L'algorithme garantit la confidentialité et l'authenticité des données
- Les nonces sont à 96 bits et les tags d'authentification à 128 bits

*CRYSTALS-Kyber (ML-KEM-1024)* pour pour la génération et l'encapsulation de clés post-quantiques :
- Il s'agit d'un algorithme post-quantique standardisé par le NIST
- Le niveau 5 NIST offre 128 bits de sécurité post-quantique
- Il résiste aux attaques par ordinateurs quantiques qui utilisent l'algorithme de Shor

*Argon2id* pour la dérivation de clés à partir de mots de passe:
- Paramètres : `time_cost=2`, `memory_cost=64MB`, `parallelism=4`
- Il est résistant aux attaques par GPU et bruteforce
- Une dérivation de Master Key (MK) est réalisée à partir du mot de passe utilisateur

== Paramètres cryptographiques

=== Clés symétriques (toutes à 256 bits)

L'uniformité garantit une sécurité 128 bits post-quantique :
- *Clé de fichier (File Key)* : 256 bits (32 octets) - une par fichier
- *Master Key (MK)* : 256 bits (32 octets) - dérivée du mot de passe
- *Root Key (RK)* : 256 bits (32 octets) - secret partagé Kyber

=== Paramètres AES-256-GCM

- *Nonce* : 96 bits (12 octets), qui est la taille optimale pour GCM
- *Tag d'authentification* : 128 bits (16 octets)
- *Taille de bloc* : 128 bits

=== Paramètres Argon2id

- *Salt* : 128 bits (16 octets)
- *Hash de sortie* : 256 bits (32 octets)
- *time_cost* : 2 itérations
- *memory_cost* : 65536 KB
- *parallelism* : 4 threads

=== CRYSTALS-Kyber (ML-KEM-1024)

- *Clé publique* : 1568 octets
- *Clé secrète* : 3168 octets
- *Ciphertext* : 1568 octets
- *Secret partagé* : 256 bits (32 octets) - devient la Root Key
- *Niveau NIST* : 5 (équivalent AES-256 post-quantique)

Tous ces paramètres sont définis dans `config.py`.

= Architecture générale

== Séparation client/serveur

#figure(
  image("out/schema/client-serveur.png", width: 100%),
  caption: [Architecture client-serveur du ransomware]
)

Le ransomware est composé de deux parties distinctes :

*Serveur (attaquant)* :
- Génère la paire de clés CRYSTALS-Kyber (publique/secrète)
- Génère le mot de passe aléatoire mémorable
- Conserve la clé secrète Kyber en mémoire sécurisée
- Fournit les credentials pour le déchiffrement

*Client (victime)* :
- Dérive la Master Key (MK) à partir du mot de passe
- Encapsule la Root Key (RK) via Kyber
- Chiffre/déchiffre les fichiers
- Stocke les métadonnées localement (`rootkey.bin`, fichiers `.meta`)

La communication est actuellement simulée localement (appels de fonctions Python), mais l'architecture modulaire permet une future implémentation réseau.

== Hiérarchie des clés

#figure(
  image("out/schema/clés.png", width: 70%),
  caption: [Hiérarchie cryptographique des clés]
)

Le système utilise une architecture hiérarchique à 3 niveaux :

*Niveau 1 - Master Key (MK)* :
- Dérivée du mot de passe utilisateur avec Argon2id + salt
- Protège la Root Key
- Changeable sans rechiffrer les fichiers

*Niveau 2 - Root Key (RK)* :
- Générée par Kyber (secret partagé de 256 bits)
- Encapsulée avec la MK (AES-256-GCM)
- Protège toutes les clés de fichiers

*Niveau 3 - Clés de fichiers* :
- Une clé unique par fichier (256 bits aléatoires)
- Encapsulées avec la RK (AES-256-GCM)
- Isolation : compromission d'une clé ≠ compromission des autres

Cette hiérarchie permet :
- Changement de mot de passe sans rechiffrement
- Déchiffrement sélectif (fichier par fichier via le serveur)
- Déchiffrement complet (avec le mot de passe)

= Description du ransomware

== Fonctionnalités implémentées

Le ransomware offre les fonctionnalités suivantes :

*Chiffrement :*
- Chiffrement récursif d'un dossier avec exclusion du code source
- Génération automatique d'un mot de passe mémorable (4 mots de rockyou.txt)
- Une clé unique par fichier pour isolation cryptographique
- Métadonnées stockées dans des fichiers `.meta` séparés

*Déchiffrement :*
- Déchiffrement complet avec fourniture du mot de passe (méthode `decrypt_all()`)
- Déchiffrement sélectif fichier par fichier via le serveur (méthode `decrypt_file()`)
- Pas besoin de la Root Key côté client pour le déchiffrement sélectif

*Gestion du mot de passe :*
- Changement de mot de passe sans rechiffrer les fichiers (méthode `change_password()`)
- Réencapsulation de la Root Key avec la nouvelle Master Key

== Initialisation et chiffrement

#figure(
  image("out/schema/01-Initialisation_Chiffrement.png", width: 70%),
  caption: [Processus d'initialisation et de chiffrement]
)

=== Étape 1 : Initialisation du serveur

Le serveur (`RansomwareServer.initialize_server()`) effectue :
+ Génération d'une paire de clés CRYSTALS-Kyber (publique/secrète)
+ Génération d'un mot de passe aléatoire de 4 mots via `wordlist.generate_random_password()`
  - Exemple : `"dragon-shadow-matrix-secret"`
  - Mots filtrés de rockyou.txt (4-10 caractères, alphanumériques)
+ Génération d'un salt aléatoire de 128 bits
+ Préparation des paramètres Argon2 (time_cost=2, memory_cost=64MB, parallelism=4)
+ Retour au client : password, salt, paramètres Argon2, clé publique Kyber

=== Étape 2 : Génération des clés cryptographiques (Client)

Le client (`RansomwareClient.encrypt_directory()`) effectue :
+ *Dérivation de la Master Key (MK)* :
  - Utilise Argon2id avec le password et le salt reçus
  - Produit une clé de 256 bits
  - Temps de calcul : ~0.5s (protection contre brute force)

+ *Génération de la Root Key (RK)* :
  - Encapsulation Kyber avec la clé publique du serveur
  - Produit : ciphertext Kyber (1568 octets) + secret partagé (256 bits)
  - Le secret partagé devient la Root Key

+ *Protection de la Root Key* :
  - Encapsulation de la RK avec la MK via AES-GCM
  - Génération de : ciphertext, nonce (96 bits), tag (128 bits)
  - Sauvegarde dans `rootkey.bin` (format JSON/base64) :
    ```json
    {
      "wrapped_rk_ciphertext": "...",
      "wrapped_rk_nonce": "...",
      "wrapped_rk_tag": "...",
      "kyber_ciphertext": "...",
      "salt": "...",
      "argon2_params": {...}
    }
    ```

=== Étape 3 : Chiffrement des fichiers

Pour chaque fichier à chiffrer (`_encrypt_file()`) :

+ *Génération d'une clé unique* :
  - Clé de fichier aléatoire de 256 bits via `secrets.token_bytes(32)`
  - Garantit l'isolation : compromission d'une clé ≠ compromission des autres

+ *Chiffrement du contenu* :
  - Algorithme : AES-256-GCM
  - Entrée : contenu du fichier + clé de fichier
  - Sortie : ciphertext, nonce (96 bits), tag (128 bits)

+ *Protection de la clé de fichier* :
  - Encapsulation de la clé de fichier avec la Root Key (AES-GCM)
  - Produit : wrapped_key_ciphertext, wrapped_key_nonce, wrapped_key_tag

+ *Stockage des métadonnées* :
  - Fichier `.meta` créé (exemple : `document.txt.meta`)
  - Format JSON/base64 :
    ```json
    {
      "wrapped_key_ciphertext": "...",
      "wrapped_key_nonce": "...",
      "wrapped_key_tag": "...",
      "nonce": "...",
      "tag": "..."
    }
    ```

+ *Remplacement du fichier* :
  - Le fichier original est écrasé avec le ciphertext
  - Seul le fichier `.meta` permet le déchiffrement

=== Fichiers exclus du chiffrement

Le système protège automatiquement :
- Fichiers Python (`.py`, `.pyc`)
- Le code source du ransomware (`client.py`, `server.py`, etc.)
- Les fichiers de métadonnées (`.meta`)
- Le fichier `rootkey.bin`
- Dossiers système (`.git`, `__pycache__`, `.venv`)

== Déchiffrement complet

#figure(
  image("out/schema/02-Déchiffrement_Complet.png", width: 90%),
  caption: [Processus de déchiffrement complet avec le mot de passe]
)

Méthode `decrypt_all()` - Le client possède le mot de passe :

=== Étape 1 : Récupération des credentials

+ Le client demande au serveur les credentials complets
+ Le serveur retourne : password, salt, paramètres Argon2
+ (Dans un vrai ransomware, cela nécessiterait un paiement)

=== Étape 2 : Récupération de la Root Key

+ *Dérivation de la Master Key* :
  - Utilise Argon2id avec password + salt + paramètres
  - Recalcul la même MK que lors du chiffrement

+ *Lecture de rootkey.bin* :
  - Charge les métadonnées de la Root Key

+ *Désencapsulation de la Root Key* :
  - Utilise AES-GCM avec la MK
  - Entrée : wrapped_rk_ciphertext, wrapped_rk_nonce, wrapped_rk_tag
  - Sortie : Root Key (256 bits)

=== Étape 3 : Déchiffrement de tous les fichiers

Pour chaque fichier `.meta` trouvé (`_decrypt_file_with_rk()`) :

+ *Lecture des métadonnées* :
  - Charge le fichier `.meta` associé

+ *Désencapsulation de la clé de fichier* :
  - Utilise AES-GCM avec la Root Key
  - Récupère la clé de fichier originale (256 bits)

+ *Déchiffrement du contenu* :
  - Utilise AES-GCM avec la clé de fichier
  - Restaure le contenu original

+ *Nettoyage* :
  - Écrase le fichier chiffré avec le contenu déchiffré
  - Supprime le fichier `.meta`

== Déchiffrement spécifique d'un fichier ou d'un dossier

#figure(
  image("out/schema/03-Dechiffrement_Spécifique.png", width: 90%),
  caption: [Déchiffrement spécifique d'un fichier ou d'un dossier sans exposer la Root Key]
)

Méthode `decrypt_file()` - Le client N'A PAS la Root Key :

=== Architecture de sécurité

Ce mode permet un déchiffrement "pay-per-file" :
- Le client ne reçoit jamais la Root Key
- Le serveur désencapsule chaque clé de fichier à la demande
- Limitation possible du nombre de fichiers déchiffrables

=== Processus de déchiffrement

+ *Lecture des métadonnées* :
  - Le client lit le fichier `.meta`
  - Récupère : wrapped_key_ciphertext, wrapped_key_nonce, wrapped_key_tag
  - Récupère aussi le kyber_ciphertext depuis `rootkey.bin`

+ *Demande au serveur* :
  - Le client appelle `server.request_file_key_unwrap()`
  - Envoie : les métadonnées de la clé wrappée + kyber_ciphertext

+ *Désencapsulation côté serveur* :
  - Le serveur désencapsule la RK avec Kyber (via sa clé secrète)
  - Le serveur désencapsule la clé de fichier avec la RK
  - Le serveur retourne la clé de fichier déjà désencapsulée

+ *Déchiffrement côté client* :
  - Le client reçoit la clé de fichier en clair
  - Déchiffre le fichier avec AES-GCM
  - Restaure le fichier et supprime le `.meta`

== Modification du mot de passe

#figure(
  image("out/schema/04-Modification_Mdp.png", width: 90%),
  caption: [Changement de mot de passe sans rechiffrer les fichiers]
)

Méthode `change_password()` - Permet de changer le mot de passe sans rechiffrer tous les fichiers :

=== Principe

- La Root Key reste inchangée (elle protège tous les fichiers)
- Seule la Master Key change (elle protège la Root Key)
- Pas besoin de rechiffrer les fichiers (optimisation majeure)

=== Processus détaillé

+ *Génération du nouveau mot de passe* :
  - Le client génère un nouveau mot de passe aléatoire
  - Génère un nouveau salt de 128 bits
  - Prépare les nouveaux paramètres Argon2

+ *Demande au serveur* :
  - Le client envoie : nouveau password, nouveau salt, nouveaux paramètres
  - Envoie aussi le kyber_ciphertext depuis `rootkey.bin`

+ *Réencapsulation côté serveur* :
  - Le serveur dérive la nouvelle MK avec Argon2
  - Le serveur récupère la RK via Kyber (avec sa clé secrète)
  - Le serveur réencapsule la RK avec la nouvelle MK (AES-GCM)
  - Retourne : nouveau wrapped_rk_ciphertext, nonce, tag

+ *Mise à jour de rootkey.bin* :
  - Le client remplace les anciennes métadonnées
  - Conserve le kyber_ciphertext (inchangé)
  - Met à jour le salt et les paramètres Argon2
  - Sauvegarde le nouveau `rootkey.bin`

=== Avantages

- Opération très rapide (~1 seconde vs plusieurs minutes/heures de rechiffrement)
- Pas de risque de corruption des fichiers
- Permet de gérer plusieurs "clients" avec des mots de passe différents


= Implémentation technique

== Architecture du code

L'implémentation a été réalisée en Python, avec une séparation claire entre le client et le serveur.



=== Structure des fichiers

*`config.py` - Configuration et constantes*
- Définit toutes les tailles de clés (`KEY_SIZE = 32` pour 256 bits)
- Paramètres Argon2 : `time_cost=2`, `memory_cost=65536` (64 MB), `parallelism=4`
- Noms des fichiers spéciaux (`rootkey.bin`, extension `.meta`)
- Listes d'exclusion pour protéger le code source du chiffrement

*`crypto_utils.py` - Opérations cryptographiques*

Ce module fournit des wrappers autour des bibliothèques cryptographiques :
- `generate_random_key()` : génération sécurisée avec `secrets.token_bytes()`
- `derive_key_argon2()` : dérivation de clés avec Argon2id
- `encrypt_aes_gcm()` / `decrypt_aes_gcm()` : chiffrement symétrique AEAD
- `wrap_key_aes_gcm()` / `unwrap_key_aes_gcm()` : encapsulation de clés
- `generate_kyber_keypair()` : génération de paire de clés ML-KEM-1024
- `kyber_encapsulate()` / `kyber_decapsulate()` : échange de clés post-quantique

Toutes les opérations cryptographiques passent par ces fonctions, assurant une utilisation cohérente et sécurisée des bibliothèques.

*`wordlist.py` - Génération de mots de passe*
- Charge et filtre `rockyou.txt` (4-10 caractères, alphanumériques uniquement)
- Maintient un cache de 50,000 mots en mémoire
- Génère des mots de passe mémorables de 4 mots (ex: "dragon-shadow-matrix-secret")
- Utilise `secrets.choice()` pour sélection cryptographiquement sécurisée

*`server.py` - Serveur de gestion des clés*

La classe `RansomwareServer` gère :
- Génération de la paire de clés Kyber (publique/secrète)
- Génération du mot de passe aléatoire et du salt
- Stockage sécurisé de la clé secrète Kyber en mémoire
- Méthode `initialize_server()` : retourne password, salt, paramètres Argon2 et clé publique Kyber
- Méthode `request_full_decryption_credentials()` : fournit les credentials pour déchiffrement complet
- Méthode `request_file_key_unwrap()` : désencapsule une clé de fichier spécifique (déchiffrement à la demande)
- Méthode `change_password()` : permet de changer le mot de passe sans rechiffrer les fichiers

*`client.py` - Client de chiffrement/déchiffrement*

La classe `RansomwareClient` implémente les méthodes principales :
- `encrypt_directory()` : chiffrement récursif d'un dossier
- `decrypt_all()` : déchiffrement complet avec mot de passe
- `decrypt_file()` : déchiffrement sélectif via le serveur
- `change_password()` : changement de mot de passe sans rechiffrement
- `_encrypt_file()` : méthode privée de chiffrement d'un fichier
- `_decrypt_file_with_rk()` : méthode privée de déchiffrement avec RK locale
- `_should_skip_file()` / `_should_skip_dir()` : filtrage des fichiers/dossiers exclus

*`main.py` - Interface utilisateur*
- Menu interactif avec 6 options
- Gestion des entrées utilisateur avec valeurs par défaut
- Confirmations pour les opérations sensibles
- Gestion des erreurs avec affichage détaillé

== Bibliothèques cryptographiques utilisées

*`cryptography` (PyCA) - Chiffrement symétrique*
- Module `AESGCM` pour le chiffrement authentifié
- Utilisé pour chiffrer les fichiers ET encapsuler toutes les clés
- Bibliothèque mature et auditée, largement utilisée en production

*`argon2` (PyCA) - Dérivation de clés*
- Module `argon2.low_level.hash_secret_raw` pour Argon2id
- Résistant aux attaques par GPU, ASIC et tables arc-en-ciel
- Paramètres calibrés pour ~0.5s de calcul sur machine moderne

*`pqcrypto` - Cryptographie post-quantique*
- Implémentation de ML-KEM-1024 (CRYSTALS-Kyber niveau 5)
- Utilisé uniquement pour générer et échanger la Root Key
- Bibliothèque conforme aux spécifications NIST

*`secrets` - Génération aléatoire sécurisée*
- Utilisé pour toutes les générations aléatoires (clés, nonces, salts)
- Utilise le CSPRNG du système d'exploitation

== Choix d'implémentation

*Séparation client/serveur :*
- Architecture modulaire permettant une communication réseau future
- Pour ce projet éducatif, la communication est simulée localement (appels de fonctions)
- Le serveur conserve la clé secrète Kyber en mémoire
- Le client ne manipule jamais directement la clé secrète Kyber

*Gestion des métadonnées :*
- Format JSON avec encodage base64 pour lisibilité (contexte éducatif)
- Chaque fichier chiffré possède son fichier `.meta` contenant :
  - La clé de fichier encapsulée (wrapped avec la RK)
  - Le nonce et le tag AES-GCM
- Le fichier `rootkey.bin` contient :
  - La Root Key encapsulée (wrapped avec la MK)
  - Le ciphertext Kyber
  - Le salt et les paramètres Argon2

*Isolation des clés de fichiers :*
- Chaque fichier utilise une clé unique générée aléatoirement
- Si une clé de fichier est compromise, les autres fichiers restent protégés
- Pattern standard dans les ransomwares modernes

*Utilisation de wrappers :*
- Toutes les opérations cryptographiques passent par `crypto_utils.py`
- Facilite les tests et la maintenance
- Garantit une utilisation cohérente des bibliothèques
- Permet de changer facilement d'implémentation si nécessaire

*Gestion des erreurs :*
- Exceptions levées pour toutes les erreurs cryptographiques
- Validation des tailles de clés et paramètres
- Messages d'erreur détaillés pour le débogage (contexte éducatif)

= Tests et validation

== Structure des tests

Le fichier `app/test/test.py` valide les fonctionnalités principales :

*Test 1 - Chiffrement* :
- Chiffrement récursif du dossier `dossier_0`
- Vérification de la création de `rootkey.bin`
- Vérification de la création des fichiers `.meta`

*Test 2 - Déchiffrement complet* :
- Déchiffrement de tous les fichiers via `decrypt_all()`
- Vérification de la restauration du contenu original
- Suppression des fichiers `.meta`

*Test 3 - Changement de mot de passe* :
- Génération d'un nouveau mot de passe
- Mise à jour de `rootkey.bin`
- Vérification que les fichiers restent chiffrés

*Test 4 - Déchiffrement sélectif* :
- Rechiffrement du dossier
- Déchiffrement d'un seul fichier via `decrypt_file()`
- Vérification que les autres fichiers restent chiffrés

== Résultats observés

✅ *Chiffrement* : Tous les fichiers sont correctement chiffrés avec des clés uniques
✅ *Déchiffrement complet* : Restauration intégrale du contenu original
✅ *Déchiffrement sélectif* : Fonctionne sans exposer la Root Key au client
✅ *Changement de mot de passe* : Opération rapide (~1s) sans rechiffrement
✅ *Exclusions* : Le code source et les dossiers système sont préservés

= Limitations et améliorations possibles

== Limitations du contexte éducatif

*Communication client/serveur* :
- Actuellement simulée localement (appels de fonctions Python)
- Dans un ransomware réel, nécessiterait une vraie communication réseau (HTTP/HTTPS)
- Pas d'authentification ou de chiffrement des communications

*Stockage des métadonnées* :
- Format JSON/base64 lisible et verbeux (~40% d'overhead)
- Un format binaire serait plus compact et moins lisible
- Pas de vérification d'intégrité de `rootkey.bin` (pas de signature)

*Gestion des erreurs* :
- Messages d'erreur détaillés (utiles pour l'apprentissage, dangereux en production)
- Pas de gestion des pannes pendant le chiffrement (fichiers partiellement chiffrés)
- Pas de sauvegarde ou de rollback en cas d'erreur

== Vulnérabilités potentielles

*Récupération des clés en mémoire* :
- Les clés sont stockées en clair en RAM pendant l'exécution
- Attaque par dump mémoire possible
- Amélioration : utiliser des zones mémoire sécurisées (mlock, secure_memory)

*Traces sur le disque* :
- Les fichiers originaux sont écrasés mais pourraient être récupérés (forensics)
- Amélioration : écraser avec des données aléatoires (méthode Gutmann)

*Clé secrète Kyber persistante* :
- Le serveur conserve la clé secrète Kyber en mémoire pendant toute la session
- Si le serveur est compromis, tous les fichiers peuvent être déchiffrés
- Amélioration : détruire la clé secrète après l'encapsulation initiale

*Pas de vérification d'authenticité* :
- `rootkey.bin` peut être modifié par un attaquant
- Amélioration : signer `rootkey.bin` avec la clé Kyber

== Améliorations possibles

*Performance* :
- Chiffrement parallèle des fichiers (multiprocessing)
- Optimisation pour les gros fichiers (chiffrement par chunks)

*Fonctionnalités* :
- Support du chiffrement réseau (communication HTTPS avec le serveur)
- Interface graphique pour simplifier l'utilisation
- Logs d'opérations pour audit

*Sécurité* :
- Anti-debugging et obfuscation du code
- Détection de machines virtuelles / sandboxes
- Persistance (redémarrage automatique)

= Conclusion

Ce projet démontre l'implémentation d'un ransomware éducatif intégrant la cryptographie post-quantique. L'utilisation de CRYSTALS-Kyber (ML-KEM-1024) pour la génération de la Root Key garantit une résistance aux attaques quantiques futures, conformément aux recommandations du NIST.

== Points forts de l'implémentation

*Architecture cryptographique solide* :
- Niveau de sécurité uniforme à 128 bits post-quantique
- Utilisation exclusive d'algorithmes standardisés (NIST, PyCA)
- Séparation claire entre clés symétriques et asymétriques post-quantiques

*Flexibilité opérationnelle* :
- Trois modes de déchiffrement (complet, sélectif, par dossier)
- Changement de mot de passe sans rechiffrement des fichiers
- Isolation cryptographique complète entre fichiers (clé unique par fichier)

*Code modulaire et maintenable* :
- Séparation claire des responsabilités (client, serveur, crypto)
- Wrappers autour des bibliothèques pour cohérence et sécurité
- Tests validant toutes les fonctionnalités principales

== Objectifs pédagogiques atteints

Ce projet a permis d'explorer :
- L'intégration pratique de la cryptographie post-quantique (Kyber/ML-KEM)
- La gestion hiérarchique des clés (File Keys → Root Key → Master Key)
- L'équilibre entre sécurité cryptographique et utilisabilité (mots de passe mémorables)
- Les patterns d'architecture des ransomwares modernes

== Perspective

Bien que ce ransomware soit conçu dans un cadre éducatif, il illustre les défis de sécurité actuels :
- La transition vers la cryptographie post-quantique est indispensable
- Les ransomwares modernes utilisent des architectures cryptographiques sophistiquées
- La défense nécessite une compréhension approfondie de ces mécanismes

L'implémentation démontre qu'avec des bibliothèques appropriées (cryptography, pqcrypto, argon2), il est possible de construire un système cryptographique robuste tout en maintenant une complexité maîtrisable.

= Utilisation de l'IA
*Rédaction du rapport*\
La rédaction de ce rapport a bénéficié de l’assistance d’intelligences artificielles, notamment GPT-5.1 et Claude Sonnet 4.5. Ces outils ont principalement été utilisés pour : 
- La reformulation de phrases afin d’améliorer la clarté et la qualité du texte.
- La structuration de certains paragraphes pour une meilleure cohérence.
- La vérification des termes techniques.
- La correction et ajouts d'éléments sur les schémas explicatifs.

Cette aide m’a permis de maintenir une certaine qualité dans la rédaction tout en respectant l’aspect technique et les objectifs pédagogiques du projet. L’IA n’a pas écrit le rapport à ma place, mais elle a été utilisée comme un outil de soutien à la rédaction.

*Assistance au développement* \
L’IA a également été utilisée lors du développement pour : 
- Le débogage afin d’identifier et résoudre des erreurs de code ou d’exécution 
- Optimiser et améliorer certaines fonctions.
- Résoudre des problèmes techniques qui ont demandé une assistance lors de blocages sur des configurations spécifiques.
- La compréhension des bibliothèques et la clarification de la documentation des technologies utilisées. 

L’usage de l’IA a donc servi d’assistant de débogage et de documentation, pour faciliter la compréhension de certains messages d’erreur et accélérer le processus de développement.