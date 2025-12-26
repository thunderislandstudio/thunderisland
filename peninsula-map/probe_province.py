#!/usr/bin/env python3
import json
from shapely.geometry import shape, Point

RAW = "data/fl_geomorphology_provinces_raw.geojson"

# ---- Pick a point you care about (lon, lat)
# Kissimmee Prairie Preserve-ish
POINTS = [
    ("Kissimmee Prairie (approx)", -81.05, 27.67),
    # Add more probes if you want:
    # ("North of Prairie", -81.05, 27.80),
    # ("South of Prairie", -81.05, 27.55),
]

def main():
    data = json.load(open(RAW))
    feats = data.get("features", [])

    for label, lon, lat in POINTS:
        pt = Point(lon, lat)
        hit = None

        for f in feats:
            g = shape(f["geometry"])
            if g.contains(pt):
                p = f.get("properties", {}) or {}
                hit = (p.get("DISTRICT", ""), p.get("PROVINCE", ""))
                break

        print(f"\n{label}: ({lat}, {lon})")
        if hit:
            print(f"  DISTRICT: {hit[0]}")
            print(f"  PROVINCE: {hit[1]}")
        else:
            print("  No containing polygon found (nudge coordinates slightly).")

if __name__ == "__main__":
    main()