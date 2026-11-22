# Feuille de route historique

Toutes les évolutions, y compris matérielles, sont désormais suivies dans [CamaroDiag #80](https://github.com/Hellorheaven/CamaroDiag/issues/80) et [le module connectors](https://github.com/Hellorheaven/CamaroDiag/tree/main/connectors). Ancienne feuille de route :

# Feuille de route matérielle

Les travaux de firmware, pilotes, CI, applications et compatibilité logicielle sont suivis dans [CamaroDiag #80](https://github.com/Hellorheaven/CamaroDiag/issues/80), avec les issues migrées #81–#93.

- [ ] Inventaire des composants, références réelles ESP32/STM32 et extension mémoire.
- [ ] Schémas électriques, alimentation protégée, transceivers, isolation, multiplexage et Vref.
- [ ] PCB, nomenclature, connecteurs et adaptateurs CAN/CAN FD/SWCAN/K-Line, I²C/SPI/Microwire et accès MCU, selon validation.
- [ ] Revue ERC/DRC et plan de qualification électrique.
- [ ] Faisceaux et fiches ECU par référence et variante, avec photo et preuve de brochage.
- [ ] Réalisation des prototypes et compte rendus de banc, tests de protections et coupures.

Toute validation doit préciser la révision de PCB, MCU, référence composant, version du firmware issue de CamaroDiag et résultats mesurés. Les projets de schéma ne sont pas des cartes qualifiées. Voir [validation](docs/HARDWARE_VALIDATION.md).
