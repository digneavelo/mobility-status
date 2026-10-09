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
OUTPUT_GEOJSON = "data.geojson"
ANNOTATIONS_FILE = "annotations.json"

VALID_CATEGORIES = {"infrastructure", "security", "signs", "parking"}
VALID_COLORS = {"green", "yellow", "orange", "red", "purple", "pink"}

# The JWT token is read from the PANORAMAX_JWT environment variable
# (public Panoramax data does not require authentication; the token is
#  only needed if your sequences are private).
JWT_TOKEN = os.environ.get("PANORAMAX_JWT", "")
HEADERS = {"Authorization": f"Bearer {JWT_TOKEN}"} if JWT_TOKEN else {}


# ─────────────────────────────────────────────
# Manual annotations (color and category per photo)
# ─────────────────────────────────────────────
def load_annotations():
    """
    Loads manual annotations from annotations.json.
    Expected format:
    {
      "<photo_id>": {"color": "orange", "category": "security"},
      ...
    }
    Returns an empty dict if the file does not exist.
    """
    if not os.path.exists(ANNOTATIONS_FILE):
        return {}
    with open(ANNOTATIONS_FILE, encoding="utf-8") as f:
        data = json.load(f)

    annotations = {}
    for pic_id, props in data.items():
        color = props.get("color")
        category = props.get("category")
        annotations[pic_id] = {
            "color": color if color in VALID_COLORS else None,
            "category": category if category in VALID_CATEGORIES else None,
        }
    return annotations


# ─────────────────────────────────────────────
# Step 1: Fetch the list of sequences
# ─────────────────────────────────────────────
def get_user_sequences():
    """
    Fetches all sequences from /api/users/<uuid>/collection.
    Returns a list of dicts {url, title}.
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
# Step 2: Fetch the title of a sequence
# ─────────────────────────────────────────────
def get_sequence_title(seq_url):
    """
    Fetches the title of a sequence.
    """
    resp = requests.get(seq_url, headers=HEADERS)
    if resp.status_code == 200:
        return resp.json().get("title")
    return None


# ─────────────────────────────────────────────
# Step 3: Fetch all photos of a sequence
# ─────────────────────────────────────────────
def get_sequence_photos(seq_url):
    """
    Fetches all photos of a sequence with pagination.
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
# Step 4: Extract photo information
# ─────────────────────────────────────────────
def extract_photo_feature(feature, sequence_title, annotations):
    """
    Extracts the location, sequence name, photo URL and manual
    annotations (color, category) as a GeoJSON Feature.
    """
    pic_id = feature["id"]
    geom = feature.get("geometry", {})
    coords = geom.get("coordinates", [None, None])

    # Image URL from the assets
    assets = feature.get("assets", {})
    if "sd" in assets:
        image_url = assets["sd"]["href"]
    elif "hd" in assets:
        image_url = assets["hd"]["href"]
    else:
        image_url = None

    if coords[0] is None or coords[1] is None:
        return None

    props = {
        "id": pic_id,
        "sequence_title": sequence_title,
        "image_url": image_url,
    }

    annotation = annotations.get(pic_id, {})
    props["color"] = annotation.get("color")
    props["category"] = annotation.get("category")

    return {
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": [coords[0], coords[1]],
        },
        "properties": props,
    }


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────
def main():
    print("🔍 Fetching your sequences...")

    annotations = load_annotations()
    print(f"   🎨 {len(annotations)} annotations loaded\n")

    sequences = get_user_sequences()
    print(f"   📁 {len(sequences)} sequences found\n")

    features = []
    for i, seq in enumerate(sequences):
        print(f"  📸 Sequence {i+1}/{len(sequences)}...")

        # Sequence title
        seq["title"] = get_sequence_title(seq["url"])
        print(f"     → {seq['title']}")

        # Sequence photos
        photos = get_sequence_photos(seq["url"])
        for feature in photos:
            photo_feature = extract_photo_feature(feature, seq["title"], annotations)
            if photo_feature:
                features.append(photo_feature)
        print(f"     → {len(photos)} photos")

    print(f"\n✅ Total: {len(features)} photos")

    # Build the GeoJSON FeatureCollection
    geojson = {
        "type": "FeatureCollection",
        "features": features,
    }

    # Save
    with open(OUTPUT_GEOJSON, "w", encoding="utf-8") as f:
        json.dump(geojson, f, ensure_ascii=False, indent=2)
    print(f"💾 File saved: {OUTPUT_GEOJSON}")

    return 0 if features else 1


if __name__ == "__main__":
    sys.exit(main())
