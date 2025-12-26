#!/usr/bin/env python3
import json
import re
from pathlib import Path

from shapely.geometry import shape, mapping
from shapely.ops import unary_union

# ---------------- CONFIG ----------------

DATA_DIR = Path("data")
RAW_PROVINCES = DATA_DIR / "fl_geomorphology_provinces_raw.geojson"

# Output files
OUT_KARST_FEATURES = DATA_DIR / "geology_karst_features.geojson"
OUT_LOWLAND_FEATURES = DATA_DIR / "geology_lowland_features.geojson"
OUT_UPLAND_FEATURES = DATA_DIR / "geology_upland_features.geojson"

OUT_KARST_UNION = DATA_DIR / "geology_karst_union.geojson"
OUT_LOWLAND_UNION = DATA_DIR / "geology_lowland_union.geojson"
OUT_UPLAND_UNION = DATA_DIR / "geology_upland_union.geojson"

# Name-based rules (v1: intentionally simple and tweakable)
KARST_RE = re.compile(r"\bkarst\b", re.IGNORECASE)
UPLAND_RE = re.compile(r"\b(ridge|highlands|hills|upland)\b", re.IGNORECASE)

# Lowland / coastal / wetland-ish provinces (you'll likely tweak this after seeing the map)
LOWLAND_PROVINCES = {
    # Coastal lowlands (big veto-ish swaths)
    "Peninsular Coastal Lowlands Province",
    "Panhandle Coastal Lowlands Province",

    # South Florida wetland systems
    "Everglades Province",
    "Big Cypress Province",
    "Ten Thousand Islands Province",
    "Florida Bay Province",

    # Keys / coastal island systems
    "Upper Keys Province",
    "Middle Keys Province",
    "Lower Keys Province",

    # Atlantic side coastal complex (often low + sandy + wet)
    "Atlantic Coastal Complex Province",
    "Sea Islands Province",

    # Other commonly “lowland-ish” named provinces in this atlas
    "Coastal Swamps Province",
    "Coastal Strand Province",
    "Barrier Island Province",
    "Barrier Islands Province",
}

# ---------------- HELPERS ----------------

def norm(s: str) -> str:
    return (s or "").strip()

def load_fc(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")
    with path.open() as f:
        return json.load(f)

def write_fc(path: Path, features: list):
    fc = {"type": "FeatureCollection", "features": features}
    path.write_text(json.dumps(fc))
    print(f"Wrote {path} ({len(features)} features)")

def write_union(path: Path, geoms: list, props: dict):
    if not geoms:
        fc = {"type": "FeatureCollection", "features": []}
        path.write_text(json.dumps(fc))
        print(f"Wrote {path} (EMPTY)")
        return

    u = unary_union(geoms)
    feat = {
        "type": "Feature",
        "properties": props,
        "geometry": mapping(u),
    }
    fc = {"type": "FeatureCollection", "features": [feat]}
    path.write_text(json.dumps(fc))
    print(f"Wrote {path} (union)")

def province_name(feature: dict) -> str:
    # Primary field in your sample: PROVINCE
    props = feature.get("properties", {}) or {}
    return norm(props.get("PROVINCE"))

# ---------------- MAIN ----------------

def main():
    DATA_DIR.mkdir(exist_ok=True)

    provinces = load_fc(RAW_PROVINCES)
    feats = provinces.get("features", [])
    print(f"Loaded {RAW_PROVINCES} ({len(feats)} features)")

    karst_features = []
    lowland_features = []
    upland_features = []

    karst_geoms = []
    lowland_geoms = []
    upland_geoms = []

    # Classify
    for f in feats:
        name = province_name(f)
        if not name:
            continue

        geom = f.get("geometry")
        if not geom:
            continue

        g = shape(geom)

        # Buckets are not mutually exclusive by default,
        # but we usually *want* one province to land in one bucket.
        # We'll prioritize: LOWLAND > KARST > UPLAND.
        if name in LOWLAND_PROVINCES:
            lowland_features.append(f)
            lowland_geoms.append(g)
            continue

        if KARST_RE.search(name):
            karst_features.append(f)
            karst_geoms.append(g)
            continue

        if UPLAND_RE.search(name):
            upland_features.append(f)
            upland_geoms.append(g)
            continue

    # Write debug feature layers
    write_fc(OUT_KARST_FEATURES, karst_features)
    write_fc(OUT_LOWLAND_FEATURES, lowland_features)
    write_fc(OUT_UPLAND_FEATURES, upland_features)

    # Write union layers (fast overlays + later intersections)
    write_union(OUT_KARST_UNION, karst_geoms, {"zone": "karst_caution"})
    write_union(OUT_LOWLAND_UNION, lowland_geoms, {"zone": "lowland_coastal_nogo"})
    write_union(OUT_UPLAND_UNION, upland_geoms, {"zone": "upland_ridge_candidate"})

    # Quick counts so you know if you're missing expected categories
    print("\nCounts:")
    print(f"  Karst features:   {len(karst_features)}")
    print(f"  Lowland features: {len(lowland_features)}")
    print(f"  Upland features:  {len(upland_features)}")
    print("\nDone.")

if __name__ == "__main__":
    main()