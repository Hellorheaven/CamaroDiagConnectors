# Matériel — cahier des charges, pas de PCB validé

1. Un ESP32-S3 pour USB et contrôle (et éventuellement Wi-Fi/BLE pour diagnostic non destructif).
2. Un contrôleur temps réel optionnel (STM32G4 selon référence et capacité CAN/FDCAN vérifiées).
3. Un transceiver HS CAN + protection automobile pour DLC 6/14, et un transceiver **SAE J2411 Single-Wire CAN** distinct pour DLC 1, sans connexions directes aux GPIO.
4. Alimentation véhicule résistante aux transitoires, inversion, surtension et ESD.
5. **Connecteur de banc séparé** avec alimentation à tension sélectionnée/mesurée et interverrouillage ; adaptateurs I²C 24xx, SPI 25xx, Microwire 93xx et NOR SPI, socket ZIF/clip validé.
6. Adaptateurs MCU internes BOOT/BDM/Nexus/JTAG en option, selon référence exacte ; ne pas assimiler un MCU à une EEPROM SPI.

À produire : schéma, BOM avec fiches constructeur, PCB, mesure thermique/transitoires, tests de compatibilité et prototype de banc. **Ne pas raccorder un prototype non validé à un calculateur réel.**
