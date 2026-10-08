# mobility-status

Project aimed at creating a uMap of the cycling network in Digne-les-Bains.

## How it works

Photos are uploaded to [Panoramax](https://panoramax.openstreetmap.fr/)
("lyse" account), then automatically exported as GeoJSON
(`mes_photos.geojson`) by [`panoramax_export.py`](panoramax_export.py).

A [GitHub Actions workflow](.github/workflows/update-photos.yml) regenerates
the file every day at 4 AM (UTC) and commits it, so the URL below always
serves up-to-date data:

```
https://raw.githubusercontent.com/digneavelo/mobility-status/main/mes_photos.geojson
```

Use this URL in uMap as a "remote data" layer (geojson format, "dynamic"
option checked).

## Manual annotations (color and category)

The [`annotations.json`](annotations.json) file lets you add two pieces of
information to each photo:

- `color`: `green`, `yellow`, `orange`, `red` or `purple`
- `category`: `infrastructure`, `security` or `parking`

Each key is the photo ID (the `id` property in `mes_photos.geojson`):

```json
{
  "64dd33db-ebe2-4260-83a5-c063a5887727": {
    "color": "orange",
    "category": "security"
  }
}
```

These annotations are merged into `mes_photos.geojson` (`color` and `category`
properties) on every run of the script. To add or change an annotation, edit
`annotations.json` and commit — the next workflow run (or a manual run) will
update the GeoJSON file.

In uMap, these values can be used with the layer's **conditional style rules**:

- marker **color** based on the `color` property;
- marker **pictogram** based on the `category` property
  (infrastructure → road icon, security → warning sign icon,
  parking → parking icon).
