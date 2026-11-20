# CamaroDiagConnectors

Projet matériel et logiciel indépendant pour **[CamaroDiag](https://github.com/Hellorheaven/CamaroDiag)** : interface diagnostic Chevrolet Camaro Gen 5/Gen 6, passerelle Windows SAE J2534 et programmateur EEPROM/flash sur banc.

> **Prototype initial non validé sur matériel.** Aucun pilotage CAN, aucune lecture/écriture EEPROM, aucun pilote J2534 ni programmation ECU réelle n'est implémenté. Ne connecter ce firmware ni à un véhicule, ni à une puce ou à une alimentation automobile.

## Objectifs
- **Véhicule** : HS CAN (DLC 6/14), GM Single-Wire CAN/SAE J2411 (DLC 1) et autres réseaux *après vérification par modèle et année*.
- **Windows** : DLL Pass-Thru J2534 à implémenter ; USB câblé pour les opérations critiques.
- **Android** : protocole USB natif CamaroDiag ; Wi-Fi/BLE envisagés uniquement pour les opérations non destructives.
- **Banc** : EEPROM externes I²C 24xx, SPI 25xx, Microwire 93xx, NOR SPI et adaptateurs spécifiques, lecture double, sauvegarde, comparaison, écriture ciblée et relecture *après validation*.
- **MCU internes** : méthodes BOOT/BDM/Nexus/JTAG distinctes des EEPROM externes ; ne pas supposer de compatibilité à partir du nom d'un ECU.

## État actuel
Le firmware ESP32-S3 fournit uniquement `PING`, `CAPS` et `STATUS` ; `CAPS` déclare toutes les fonctions véhicule/écriture désactivées. Le client Python fournit analyse hors ligne, format de trame expérimental, sauvegardes de fichiers et planification de patches sans accès matériel.

| Dossier | Contenu |
|---|---|
| `firmware/esp32s3` | Prototype série USB en lecture seule |
| `host/python` | Client de découverte, simulateurs et tests |
| `host/windows-j2534` | Spécification du pilote Windows futur |
| `host/android` | Plan d'intégration dans CamaroDiag Android |
| `hardware` | Contraintes électriques / transceivers / connectique |
| `docs` | Architecture, protocole, risques et validation |

## Tests logiciels
```shell
cd host/python
python -m unittest discover -s tests -v
```
Pour tenter la découverte USB sur une carte ESP32-S3 **isolée du véhicule** : flasher `firmware/esp32s3` avec PlatformIO (build non validé à ce stade), installer `pyserial`, puis `python -m camarodiagconnectors --port COM5 ping`.

## Gouvernance
Projet distinct de la [PR CamaroDiag #54](https://github.com/Hellorheaven/CamaroDiag/pull/54), qui ne doit pas être ralentie. Coordination et exigences : [CamaroDiag #69](https://github.com/Hellorheaven/CamaroDiag/issues/69).

Aucune licence open source choisie pour le moment. Ne pas publier de dumps, clés ou images firmware GM ni des données véhicules privées.
