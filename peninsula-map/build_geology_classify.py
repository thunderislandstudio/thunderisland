#!/usr/bin/env python3
import json
import re
from pathlib import Path

from shapely.geometry import shape, mapping
from shapely.ops import unary_union

# ---------------- CONFIG ----------------

DATA_DIR = Path("data")
RAW_PROVINCES = DATA_DIR / "fl_geomorphology_provinces_raw.geojson"

# Output: debug feature layers
OUT_T1_FEATURES = DATA_DIR / "geology_tier1_features.geojson"
OUT_T2_FEATURES = DATA_DIR / "geology_tier2_features.geojson"
OUT_T3_FEATURES = DATA_DIR / "geology_tier3_features.geojson"
OUT_T4_FEATURES = DATA_DIR / "geology_tier4_features.geojson"

# Output: union overlays (the ones you map)
OUT_T1_UNION = DATA_DIR / "geology_tier1_union.geojson"
OUT_T2_UNION = DATA_DIR / "geology_tier2_union.geojson"
OUT_T3_UNION = DATA_DIR / "geology_tier3_union.geojson"
OUT_T4_UNION = DATA_DIR / "geology_tier4_union.geojson"

# ---- Districts that are broadly “upland-ish” in the classic Florida sense
HIGHLAND_DISTRICTS = {
    "Northern Highlands District",
    "Central Highlands District",
    "Lakes District",
}

# ---- Regexes for province name cues
RE_KARST = re.compile(r"\bkarst\b", re.IGNORECASE)

RE_UPLAND_CUE = re.compile(
    r"\b(ridge|highlands|hills|upland)\b",
    re.IGNORECASE
)

RE_T4_CUE = re.compile(
    r"\b(keys?|everglades|big\s*cypress|ten\s*thousand\s*islands|florida\s*bay|barrier)\b",
    re.IGNORECASE
)

RE_T3_CUE = re.compile(
    r"\b(coastal|lowlands?|swamp|strand|marsh|bay|lagoon|river|delta|terrace|flatwoods)\b",
    re.IGNORECASE
)

# ---- Hard Tier 4 province names (override list)
# Tune this after you see the first map.
TIER4_PROVINCES = {
    "Everglades Province",
    "Big Cypress Province",
    "Ten Thousand Islands Province",
    "Florida Bay Province",
    "Upper Keys Province",
    "Middle Keys Province",
    "Lower Keys Province",
    # Some datasets use variations — the regex catches most of it anyway.
    "Barrier Islands Province",
    "Barrier Island Province",
}

# ---- Tier 3 explicit province names (coastal/lowland/wet headaches)
# Again: tune after first pass.
TIER3_PROVINCES = {
    "Peninsular Coastal Lowlands Province",
    "Panhandle Coastal Lowlands Province",
    "Atlantic Coastal Complex Province",
    "Sea Islands Province",
    "Coastal Strand Province",
    "Coastal Swamps Province",
}

# ---------------- HELPERS ----------------

def norm(s: str) -> str:
    return (s or "").strip()

def load_fc(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")
    return json.loads(path.read_text())

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
    feat = {"type": "Feature", "properties": props, "geometry": mapping(u)}
    fc = {"type": "FeatureCollection", "features": [feat]}
    path.write_text(json.dumps(fc))
    print(f"Wrote {path} (union)")

def get_name(feature: dict) -> str:
    props = feature.get("properties", {}) or {}
    return norm(props.get("PROVINCE"))

def get_district(feature: dict) -> str:
    props = feature.get("properties", {}) or {}
    return norm(props.get("DISTRICT"))

# ---------------- CLASSIFICATION ----------------

def classify(feature: dict) -> int | None:
    """
    Returns tier number 1..4 (1 least risky, 4 most risky), or None if unclassified.
    Priority: 4 overrides all, then 3, then 2, then 1.
    """
    name = get_name(feature)
    district = get_district(feature)

    if not name:
        return None

    # Tier 4: hard veto systems
    if name in TIER4_PROVINCES or RE_T4_CUE.search(name):
        return 4

    # Tier 3: coastal/lowland/wet/flat
    if name in TIER3_PROVINCES or RE_T3_CUE.search(name):
        return 3

    # Tier 2: karst caution (this is where Gainesville/Alachua should live)
    # If a province says Karst explicitly, it’s Tier 2 unless it already got bumped to 3/4 above.
    if RE_KARST.search(name):
        return 2

    # Tier 1: upland-ish / ridge-ish candidates
    if district in HIGHLAND_DISTRICTS or RE_UPLAND_CUE.search(name):
        return 1

    return None

# ---------------- MAIN ----------------

def main():
    DATA_DIR.mkdir(exist_ok=True)
    raw = load_fc(RAW_PROVINCES)
    feats = raw.get("features", [])
    print(f"Loaded {RAW_PROVINCES} ({len(feats)} features)")

    t1_feats, t2_feats, t3_feats, t4_feats = [], [], [], []
    t1_geoms, t2_geoms, t3_geoms, t4_geoms = [], [], [], []

    unclassified = 0

    for f in feats:
        if not f.get("geometry"):
            continue

        tier = classify(f)
        g = shape(f["geometry"])

        if tier == 4:
            t4_feats.append(f); t4_geoms.append(g)
        elif tier == 3:
            t3_feats.append(f); t3_geoms.append(g)
        elif tier == 2:
            t2_feats.append(f); t2_geoms.append(g)
        elif tier == 1:
            t1_feats.append(f); t1_geoms.append(g)
        else:
            unclassified += 1

    # Debug feature layers
    write_fc(OUT_T1_FEATURES, t1_feats)
    write_fc(OUT_T2_FEATURES, t2_feats)
    write_fc(OUT_T3_FEATURES, t3_feats)
    write_fc(OUT_T4_FEATURES, t4_feats)

    # Union overlays
    write_union(OUT_T1_UNION, t1_geoms, {"tier": 1, "label": "Least risky"})
    write_union(OUT_T2_UNION, t2_geoms, {"tier": 2, "label": "Karst caution"})
    write_union(OUT_T3_UNION, t3_geoms, {"tier": 3, "label": "Lowland / coastal / wet"})
    write_union(OUT_T4_UNION, t4_geoms, {"tier": 4, "label": "Highest risk veto"})

    print("\nCounts:")
    print(f"  Tier 1 (least risky): {len(t1_feats)}")
    print(f"  Tier 2 (karst):       {len(t2_feats)}")
    print(f"  Tier 3 (lowland):     {len(t3_feats)}")
    print(f"  Tier 4 (veto):        {len(t4_feats)}")
    print(f"  Unclassified:         {unclassified}")
    print("\nDone.")

if __name__ == "__main__":
    main()