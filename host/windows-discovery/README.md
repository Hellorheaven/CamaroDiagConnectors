# Découverte USB native Windows

Uniquement le prototype ESP32-S3 binaire isolé. Aucun J2534, CAN réel ni flash implémenté par cet outil. Après reset du prototype, identifier le port COM dans Windows et lancer `dotnet run --project host/windows-discovery -- --port COM5` en remplaçant COM5. Les contrôles identité textuelle, statut, CRC et ordre n'authentifient pas cryptographiquement le périphérique. Ne pas connecter véhicule ou puce. `--self-test` effectue exclusivement des échanges simulés. .NET 8 requis. Le pilote Pass-Thru reste un lot distinct.
