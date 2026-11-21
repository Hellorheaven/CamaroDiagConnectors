# Protocole expérimental USB

Le firmware ESP32-S3 **actuel** écoute un port série ASCII 115200 bauds, avec lignes limitées à 96 caractères.

| Requête | Réponse |
|---|---|
| `PING\n` | `PONG CamaroDiagConnectors 0.1.0` |
| `CAPS\n` | `CAPS hs_can=disabled sw_can=disabled eeprom_read=disabled eeprom_write=disabled ecu_flash=disabled j2534=disabled` |
| `STATUS\n` | `STATUS mode=prototype write=disabled` |
| Autre | `ERR UNSUPPORTED` |

Aucun opcode d'accès à la mémoire ou au bus du véhicule n'est implémenté.

Le **framing binaire défini côté Python est un modèle hors ligne uniquement**, incompatible avec ce firmware ASCII. Format de simulation : magic `CD`, version sur un octet, opcode sur un octet, séquence uint16 LE, longueur uint16 LE, payload, CRC32 LE. Seuls PING, CAPABILITIES et STATUS existent. À développer avant déploiement : négociation de version, timeouts, contrôle de flux, authentification, refus des commandes destructives non autorisées et arrêt sécurisé.

## Validation des réponses côté hôte

Le client Python de découverte accepte uniquement une réponse ASCII imprimable terminée par LF ou CRLF, au plus 256 octets. Il rejette les trames partielles, les réponses concaténées, les caractères de contrôle (notamment NUL, TAB, ESC et DEL), les préfixes inattendus et les capacités inconnues. La réponse `PING` doit correspondre exactement à l'identité et à la version de firmware `PONG CamaroDiagConnectors 0.1.0` ; tout suffixe, version inconnue ou espace final est rejeté (la découverte ne constitue pas une authentification cryptographique). Les commandes restent limitées à `PING`, `CAPS` et `STATUS`. Ces protections sont des contrôles logiciels testés sur hôte ; elles ne constituent pas une validation sur carte réelle, ni une prise en charge CAN, EEPROM ou J2534.

La méthode hôte `verify_read_only()` interroge maintenant **PING en premier**, puis **CAPS**, puis **STATUS**. Une identité/version non conforme arrête la découverte avant toute autre requête. Cette vérification ne prouve ni l'authenticité cryptographique du périphérique ni sa sécurité électrique ; aucun accès CAN/EEPROM n'est autorisé.
