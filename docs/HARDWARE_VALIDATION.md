# Validation de la carte avant tout ECU

## A. Alimentation
Faire relire le schéma et la nomenclature exacte. Banc isolé, mesurer VCC/VIO, surtensions, inversion, ESD, limitation de courant, redémarrage et watchdog. Aucun bus automobile raccordé à des GPIO directs.

## B. Bus véhicule passifs
Commencer par un simulateur CAN. Transceiver HS CAN, puis transceiver SAE J2411 séparé pour SWCAN. Mesurer horodatage, saturation, trames perdues, wake-up et résistance aux perturbations. Pas de transmission active vers véhicule avant validation dédiée.

## C. EEPROM sacrifiables
Choisir des puces d'essai identifiées : tension, pinout et organisation documentés. Lire deux fois, comparer octet à octet, écrire l'original et son manifeste sans écrasement, planifier un patch par page/secteur, programmer uniquement la puce d'essai, relire indépendamment et vérifier. Simuler coupure en cours d'écriture. Interdire des zones protégées même si seul un octet voisin est modifié dans un secteur.

## D. ECU sur banc
Identifier la référence physique et toutes les régions. Accès BOOT/BDM/Nexus/JTAG distinct d'une EEPROM externe. Tester sur ECU de remplacement après preuve de récupération et stratégie de sauvegarde. Aucun test en véhicule avant validation complète.

**Résultat requis :** preuves mesurées par carte, version PCB, MCU, firmware, composant, protocole, tension, test et rapport. Une simulation logicielle ne permet aucune revendication de compatibilité réelle.
