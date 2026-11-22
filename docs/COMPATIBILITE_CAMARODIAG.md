# Compatibilité des deux projets — lot CD/1 et CDJ/1

Les PR CamaroDiag #70 et CamaroDiagConnectors #6 sont développées de façon coordonnée, chacune dans sa branche active. Aucun accès véhicule n'est autorisé par les protocoles publics de découverte.

- CD/1 : PING (0), CAPABILITIES (1), STATUS (2), puis fermeture. Réponses canoniques, longueur bornée, CRC32 et séquence vérifiés ; pas de repli ASCII.
- CDJ/1 : enregistrement hors ligne de 64 octets. Magie CDJ, version 1, étape, trois octets réservés nuls, séquence uint32 LE, transaction 16 octets, SHA-256 manifeste 32 octets, CRC32 LE sur les 60 premiers octets.
- Le vecteur fixe de test ERASE_INTENT/1 est `43444a0102000000010000000102030405060708090a0b0c0d0e0f10202122232425262728292a2b2c2d2e2f303132333435363738393a3b3c3d3e3fa75e21b6`. Il doit être interprété comme récupération requise dans les deux projets. Ce vecteur synthétique ne contient aucune donnée véhicule.
- Une séquence impossible ou une identité différente ne peut jamais autoriser une reprise. Aucun état importé n'autorise une écriture.
- Le CRC n'est pas une authentification. La future récupération en ligne exige un transport authentifié, une transaction et un profil exacts, une alimentation qualifiée et un état local vérifié ; aucun opcode USB de lecture du journal n'existe encore.
- Les images ECU restent au format constructeur, sans enveloppe cryptographique arbitraire.

Validation de fin du lot : tests natifs C++, Python, Java/Kotlin, Windows et builds des deux firmwares ; recette USB sur carte isolée distincte des tests logiciels. Ne pas fusionner tant que les critères de la PR concernée ne sont pas validés.

## ISO-TP CAN FD (analyse passive)
Le décodeur commun accepte maintenant explicitement CAN classique ou CAN FD, tailles de données CAN FD valides 12/16/20/24/32/48/64 octets, SF avec longueur étendue et FF/CF jusqu'à 4095 octets. Mélange des formats ignoré ; trames mal formées du canal choisi bloquent le décodeur. Pas d'adressage étendu, de longues FF 32 bits, de FlowControl envoyé ni de liaison physique active. Vecteurs C++ synthétiques ; référence de format ISO 15765-2:2024. Ce développement ne qualifie aucune VCI ni application OEM.
