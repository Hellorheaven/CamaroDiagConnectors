# Feuille de route

**Tous les composants de programmation et de diagnostic avancé restent à développer.** Une validation logicielle ne remplace jamais des essais matériels.

## M0 — Socle (en cours)
- [x] Structure du dépôt séparé, documentation, découverte USB en lecture seule
- [x] Planification de patches et manifestes de sauvegarde **hors ligne**
- [ ] Compilation du firmware ESP32-S3 et validation USB sur carte réelle
- [ ] Protocole binaire versionné et test firmware ↔ hôte

## M1 — Capture automobile passive
- [ ] Matrice par génération, année, VIN/RPO et calculateurs
- [ ] Transceivers séparés HS CAN et GM SWCAN SAE J2411, protections électriques
- [ ] Carte prototype, validation alimentation et banc CAN passif
- [ ] Déconnexions, filtres, latence, horodatage et watchdog

## M2 — Programmateur EEPROM sur banc
- [ ] PCB et connecteur de banc séparés, rails mesurés 1,8/3,3/5 V selon datasheet
- [ ] Supports SOIC/ZIF, protections ESD/courant, isolation et absence de contention
- [ ] Pilotes de lecture 24xx/I²C, 25xx/SPI, 93xx/Microwire, NOR SPI
- [ ] Deux lectures concordantes, sauvegardes immuables et manifeste de couverture
- [ ] Patches par unités physiques, lecture post-écriture et essais sur puces sacrifiables
- [ ] Refuser automatiquement tout composant, tension ou secteur non identifié

## M3 — J2534 Windows et Android
- [ ] DLL Windows Pass-Thru 32/64 bits, API J2534-1 et extensions applicables
- [ ] Tests de conformité J2534 et d'ISO-TP, jamais de compatibilité GM présumée
- [ ] Protocole USB binaire robuste, versionné, CRC, séquences, backpressure
- [ ] Transport Android natif et matrice des capacités vérifiées

## M4 — Programmation ECU interne
- [ ] Identifier références ECU/MCU LFX 2012 sur matériel physique
- [ ] Adaptateurs BOOT/BDM/Nexus/JTAG compatibles avec chaque référence
- [ ] Lecture multi-régions prouvée, comparaison et récupération sur banc
- [ ] Écriture uniquement après sauvegarde/relecture et essais de coupure

## M5 — Gen 5/Gen 6 multi-modules
- [ ] Inventaire BCM/TPMS, EBCM, SDM, IPC, FPCM, HVAC et ECM/TCM selon VIN/RPO
- [ ] Préconditions constructeur, permissions, sécurités, compatibilité démontrée
- [ ] Rapports avant/après et maintien des modes lecture seule quand nécessaire
