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

= Niveau de sécurité
Niveau de sécurité avec AES 256 bits : 5
Résistant aux attaques quantiques avec CRYSTALS-Kyber et AES-GCM 256 bits
Résistant aux attaques par force brute avec Argon2

Même niveau de sécurité partout

= Utilisation de bibliothèques sécurisées
+ Utilisation de la bibliothèque `cryptography` pour les opérations de chiffrement symétrique
+ Utilisation de la bibliothèque `pyca/argon2` pour la dérivation de clés
+ Utilisation de la bibliothèque `pqcrypto` pour les opérations post-quantiques avec CRYSTALS-Kyber
+ Gestion sécurisée des clés et des mots de passe en mémoire
+ Mise en place de bonnes pratiques de sécurité pour minimiser les risques de vulnérabilités 

= Gestion des clés
+ Utilisation d'AES-GCM 256 bits pour le chiffrement des clés et des fichiers
+ Utilisation d'Argon2 pour la dérivation de clés à partir de mots de passe
+ Utilisation de CRYSTALS-Kyber pour la génération de clés post-quantiques

== Taille des clés
+ Clé de fichier : 256 bits
+ Master Key (MK) : 256 bits
+ Root Key (RK) : 256 bits

= Architecture cryptographique
Le ransomware est composé de deux parties principales : le client et le serveur.
- Le client est responsable du chiffrement des fichiers sur la machine de la victime.
- Le serveur gère la génération des clés, le stockage sécurisé des informations de chiffrement et la communication avec le client.

= Description du ransomware
== Fonctionnalités principales
- Chiffrement des fichiers avec AES-GCM 256 bits
- Chiffrement des clés de fichiers et de la Root Key avec AES-GCM 256 bits
- Dérivation de la Master Key à partir d'un mot de passe avec Argon2
- Génération de la Root Key avec CRYSTALS-Kyber
- Stockage sécurisé des informations de chiffrement dans les métadonnées des fichiers
- Possibilité de déchiffrement complet ou partiel des fichiers
- Possibilité de modification du mot de passe de chiffrement

== Lancement du ransomware
+ On génère une Master Key (MK) dérivée avec Argon2 à partir d'un mot de passe aléatoire du dictionnaire rockyou.txt.
+ On génère la Root Key (RK) de 256 bits via encapsulation CRYSTALS-Kyber.

== Chiffrement des fichiers et de la Root Key
Le chiffrement se fera au niveau où le ransomware est lancé (dossier ou disque entier), sans prendre le ransomware dans le chiffrement et les dossiers au dessus.

Le chiffrement des fichiers se fait de la manière suivante :
- Pour chaque fichier à chiffrer:
  + On chiffre le fichier avec AES-GCM 256 bits.
  + On chiffre la clé du fichier avec la RK avec AES-GCM 256 bits.
  + On stocke le ciphertext, nonce et tag de la clé wrappée dans les métadonnées du fichier.

- Pour la Root Key:
  + On chiffre la RK avec la MK avec AES-GCM 256 bits.
  + On stocke le ciphertext, nonce et tag dans un nouveau fichier `rootkey.bin`.

== Paiement de la rançon
Lors du choix de payer la rançon :
+ Le serveur envoie le mot de passe et les paramètres Argon2 au client.
+ Le client dérive la clé à partir du mot de passe et des paramètres Argon2, puis déchiffre la RK avec AES-GCM 256 bits en utilisant cette clé dérivée.
+ Le client déchiffre chaque clé de fichier avec la RK.
+ Le client déchiffre chaque fichier avec AES-GCM en utilisant la clé du fichier, le nonce et le tag stockés dans les métadonnées du fichier.

== Déchiffrement
=== Déchiffrement de l'ensemble des dossiers et fichiers
+ Le serveur envoie le mot de passe et les paramètres Argon2 au client.
+ Le client dérive la MK avec Argon2.
+ Le client déchiffre la RK avec la MK.

=== Déchiffrement d'un dossier ou d'un fichier spécifique
+ Le client envoie au serveur le texte chiffré des métadonnées du fichier.
+ Le serveur unwrap la clé du fichier avec la RK et envoie la clé au client.
+ Le client déchiffre le fichier avec la clé reçue.

== Modification du mot de passe
+ Le serveur demande de réinitialiser le mot de passe.
+ Le client génère un nouveau mot de passe aléatoire du dictionnaire.
+ Le client dérive une nouvelle MK avec Argon2.
+ Le client transmet le paquet de mot de passe et paramètres Argon2 au serveur.
+ Le serveur dérive la nouvelle MK et déchiffre la RK avec la MK.
+ Le serveur chiffre la RK avec la nouvelle MK et stocke le tout dans `rootkey.bin`.
+ Le serveur envoie la RK chiffrée au client.
+ Le client remplace le fichier de l'ancienne RK chiffrée par la nouvelle.


= Implémentation technique
== Librairies utilisées
- `pyca/cryptography` pour le chiffrement symétrique (AES-GCM)
- `pyca/argon2` pour la dérivation de clés avec Argon2
- `pqcrypto` pour les opérations post-quantiques avec CRYSTALS-Kyber

CRYSTALS-Kyber (ML-KEM-1024) : Utilisé seulement pour générer/échanger la Root Key
AES-GCM 256 : Utilisé pour chiffrer les fichiers ET pour l'encapsulation de toutes les clés
Argon2id : Utilisé pour dériver la Master Key du mot de passe

= Conclusion


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