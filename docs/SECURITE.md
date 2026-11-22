# Sécurité et limites

Avant chaque modification d'une mémoire ou d'un ECU, proposer **une sauvegarde partielle ou complète réellement lisible**, puis vérifier sa cohérence. Un hash SHA-256 prouve l'intégrité du fichier, **pas son origine matérielle, sa compatibilité ECU ou la possibilité de restauration**.

## Interverrouillages matériels
- Référence exacte de la puce, brochage et fiche constructeur avant alimentation.
- Rails 1,8/3,3/5 V mesurés, adaptés à la référence, protections ESD/inversion/courant ; aucune alimentation 12 V sur une broche mémoire.
- Interdire toute contention entre programmateur et ECU encore alimenté. En cas de doute, déposer la puce ; ne pas supposer qu'un clip est sûr in circuit.
- EEPROM : respect des cycles, pages, registres de protection ; NOR : sauvegarder et préserver le **secteur d'effacement complet**.
- Ne pas confondre clé de sécurité, déverrouillage constructeur, identification et autorisation réelle d'une opération.
- Sur ECU, vérifier alimentation, identifiants hardware/software, couverture des sauvegardes, état des sessions, procédure de récupération et journal d'opérations.
- Après interruption de communication, état ECU inconnu : aucune reprise ni retransmission aveugle.

## État implémenté
Le firmware ne sait ni lire ni écrire une mémoire ni transmettre du CAN ; le code Python ne produit que des sauvegardes de **fichiers locaux** et des plans **hors ligne**. Aucun essai véhicule/ECU, pas de récupération matériellement démontrée. Ne jamais présenter une capacité désactivée comme disponible.

## Validation des manifestes hors ligne
L'import Python refuse les champs JSON dupliqués (même lorsque leurs valeurs sont identiques) et les manifestes dépassant 64 Kio, avant lecture de l'image binaire. Ces contrôles réduisent les ambiguïtés de parsing et la consommation de mémoire ; ils ne constituent ni une signature cryptographique, ni une preuve d'origine physique. Les tests correspondants sont logiciels et ne valident aucun matériel.

L'import vérifie aussi que la racine du manifeste est un objet JSON et que la taille réelle du fichier binaire correspond exactement à la longueur déclarée **avant de calculer son empreinte SHA-256 par blocs, sans charger toute l'image en mémoire**. Il ne garantit pas une limite de taille absolue pour les images déclarées très grandes : l'appelant doit utiliser des quotas de stockage, de temps et d'entrées/sorties adaptés. L'empreinte attendue doit être une chaîne hexadécimale SHA-256 canonique de 64 caractères minuscules ; la comparaison utilise `hmac.compare_digest`. Cela ne constitue pas une authentification du manifeste.

## Sauvegardes hors ligne : fichiers locaux

La vérification refuse les composants `.json` et `.bin` qui ne sont pas des fichiers ordinaires (liens symboliques, périphériques, tubes nommés). Elle évite ainsi de lire volontairement des chemins externes ou des flux spéciaux via une sauvegarde. Le contrôle est effectué avant l'ouverture ; il ne protège **pas** contre une substitution concurrente de fichiers entre la vérification et l'ouverture (TOCTOU). Les sauvegardes doivent être conservées dans un répertoire privé et non modifiable par un tiers pendant la vérification.

L'export refuse également les liens symboliques pendants (sans cible existante) aux chemins `.bin` ou `.json` : le contrôle de non-écrasement utilise `lexists` et la création exclusive. Cela ne rend pas l'export atomique pour les deux fichiers et ne protège pas contre toutes les courses dans un répertoire modifiable par un tiers.

## Géométrie mémoire hors ligne

Le planificateur refuse désormais les technologies mémoire inconnues, les dimensions booléennes (Python considère autrement `True` comme un entier) et les zones protégées qui ne sont pas des objets `Region`. Ces contrôles empêchent qu'une description mal typée produise un plan ambigu ; ils ne vérifient **ni** la référence réelle de la puce, **ni** sa tension, **ni** son brochage. Aucun plan ne confère une autorisation d'écriture sur matériel.

## Autorisation locale des identités TLS — référence hors ligne
Le modèle Python TLS 1.3 exige maintenant un certificat client autorisé par empreinte SHA-256 en plus de la CA, et un certificat boîtier épinglé en plus de la CA et du nom. Une liste vide bloque tout ; une identité délivrée par la même CA n'est pas automatiquement autorisée. La suppression d'une empreinte interdit la connexion suivante. Les sessions TLS reprises sont refusées dans le prototype. Ne pas confondre cette liste locale de simulation et un provisionnement embarqué : stockage protégé, révocation des sessions actives, rôles et transport physique restent à qualifier. Aucun droit ECU n'en découle.
