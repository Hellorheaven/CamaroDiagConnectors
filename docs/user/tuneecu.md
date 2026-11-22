# TuneECU — cible d'interopérabilité (non disponible)

CamaroDiagConnectors prévoit une interface indépendante pour TuneECU Android. Pas de compatibilité annoncée à ce stade.

| Mode | Objectif | État |
|---|---|---|
| USB FTDI KKL + K-Line/KWP2000 | Motos et ECU compatibles par câble | À développer et qualifier |
| Bluetooth AT / ELM | Diagnostic selon liste officielle | À développer et qualifier |
| Bluetooth avancé | Fonctions spécifiques acceptées par TuneECU | À étudier avec l'éditeur, pas de garantie |
| RS232 Walbro | Faisceaux et convertisseur dédiés | Étude |
| USB CD/1 natif | Découverte CamaroDiag seulement | Prototype isolé |

L'ESP32-S3 ne dispose pas de Bluetooth Classic SPP. Un module additionnel est nécessaire si ce profil est requis. Les versions de TuneECU et les modèles compatibles doivent être contrôlés dans la documentation officielle. Ne pas simuler frauduleusement une identité FTDI, OBDLink ou UniCarScan.

Le modèle logiciel de contrôle d'interface bloque les accès concurrents, les opérations en récupération, et toutes les commandes non strictement allowlistées sur les futures voies legacy. Il n'active aucune sortie. Une programmation par interface tierce brute doit rester bloquée tant qu'une qualification spécifique et la maîtrise anti-brick ne sont pas acquises.

Références : [TuneECU Android](https://tuneecu.net/TuneECU_Fr/android.html), [opérations](https://tuneecu.net/TuneECU_Fr/tasks.html), [ESP32-S3 Bluetooth](https://docs.espressif.com/projects/esp-idf/en/stable/esp32s3/api-guides/ble/overview.html).
