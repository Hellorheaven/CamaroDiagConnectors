# Vérifier le boîtier USB — prototype binaire

La variante expérimentale cible uniquement l'ESP32-S3 DevKit isolé : aucun faisceau ECU, alimentation automobile ou mémoire connecté. Le firmware normal reste ASCII. Aucune commande CAN, EEPROM, flash ou J2534 n'est disponible dans les deux variantes.

## Démarrage
Compiler la variante binaire avec PlatformIO :
```sh
pio run -d firmware/esp32s3 -e esp32s3-binary-discovery
```
Après flash et reset contrôlés sur carte isolée, installer pyserial et lancer depuis host/python :
```sh
python -m camarodiagconnectors --port COM5 --binary verify
```
Adapter le port. Le client vérifie PING, CAPABILITIES, STATUS dans cet ordre. Toute anomalie (CRC, longueur, séquence, réponse inattendue) ferme la session ; redémarrer uniquement le prototype isolé avant une nouvelle session. Aucune rétrogradation automatique vers ASCII.

Le CRC32 et l'ordre des séquences détectent certaines erreurs de transfert, mais ne prouvent pas l'identité et ne constituent pas de chiffrement. L'authentification mutuelle reste à implémenter (#8). Aucun accès physique ni programmation autorisée. Le modèle anti-brick #9 reste une simulation. La recette physique USB reste à effectuer (#1).
