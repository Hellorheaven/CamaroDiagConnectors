# CamaroDiagConnectors — matériel

Ce dépôt est dédié **exclusivement au matériel** du boîtier CamaroDiagConnectors : architecture électrique, schémas, PCB, nomenclatures, connectique, faisceaux, alimentation, brochages et validation physique.

Le code des firmwares ESP32-S3 et STM32, bibliothèques hôtes Android/Windows/Python, pilotes, tests et CI a été centralisé dans [CamaroDiag](https://github.com/Hellorheaven/CamaroDiag) sous `connectors/`. La [PR #70](https://github.com/Hellorheaven/CamaroDiag/pull/70) contient l'import ; [issue #80](https://github.com/Hellorheaven/CamaroDiag/issues/80) centralise la migration et le tableau des 13 issues. Ne plus développer de code de firmware ici. L'ancien code reste dans l'historique : [révision importée](https://github.com/Hellorheaven/CamaroDiagConnectors/tree/81b578571a56c8d96b46932f24c55f34aacd1a65).

## Documentation matérielle
- [Architecture matérielle](docs/ARCHITECTURE.md)
- [Interconnexion Rev A](hardware/rev-a-interconnect.md)
- [Prototype banc Rev A0](hardware/rev-a0-bench.md)
- [Validation électrique et matérielle](docs/HARDWARE_VALIDATION.md)
- [Guide des alimentations et raccordements](docs/user/wiring/README.md)
- [Catalogue de fiches ECU](docs/user/wiring/ecu/README.md)
- [Feuille de route matérielle](ROADMAP.md)

Les schémas restent des propositions, non qualifiées. Aucune carte nue reliée directement à un ECU, un réseau automobile ou une puce. Aucun PCB ni Gerber ne doit être déclaré validé sans revue des références, ERC/DRC et essais physiques. Toutes les exigences logicielles et matérielles sont suivies dans les issues CamaroDiag #81–#93 ; les anciennes issues sont historiques. La PR #6 du présent dépôt ne sert qu'à la bascule de documentation matérielle, sans code actif. Ne pas supprimer l'historique.
