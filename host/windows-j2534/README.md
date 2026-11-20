# Windows J2534 — non implémenté

Cible : une DLL Pass-Thru Windows 32/64 bits respectant les versions et extensions SAE J2534 réellement retenues, avec `PassThruOpen`, `PassThruConnect`, `PassThruReadMsgs`, `PassThruWriteMsgs`, filtres et ISO 15765. Tester d'abord sur simulateur.

Le protocole USB ASCII M0 n'est **pas** un pilote J2534. Une DLL qui compile ne prouve pas la compatibilité SPS2/GDS2 ; certains outils OEM dépendent aussi d'autres interfaces/API (par exemple D-PDU), licences ou procédures constructeur. Les écritures ECU restent désactivées en absence de matériel, driver et récupération vérifiés.
