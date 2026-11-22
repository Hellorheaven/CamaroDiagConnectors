# Rev A0 — prototype logique + CAN simulateur (22/11/2026)

Aucun raccordement véhicule/ECU/puce. Pas de PCB ni ERC validés. Le schéma électrique de développement est fourni séparément dans le dossier KiCad local, à importer et revoir avant fabrication.

## Interconnexion proposée
ESP32-S3-DevKitC-1 v1.1 (N8R8) -> TXU0304PWR TSSOP14 -> NUCLEO-G474RE MB1367.
| Signal | ESP32 | U1 A/B | STM32 |
|---|---|---|---|
| SCK | J2.18 GPIO12 | 2/13 | PA5 D13 CN5.6 |
| MOSI | J2.17 GPIO11 | 3/12 | PA7 D11 CN5.4 |
| CS | J2.16 GPIO10 | 4/11 | PB6 D10 CN5.3 |
| MISO | J2.19 GPIO13 | 5/10 | PA6 D12 CN5.5 |
| OE | J2.4 GPIO4 | 8 | 10k vers GND |
| VCCA | J2.1 3V3 | 1 | séparé de VCCB |
| VCCB | — | 14 | 3V3 Nucleo |
| GND | J2.22 | 7 | GND commun |
| NC | — | 6,9 | NC |
CS côté STM tiré à 3V3 par 10k. 100nF + 1uF pour chaque rail à proximité U1. Chaque carte alimentée séparément selon son manuel, ne pas relier leurs rails. TXU0304 présente haute impédance quand un rail manque ; pas d'isolation galvanique. GPIO4 OE non utilisé par firmware actuel. SPI esclave NSS logiciel PB6 à valider.
## CAN simulateur
TCAN1042VDRQ1 : pin1 TXD tirée VIO via 10k, pin2 GND, pin3 5V, pin4 RXD PA11/FDCAN1_RX, pin5 VIO 3V3, pin6 CANL, pin7 CANH, pin8 STB tirée VIO via 10k. PA12/FDCAN1_TX et PA8/STB uniquement via liens non montés. 100nF par rail et 4,7uF sur 5V ; 120 ohms non monté (selon topologie simulateur). Veille par défaut, pas d'écoute complète ni transmission. Confirmer broches Morpho sur révision réelle.
## Budget
Prix indicatifs HT DigiKey : ESP32 13,32 € (hors stock), Nucleo 17,87 €, TXU0304 0,85 €, TCAN1042V 1,91 €. Passifs, connecteurs et adaptation montage estimés 15,20 € ; total A0 49,15 € HT hors port. NCV7356D1R2G 2,16 € HT non inclus. Boîtier final, alimentation et autres interfaces à chiffrer.
## Extensions obligatoires
SWCAN NCV7356, alimentation automobile protégée / mesures V/I / superviseur, faisceau BENCH par ECU, adaptateurs MCU et mémoire avec Vref contrôlée, isolation et limitation courant. Aucun raccordement tant que schémas détaillés et qualification #2/#3/#5/#8/#9 non terminés. Firmware signé du boîtier uniquement ; trames et fichiers ECU conformes OEM. Pas de Gerber avant revue, ERC/DRC et routage ; aucune promesse anti-brick absolue.
## Sources
- https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32s3/esp32-s3-devkitc-1/user_guide_v1.1.html
- https://www.st.com/resource/en/user_manual/um2505-stm32g4-nucleo64-boards-mb1367-stmicroelectronics.pdf
- https://www.st.com/resource/en/schematic_pack/mb1367-g474re-c05_schematic.pdf
- https://www.ti.com/product/TXU0304
- https://www.ti.com/product/TCAN1042V-Q1
- https://www.onsemi.com/download/data-sheet/pdf/ncv7356-d.pdf
