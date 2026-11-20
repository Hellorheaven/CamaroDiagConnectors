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
