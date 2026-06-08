#let titre = "ICR mini projet - Ransomware post quantique"
#let auteurs = ("Camille Koestli",)
#let header_titre = "ICR - mini projet"
#let header_auteurs = "Koestli"
#let project(
  title: "",
  subtitle: "",
  group: "",
  authors: (),
  nameAuthors: (),
  date: "",
  logo: "mse_logo.jpg",
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
    align(right, image(logo, width: 50%))
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
- Les clés sont de 256 bits ce qui offre 128 bits de sécurité post-quantique et donc est résistant à l'algorithme de Grover.
- L'algorithme garantit la confidentialité et l'authenticité des données.
- Les nonces sont à 96 bits et les tags d'authentification à 128 bits.

*CRYSTALS-Kyber (ML-KEM-1024)* pour pour la génération et l'encapsulation de clés post-quantiques :
- Il s'agit d'un algorithme post-quantique standardisé par le NIST.
- Le niveau 5 NIST offre 128 bits de sécurité post-quantique.
- Il résiste aux attaques par ordinateurs quantiques qui utilisent l'algorithme de Shor.

*Argon2id* pour la dérivation de clés à partir de mots de passe:
- Paramètres : `time_cost=2`, `memory_cost=64MB`, `parallelism=4`.
- Il est résistant aux attaques par GPU et bruteforce.
- Une dérivation de Master Key (MK) est réalisée à partir du mot de passe utilisateur.

== Paramètres cryptographiques

=== Clés symétriques (toutes à 256 bits)

L'uniformité garantit une sécurité 128 bits post-quantique :
- *Clé de fichier (File Key)* : 256 bits (32 octets), une par fichier
- *Master Key (MK)* : 256 bits (32 octets), dérivée du mot de passe
- *Root Key (RK)* : 256 bits (32 octets), secret partagé Kyber

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
- *Secret partagé* : 256 bits (32 octets), qui devient la Root Key
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

La communication entre le client et le serveur est réalisée localement grâce à des appels de fonctions. Pour un ransomware réel, cette communication serait effectuée grâce à un canal réseau sécurisé (ex: HTTPS).

== Hiérarchie des clés

#figure(
  image("out/schema/clés.png", width: 50%),
  caption: [Hiérarchie cryptographique des clés]
)

Le système utilise une architecture hiérarchique à 3 niveaux :

*Master Key (MK)* : Elle est dérivée du mot de passe utilisateur avec Argon2id + sel. Elle permet de protéger la Root Key et peut être changée sans rechiffrer les fichiers

*Root Key (RK)* : Elle est générée par Kyber (secret partagé de 256 bits). Elle est encapsulée avec la MK (AES-256-GCM) et protège toutes les clés de fichiers.

*Clés de fichiers* : Il s'agit d'une clé unique par fichier (256 bits aléatoires. Elles sont encapsulées avec la RK (AES-256-GCM). Une isolation va permettre qu'en cas de compromission d'une clé, cela n'entraîne pas la compromission des autres.

Cette hiérarchie permet :
- Changement de mot de passe sans rechiffrement
- Déchiffrement spécifique d'un fichier avec le mot de passe
- Déchiffrement d'un dossier complet

= Description du ransomware

== Fonctionnalités implémentées

Le ransomware possède les fonctionnalités suivantes :

*Chiffrement des fichiers* : Le système permet le chiffrement d'un dossier complet tout en excluant le code du ransomware. Pendant cette opération, un mot de passe utilisateur de 8 à 15 caractères est généré automatiquement en sélectionnant un seul mot dans la wordlist `rockyou.txt`. Pour garantir une isolation cryptographique, chaque fichier est chiffré avec une clé unique de 256 bits. Les métadonnées de chiffrement (clés encapsulées, nonces, tags) sont stockées dans des fichiers `.meta` séparés.

*Déchiffrement des fichiers* : Deux méthodes de déchiffrement sont disponibles dans le menu principal. La première méthode, `decrypt_all()`, permet le déchiffrement d'un dossier complet ou sous-dossier en donnant le mot de passe au serveur. Cela permet de retrouver l'intégralité des fichiers chiffrés. La seconde méthode, `decrypt_file()`, permet le déchiffrement d'un seul fichier spécifique avec le mot de passe.

*Gestion du mot de passe* : Cette fonction permet de changer le mot de passe sans avoir besoin de rechiffrer tous les fichiers. La méthode `change_password()` génère un nouveau mot de passe aléatoire et réencapsule uniquement la Root Key avec la nouvelle Master Key dérivée. Cette optimisation évite une opération coûteuse de rechiffrement complet qui pourrait prendre du temps selon la quantité de données à chiffrer.

== Initialisation et chiffrement

#figure(
  image("out/schema/01-Initialisation_Chiffrement.png", width: 70%),
  caption: [Processus d'initialisation et de chiffrement]
)

=== Étape 1 : Initialisation du serveur

Le serveur (`RansomwareServer.initialize_server()`) va :
+ Générer d'une paire de clés CRYSTALS-Kyber (publique/secrète).
+ Générer un mot de passe aléatoire grâce à `wordlist.generate_random_password()`. Le mot de passe est un seul mot de 8 à 15 caractères conformément à la consigne.
  - Exemple : `"password123"` (11 caractères)
  - Les mots sont filtrés de la liste rockyou.txt (8-15 caractères)
+ Générer d'un sel aléatoire de 128 bits.
+ Préparer des paramètres Argon2 (`time_cost=2`, `memory_cost=64MB`, `parallelism=4`).
+ Retourner au client : password, salt, paramètres Argon2, clé publique Kyber.

=== Étape 2 : Génération des clés cryptographiques (Client)

Le client (`RansomwareClient.encrypt_directory()`) va :
+ *Dériver la Master Key (MK)* :
  - Utilise Argon2id avec le password et le sel reçus. Cela produit une clé de 256 bits.

+ *Générer la Root Key (RK)* :
  - Encapsulation Kyber avec la clé publique du serveur. Cela produit un ciphertext Kyber (1568 octets) et un secret partagé (256 bits).
  - Le secret partagé devient la Root Key.

+ *Protéger de la Root Key* :
  - Encapsulation de la RK avec la MK avec AES-GCM. Cela produit un ciphertext, nonce (96 bits), tag (128 bits).
  - On sauvegarde dans `rootkey.bin` avec un format JSON/base64 :
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

Pour chaque fichier à chiffrer (`_encrypt_file()`), on va :

+ *Générer une clé unique* :
  - C'est une clé de fichier aléatoire de 256 bits avec `secrets.token_bytes(32)`. Elle garantit l'isolation donc en cas de compromission d'une clé, il n'y a pas de compromission des autres.

+ *Chiffrer le contenu* :
  - Avec l'algorithme AES-256-GCM qui à comme entrée le contenu du fichier et clé de fichier. La sortie est un ciphertext, un nonce (96 bits) et un tag (128 bits).

+ *Protéger la clé de fichier* :
  - On encapsule la clé de fichier avec la Root Key (AES-GCM). Cela produit `wrapped_key_ciphertext`, `wrapped_key_nonce`, `wrapped_key_tag`.

+ *Stocker les métadonnées* :
  - Dans un fichier `.meta` créé (par exemple : `document.txt.meta`) au format JSON/base64 :
    ```json
    {
      "wrapped_key_ciphertext": "...",
      "wrapped_key_nonce": "...",
      "wrapped_key_tag": "...",
      "nonce": "...",
      "tag": "..."
    }
    ```

+ *Remplacer le fichier* :
  - Le fichier original est écrasé avec le ciphertext.
  - Seul le fichier `.meta` permet le déchiffrement.

=== Fichiers exclus du chiffrement

L'implémentation a été conçu pour exclure certains fichiers et dossiers afin de préserver le code source du ransomware et les dossiers système. Les exclusions sont définies dans des listes dans `config.py` :
- Fichiers Python (`.py`, `.pyc`)
- Le code source du ransomware (`client.py`, `server.py`, ...)
- Les fichiers de métadonnées (`.meta`)
- Le fichier `rootkey.bin`
- Dossiers système (`.git`, `__pycache__`, `.venv`)

== Déchiffrement d'un dossier complet ou d'un sous-dossier

#figure(
  image("out/schema/02-Déchiffrement_Complet.png", width: 90%),
  caption: [Processus de déchiffrement complet avec le mot de passe avec la méthode `decrypt_all()`]
)

=== Étape 1 : Récupération des credentials

+ Le client demande au serveur les credentials complets.
+ Le serveur retourne : password, salt, paramètres Argon2.

=== Étape 2 : Récupération de la Root Key

Pour récupérer la Root Key, le client va :
+ *Dériver la Master Key* :
  - Utilise Argon2id avec le password, le salt et les paramètres
  - On recalcule la même MK que lors du chiffrement.

+ *Lire `rootkey.bin`* :
  - Charge les métadonnées de la Root Key

+ *Désencapsuler la Root Key* :
  - Utilise AES-GCM avec la MK avec en entrée : `wrapped_rk_ciphertext`, `wrapped_rk_nonce`, `wrapped_rk_tag`. La sortie sera la Root Key.

=== Étape 3 : Déchiffrement de tous les fichiers

Pour chaque fichier `.meta` trouvé (`_decrypt_file_with_rk()`) :

+ *Lire les métadonnées*

+ *Désencapsuler la clé de fichier* :
  - En utilisant AES-GCM avec la Root Key. Ce qui permet de récupérer la clé de fichier originale.

+ *Déchiffrer le contenu* :
  - Utilise AES-GCM avec la clé de fichier et §nonce/tag pour récupérer le contenu original.

+ *Nettoyer* :
  - Écrase le fichier chiffré avec le contenu déchiffré.
  - Supprime le fichier `.meta`.


== Déchiffrement d'un fichier avec mot de passe

#figure(
  image("out/schema/03-Dechiffrement_Spécifique.png", width: 90%),
  caption: [Déchiffrement spécifique d'un fichier avec le mot de passe avec la méthode `decrypt_file()`]
)

=== Étape 1 : Récupération des credentials

+ Le client demande au serveur les credentials complets.
+ Le serveur retourne : password, salt, paramètres Argon2.

C'est identique au déchiffrement complet.

=== Étape 2 : Récupération de la Root Key

Pour récupérer la Root Key, le client va :
+ *Dériver la Master Key* :
  - Utilise Argon2id avec le password, le salt et les paramètres
  - On recalcule la même MK que lors du chiffrement.

+ *Lire `rootkey.bin`* :
  - Charge les métadonnées de la Root Key

+ *Désencapsuler la Root Key* :
  - Utilise AES-GCM avec la MK avec en entrée : `wrapped_rk_ciphertext`, `wrapped_rk_nonce`, `wrapped_rk_tag`. La sortie sera la Root Key.

=== Étape 3 : Déchiffrement du fichier spécifique

Pour le fichier demandé (`_decrypt_file_with_rk()`) :

+ *Lire les métadonnées* :
  - Charge le fichier `.meta` correspondant au fichier à déchiffrer.

+ *Désencapsuler la clé de fichier* :
  - En utilisant AES-GCM avec la Root Key. Ce qui permet de récupérer la clé de fichier originale.

+ *Déchiffrer le contenu* :
  - Utilise AES-GCM avec la clé de fichier et le nonce/tag pour récupérer le contenu original.

+ *Nettoyer* :
  - Écrase le fichier chiffré avec le contenu déchiffré.
  - Supprime le fichier `.meta`.

== Modification du mot de passe

#figure(
  image("out/schema/04-Modification_Mdp.png", width: 90%),
  caption: [Changement de mot de passe sans rechiffrer les fichiers avec la méthode `change_password()`]
)

=== Principe

La Root Key reste inchangée (elle protège tous les fichiers), seule la Master Key change (elle protège la Root Key). Il n'y aura donc pas besoin de rechiffrer les fichiers.

=== Étape 1 : Préparation du nouveau mot de passe

+ *Générer un nouveau mot de passe* :
  - Le client génère un nouveau mot de passe aléatoire depuis la wordlist rockyou.txt.
  - Génère un nouveau salt de 128 bits.
  - Prépare les nouveaux paramètres Argon2.

+ *Récupérer le `kyber_ciphertext`* :
  - Lit le fichier `rootkey.bin` existant et on extrait le `kyber_ciphertext`.

=== Étape 2 : Réencapsulation de la Root Key

Le client envoie une demande au serveur avec : Le nouveau password, le nouveau salt, les nouveaux paramètres Argon2 et le `kyber_ciphertext`

Le serveur va :
+ *Dériver la nouvelle Master Key* :
  - Utilise Argon2id avec le nouveau password et le nouveau salt. Cela produit la nouvelle MK.

+ *Récupérer la Root Key* :
  - Utilise sa clé secrète Kyber pour désencapsuler le `kyber_ciphertext`.
  - Récupère la RK originale.

+ *Réencapsuler avec la nouvelle MK* :
  - Encapsule la RK avec la nouvelle MK (AES-GCM). Ce qui produit un nouveau `wrapped_rk_ciphertext`, un nouveau `wrapped_rk_nonce` et un nouveau `wrapped_rk_tag`.
  - Retourne ces nouvelles métadonnées au client.

=== Étape 3 : Mise à jour des métadonnées

+ *Mettre à jour `rootkey.bin`* :
  - Le client remplace les anciennes métadonnées `wrapped_rk_ciphertext`, `wrapped_rk_nonce` et `wrapped_rk_tag`.
  - Conserve le même `kyber_ciphertext`.
  - Met à jour le `salt` et les `argon2_params`.
  - Sauvegarde le nouveau fichier `rootkey.bin`.

= Implémentation technique

== Architecture du code

L'implémentation a été réalisée en Python, avec une séparation claire entre le client et le serveur.

=== Structure des fichiers

*`config.py` : Configuration et constantes*\
- Définit toutes les tailles de clés (`KEY_SIZE = 32` pour 256 bits)
- Paramètres Argon2 : `time_cost=2`, `memory_cost=65536`, `parallelism=4`
- Noms des fichiers spéciaux (`rootkey.bin`, extension `.meta`)
- Listes d'exclusion pour protéger le code source du chiffrement

*`crypto_utils.py` : Opérations cryptographiques*\
Ce module fournit des wrappers autour des bibliothèques cryptographiques.

*`wordlist.py` : Génération de mots de passe*\
- Charge et filtre `rockyou.txt` (8-15 caractères)
- Maintient un cache de 50000 mots en mémoire
- Sélectionne un seul mot de 8-15 caractères (ex: "password123")
- Utilise `secrets.choice()` pour une sélection cryptographiquement sure

*`server.py` : Serveur de gestion des clés*\
La classe `RansomwareServer` gère :
- Génération de la paire de clés Kyber (publique/secrète)
- Génération du mot de passe aléatoire et du salt
- Stockage sécurisé de la clé secrète Kyber en mémoire
- Méthode `initialize_server()` : retourne password, salt, paramètres Argon2 et clé publique Kyber
- Méthode `request_full_decryption_credentials()` : fournit les credentials pour déchiffrement complet
- Méthode `request_file_key_unwrap()` : désencapsule une clé de fichier spécifique (déchiffrement à la demande)
- Méthode `change_password()` : permet de changer le mot de passe sans rechiffrer les fichiers

*`client.py` : Client de chiffrement/déchiffrement*\
La classe `RansomwareClient` implémente les méthodes principales :
- `encrypt_directory()` : chiffrement récursif d'un dossier
- `decrypt_all()` : déchiffrement complet avec mot de passe
- `decrypt_file()` : déchiffrement sélectif via le serveur
- `change_password()` : changement de mot de passe sans rechiffrement
- `_encrypt_file()` : méthode privée de chiffrement d'un fichier
- `_decrypt_file_with_rk()` : méthode privée de déchiffrement avec RK locale
- `_should_skip_file()` / `_should_skip_dir()` : filtrage des fichiers/dossiers exclus

*`main.py` : Interface utilisateur*\
Ce module fournit un menu interactif avec 5 options qui permet de tester toutes les fonctionnalités du ransomware. Il gère les entrées utilisateur avec des valeurs par défaut pour simplifier les tests et affiche des messages d'erreur en cas de problème.

== Bibliothèques cryptographiques utilisées

*`cryptography` : Chiffrement symétrique*
- Module `AESGCM` pour le chiffrement authentifié
- Utilisé pour chiffrer les fichiers ET encapsuler toutes les clés
- Bibliothèque mature et auditée, largement utilisée en production

*`argon2` : Dérivation de clés*
- Module `argon2.low_level.hash_secret_raw` pour Argon2id
- Résistant aux attaques par GPU, ASIC et tables arc-en-ciel
- Paramètres calibrés pour ~0.5s de calcul sur machine moderne

*`pqcrypto` : Cryptographie post-quantique*
- Implémentation de ML-KEM-1024 (CRYSTALS-Kyber niveau 5)
- Utilisé uniquement pour générer et échanger la Root Key
- Bibliothèque conforme aux spécifications NIST

*`secrets` : Génération aléatoire sécurisée*
- Utilisé pour toutes les générations aléatoires (clés, nonces, salts)
- Utilise le CSPRNG du système d'exploitation

== Choix d'implémentation

L'architecture possède une séparation client/serveur. Dans ce projet, la communication est simulée localement grâce à des appels de fonctions Python. Le serveur conserve la clé secrète Kyber en mémoire pendant toute la session, tandis que le client ne manipule jamais directement cette clé secrète.

Concernant la gestion des métadonnées, le système utilise un format JSON avec encodage base64. Chaque fichier chiffré possède son fichier `.meta` contenant la clé de fichier encapsulée, ainsi que le nonce et le tag AES-GCM nécessaires au déchiffrement. Le fichier `rootkey.bin` contient la Root Key encapsulée, le ciphertext Kyber, le salt et les paramètres Argon2.

Chaque fichier utilise une clé unique générée aléatoirement, dans un but d'isolation des fichiers. Ainsi, si une clé de fichier est compromise, les autres fichiers restent protégés. 

L'utilisation de wrappers autour des bibliothèques cryptographiques améliore le maintien du code. Toutes les opérations cryptographiques utilisent le module `crypto_utils.py`.

Enfin cette architecture est résistante aux attaques quantiques grâce à l'utilisation de CRYSTALS-Kyber (ML-KEM-1024) pour la génération et l'échange de la Root Key. Les ordinateurs quantiques, grâce à l'algorithme de Shor, peuvent casser les schémas cryptographiques asymétriques, comme RSA ou encore Diffie-Hellman. CRYSTALS-Kyber, utilise le problème de Learning With Errors (LWE) sur les lattices, ce qui reste difficile même pour les ordinateurs quantiques. Pour le chiffrement symétrique, AES-256 reste sécurisé face aux attaques quantiques. L'algorithme de Grover permet une accélération, ce qui réduit la sécurité de 256 bits à 128 bits. Cela reste suffisant. Argon2id conserve sa robustesse car les algorithmes quantiques n'offrent pas d'avantage significatif contre les fonctions de hachage cryptographiques basées sur des opérations itératives. 

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

*Test 4 - Déchiffrement d'un fichier avec mot de passe* :
- Rechiffrement du dossier
- Déchiffrement d'un seul fichier via `decrypt_file()`
- Vérification que les autres fichiers restent chiffrés

= Fonctionnalités bonus

Ce projet implémente toutes les fonctionnalités de base demandées dans la consigne. Une fonctionnalité supplémentaire a été ajoutée :

Le chiffrement de dossiers avec profondeur utilise `os.walk()` pour parcourir récursivement tous les sous-dossiers. Cette fonctionnalité bonus permet de chiffrer une arborescence complète de fichiers. Le système exclut des dossiers système (`.git`, `__pycache__`, `.venv`) à tous les niveaux pour préserver l'intégrité du code source.

= Améliorations possibles

La robustesse du mot de passe n'est pas optimale au niveau de la sécurité. Le système génère un mot de passe unique de 8-15 caractères qui vient de la wordlist `rockyou.txt` et accepte tous les caractères incluant les symboles. Cependant, elle reste vulnérable aux attaques par dictionnaire car `rockyou.txt` contient des mots de passe couramment utilisés et compromis. L'entropie dépend de la taille du dictionnaire filtré (estimée entre 20-30 bits selon le nombre de mots disponibles de 8-15 caractères dans rockyou.txt), ce qui reste bien inférieur aux 128 bits de sécurité visés pour le reste du système. Une amélioration serait de générer des mots de passe vraiment aléatoires composés de caractères alphanumériques et symboles (exemple : `Kz9#mP2@xQ7!` = ~71 bits d'entropie pour 12 caractères), plutôt que de se baser sur un dictionnaire de mots de passe connus.

Au niveau des performances, l'implémentation pourrait être optimisée en utilisant le chiffrement parallèle des fichiers via multiprocessing, permettant de traiter plusieurs fichiers simultanément. Pour les fichiers volumineux, une approche de chiffrement par blocs permettrait d'améliorer les performances.

Du côté du réseau, le système pourrait utilisé un réseau HTTPS avec le serveur pour simuler un vrai ransomware. 

= Conclusion

Ce projet démontre l'implémentation d'un ransomware en utilisant la cryptographie post-quantique. L'utilisation de CRYSTALS-Kyber (ML-KEM-1024) pour la génération de la Root Key garantit une résistance aux attaques quantiques futures, conformément aux recommandations du NIST.

= Utilisation de l'IA
*Rédaction du rapport*\
La rédaction de ce rapport a bénéficié de l’assistance d’intelligences artificielles, notamment GPT-5.2 et Claude Sonnet 4.5. Ces outils ont principalement été utilisés pour : 
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