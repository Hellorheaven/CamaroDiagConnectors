# Architecture candidate

```text
Android CamaroDiag    Windows J2534 (futur)    Banc / CLI
        \                     |                    /
                 USB série / binaire (futur)
                            |
                         ESP32-S3
                            |
                 MCU temps réel (option)
                   /        |         \
              HS CAN     SWCAN       Port de banc
              6/14       SAE J2411   EEPROM/NOR
```

**Schéma de principe uniquement.** Vérifier les fonctionnalités de chaque référence STM32/ESP32 avant de figer le PCB. La carte de développement ESP32-S3 ne doit être branchée sur aucun réseau automobile sans transceiver et protection conçus pour cet usage.

Les transceivers HS CAN et SWCAN sont distincts. Pour CAN FD, prévoir un contrôleur et transceiver compatibles seulement après justification de la variante véhicule. J2534 est une API côté Windows, pas un niveau physique automatiquement compatible avec tous les logiciels GM. Le programmateur EEPROM possède son propre connecteur et une alimentation séparée/interverrouillée ; l'accès BOOT/Nexus aux MCU internes demande un adaptateur et un pilote différents.

## Modes
- **Prototype M0** : découverte PING/CAPS/STATUS sans action.
- **M1** : capture passive après revue PCB et validation sur simulateur.
- **M2** : lecture et éventuelle écriture de puces d'essai via pilotes adaptés, après sécurité matérielle.
- **M3** : J2534 et protocoles Windows/Android après tests.
- **M4** : banc ECU, sauvegarde et récupération après validation matérielle.

Tous les modules non supportés doivent demeurer visibles mais désactivés avec motif explicite. Le matériel, firmware, protocole et méthodes d'accès sont des dimensions séparées.
