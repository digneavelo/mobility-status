# mobility-status

Project visant à créer une Umap sur le réseau cyclable dignois.

## Principe

Les photos sont importées dans [Panoramax](https://panoramax.openstreetmap.fr/)
(compte « lyse »), puis exportées automatiquement en GeoJSON
(`mes_photos.geojson`) par [`panoramax_export.py`](panoramax_export.py).

Un [workflow GitHub Actions](.github/workflows/update-photos.yml) régénère le
fichier chaque jour à 4h du matin (UTC) et le commite, de sorte que l'URL
ci-dessous serve toujours des données à jour :

```
https://raw.githubusercontent.com/digneavelo/mobility-status/main/mes_photos.geojson
```

Cette URL est à utiliser dans uMap comme calque de « données distantes »
(format geojson, option « dynamique » cochée).

## Annotations manuelles (couleur et catégorie)

Le fichier [`annotations.json`](annotations.json) permet d'ajouter, pour chaque
photo, deux informations :

- `couleur` : `vert`, `jaune`, `orange`, `rouge` ou `violet`
- `categorie` : `infrastructure`, `securite` ou `stationnement`

Chaque clé est l'identifiant de la photo (propriété `id` dans
`mes_photos.geojson`) :

```json
{
  "64dd33db-ebe2-4260-83a5-c063a5887727": {
    "couleur": "orange",
    "categorie": "securite"
  }
}
```

Ces annotations sont fusionnées dans `mes_photos.geojson` (propriétés `couleur`
et `categorie`) à chaque exécution du script. Pour ajouter ou modifier une
annotation, éditez `annotations.json` et commitez — le prochain passage du
workflow (ou une exécution manuelle) mettra le GeoJSON à jour.

Dans uMap, les valeurs peuvent être utilisées via :

- le **style conditionnel** du calque pour colorer les points selon `couleur` ;
- un champ « catégorie » avec les icônes correspondantes
  (infrastructure → route, sécurité → panneau attention, stationnement →
  parking) via les réglages avancés d'icônes/uMap pictograms.
