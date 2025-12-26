#!/usr/bin/env python3
import json
from pathlib import Path
from urllib.request import urlopen

# Where we’ll save the raw geology data
OUTPUT_DIR = Path("data")
OUTPUT_DIR.mkdir(exist_ok=True)

# Florida Geological Survey – Geomorphology Provinces (statewide polygons)
PROVINCES_URL = (
    "https://ca.dep.state.fl.us/arcgis/rest/services/"
    "OpenData/FGS_PUBLIC/MapServer/11/query"
    "?where=1%3D1"
    "&outFields=*"
    "&returnGeometry=true"
    "&outSR=4326"
    "&f=geojson"
)

def main():
    print("Fetching Florida geomorphology provinces…")

    with urlopen(PROVINCES_URL) as resp:
        provinces = json.loads(resp.read().decode("utf-8"))

    out_path = OUTPUT_DIR / "fl_geomorphology_provinces_raw.geojson"
    with out_path.open("w") as f:
        json.dump(provinces, f)

    print(f"Wrote {out_path}")
    print(f"Feature count: {len(provinces.get('features', []))}")

if __name__ == "__main__":
    main()