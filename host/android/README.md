# Android CamaroDiag — intégration future

Un transport USB natif, versionné et documenté, est privilégié pour l'app Android. Le périphérique doit annoncer ses capacités testées ; un ECU ou un module non pris en charge reste visible, grisé et accompagné d'une explication. Les actions destructives ne sont jamais activées sur la seule réponse de découverte.

À faire : négociation protocole/firmware, permissions USB Android 10–16, logs structurés, isolation par véhicule/VIN, reprise et erreurs de transport, tests. Aucune modification dans la PR #54 n'est requise pour l'initialisation de ce dépôt.
