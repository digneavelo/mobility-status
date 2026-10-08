import json
import os
import sys

import requests

# ─────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────
API_BASE = "https://panoramax.openstreetmap.fr/api"
# USER_UUID = "6bde391d-7dd7-4811-9276-d6bb39c1aa3c"  # digneavelo
USER_UUID = "c20350b4-0f74-40e4-bd40-f89ab8f8c5f6"    # lyse
OUTPUT_GEOJSON = "mes_photos.geojson"

# Le jeton JWT est lu depuis la variable d'environnement PANORAMAX_JWT
# (les données publiques de Panoramax ne nécessitent pas d'authentification,
#  le jeton sert uniquement si vos séquences sont privées).
JWT_TOKEN = os.environ.get("PANORAMAX_JWT", "")
HEADERS = {"Authorization": f"Bearer {JWT_TOKEN}"} if JWT_TOKEN else {}


# ─────────────────────────────────────────────
# Étape 1 : Récupérer la liste des séquences
# ─────────────────────────────────────────────
def get_user_sequences():
    """
    Récupère toutes les séquences depuis /api/users/<uuid>/collection.
    Retourne une liste de dictionnaires {url, title}.
    """
    sequences = []
    url = f"{API_BASE}/users/{USER_UUID}/collection?limit=100"

    page = 1
    while url:
        print(f"  📄 Page {page}...")
        resp = requests.get(url, headers=HEADERS)
        resp.raise_for_status()
        data = resp.json()

        for link in data.get("links", []):
            if link.get("rel") == "child":
                sequences.append({"url": link["href"], "title": None})

        # Pagination
        url = None
        for link in data.get("links", []):
            if link.get("rel") == "next":
                url = link["href"]
                break

        page += 1

    return sequences


# ─────────────────────────────────────────────
# Étape 2 : Récupérer le titre d'une séquence
# ─────────────────────────────────────────────
def get_sequence_title(seq_url):
    """
    Récupère le titre d'une séquence.
    """
    resp = requests.get(seq_url, headers=HEADERS)
    if resp.status_code == 200:
        return resp.json().get("title")
    return None


# ─────────────────────────────────────────────
# Étape 3 : Récupérer toutes les photos d'une séquence
# ─────────────────────────────────────────────
def get_sequence_photos(seq_url):
    """
    Récupère toutes les photos d'une séquence avec pagination.
    """
    photos = []
    url = seq_url + "/items?limit=1000"

    while url:
        resp = requests.get(url, headers=HEADERS)
        resp.raise_for_status()
        data = resp.json()

        for feature in data.get("features", []):
            photos.append(feature)

        url = None
        for link in data.get("links", []):
            if link.get("rel") == "next":
                url = link["href"]
                break

    return photos


# ─────────────────────────────────────────────
# Étape 4 : Extraire les infos d'une photo
# ─────────────────────────────────────────────
def extract_photo_feature(feature, sequence_title):
    """
    Extrait la localisation, le nom de la séquence et l'URL de la photo
    sous forme de Feature GeoJSON.
    """
    pic_id = feature["id"]
    geom = feature.get("geometry", {})
    coords = geom.get("coordinates", [None, None])

    # URL de l'image depuis les assets
    assets = feature.get("assets", {})
    if "sd" in assets:
        image_url = assets["sd"]["href"]
    elif "hd" in assets:
        image_url = assets["hd"]["href"]
    else:
        image_url = None

    if coords[0] is None or coords[1] is None:
        return None

    return {
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": [coords[0], coords[1]],
        },
        "properties": {
            "id": pic_id,
            "sequence_title": sequence_title,
            "image_url": image_url,
        },
    }


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────
def main():
    print("🔍 Récupération de vos séquences...")

    sequences = get_user_sequences()
    print(f"   📁 {len(sequences)} séquences trouvées\n")

    features = []
    for i, seq in enumerate(sequences):
        print(f"  📸 Séquence {i+1}/{len(sequences)}...")

        # Titre de la séquence
        seq["title"] = get_sequence_title(seq["url"])
        print(f"     → {seq['title']}")

        # Photos de la séquence
        photos = get_sequence_photos(seq["url"])
        for feature in photos:
            photo_feature = extract_photo_feature(feature, seq["title"])
            if photo_feature:
                features.append(photo_feature)
        print(f"     → {len(photos)} photos")

    print(f"\n✅ Total : {len(features)} photos")

    # Création du FeatureCollection GeoJSON
    geojson = {
        "type": "FeatureCollection",
        "features": features,
    }

    # Sauvegarde
    with open(OUTPUT_GEOJSON, "w", encoding="utf-8") as f:
        json.dump(geojson, f, ensure_ascii=False, indent=2)
    print(f"💾 Fichier sauvegardé : {OUTPUT_GEOJSON}")

    return 0 if features else 1


if __name__ == "__main__":
    sys.exit(main())
