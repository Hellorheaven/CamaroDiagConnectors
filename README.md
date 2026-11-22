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
Le firmware ESP32-S3 fournit uniquement `PING`, `CAPS` et `STATUS`, en variantes ASCII et binaire distinctes ; toutes les fonctions véhicule/écriture restent désactivées. Le prototype STM32G474 démarre avec signaux cibles inactifs et diagnostic ST-LINK. Le client Python propose découverte USB, sauvegardes et planification de patches hors ligne, transport TLS 1.3 de référence sur socket et journal de programmation de simulation. Le client Android USB Host CDC est un prototype de découverte autonome, à qualifier sur carte réelle. Aucun accès physique ECU, SPI interprocesseur ou CAN réel n'est activé.

| Dossier | Contenu |
|---|---|
| `firmware/esp32s3` | Prototype série USB en lecture seule |
| `host/python` | Client de découverte, simulateurs et tests |
| `host/windows-j2534` | Spécification du pilote Windows futur |
| `host/android` | Client natif de découverte USB CDC, non intégré à l'application |
| `firmware/stm32g4` | Prototype Nucleo G474RE isolé |
| `firmware/shared` | Contrat interprocesseur et réassemblage ISO-TP passif, hors matériel |
| `hardware` | Contraintes électriques / transceivers / connectique |
| `docs` | Architecture, protocole, risques et validation |

## Tests logiciels
```shell
cd host/python
python -m unittest discover -s tests -v
```
Voir [découverte USB binaire](docs/user/usb-binary-discovery.md) et [Android](host/android/README.md). Pour tenter la découverte USB sur une carte ESP32-S3 **isolée du véhicule** : flasher `firmware/esp32s3` avec PlatformIO (compilation et qualification physique distinctes), installer `pyserial`, puis `python -m camarodiagconnectors --port COM5 ping`.

## Gouvernance
Projet indépendant de CamaroDiag. Coordination et exigences : [CamaroDiag #69](https://github.com/Hellorheaven/CamaroDiag/issues/69).

Aucune licence open source choisie pour le moment. Ne pas publier de dumps, clés ou images firmware GM ni des données véhicules privées.


## Outil de sauvegarde et de patch hors ligne

Les commandes suivantes travaillent **sur des fichiers déjà présents sur le PC**, jamais directement sur une EEPROM ou un ECU :

```bash
cd host/python
python -m camarodiagconnectors.offline_cli backup --target 24LC256 --capacity 32768 --input original.bin --output-prefix sauvegarde
python -m camarodiagconnectors.offline_cli verify --prefix sauvegarde
python -m camarodiagconnectors.offline_cli plan --target 24LC256 --technology i2c_eeprom --page-size 64 --input original.bin --patch 0x10:01 --proposed-output simulation.bin
```

`backup` crée `sauvegarde.bin` et `sauvegarde.json` en exclusivité (jamais d'écrasement). `verify` contrôle intégrité et couverture déclarée. `plan` indique les pages/secteurs qui changeraient, refuse les régions protégées et préserve tous les octets voisins de l'image. **Ni le fichier candidat ni le manifeste ne constituent une preuve de compatibilité matérielle ou une autorisation d'écriture.**

## Documentation de raccordement

[Guide générique des alimentations, broches et modes de raccordement](docs/user/wiring/README.md) · [Catalogue des fiches par calculateur](docs/user/wiring/ecu/README.md).

USB 5 V prioritaire pour la logique du boîtier ; alimentation externe stabilisée réservée à la cible BENCH, via protections. Une source auxiliaire maintenue peut être requise pour une opération critique. Les fiches documentaires ne constituent pas une qualification physique. Respecter les variantes ECU et les spécifications constructeur.

## Limites de sécurité

La découverte ASCII/binaire ne prouve pas l'identité de la carte. Le TLS mutuel de simulation ne s'applique pas encore au transport USB. Le journal logiciel ne garantit pas la restauration d'un calculateur et ne doit pas servir à déclencher une écriture. Aucun mode de programmation ne peut être activé sans qualification par cible, alimentation et route (#8, #9, #10).
