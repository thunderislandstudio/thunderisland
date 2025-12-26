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

# Districts that are broadly “upland-ish”
HIGHLAND_DISTRICTS = {
    "Northern Highlands District",
    "Central Highlands District",
    "Lakes District",
}

# Regex cues (kept intentionally blunt; you will tune by observing the output)
RE_UPLAND_CUE = re.compile(r"\b(ridge|highlands|hills|upland)\b", re.IGNORECASE)
RE_KARST = re.compile(r"\bkarst\b", re.IGNORECASE)

RE_T4_CUE = re.compile(
    r"\b(keys?|everglades|big\s*cypress|ten\s*thousand\s*islands|florida\s*bay|barrier)\b",
    re.IGNORECASE
)

RE_T3_CUE = re.compile(
    r"\b(coastal|lowlands?|swamp|strand|marsh|lagoon|terrace|flatwoods)\b",
    re.IGNORECASE
)

# Tier 4: hard veto systems (explicit)
TIER4_PROVINCES = {
    "Everglades Province",
    "Big Cypress Province",
    "Ten Thousand Islands Province",
    "Florida Bay Province",
    "Upper Keys Province",
    "Middle Keys Province",
    "Lower Keys Province",
    "Barrier Islands Province",
    "Barrier Island Province",
}

# Tier 3: coastal/lowland/wet headaches (explicit)
TIER3_PROVINCES = {
    "Peninsular Coastal Lowlands Province",
    "Panhandle Coastal Lowlands Province",
    "Atlantic Coastal Complex Province",
    "Sea Islands Province",
    "Coastal Strand Province",
    "Coastal Swamps Province",
}

# Tier 3: systemic hydrology risk overrides (prairie/basin systems)
TIER3_HYDRO_OVERRIDE_PROVINCES = {
	"Hawthorne Lakes Province",
	"Okeechobee Plain Province",
	"Big Cypress Province",
	"Chiefland Karst Plain Province",
	"Perry Karst Plain Province",
	"Caloosahahatchee Valley Province",
	"Woodville Karst Plain Province",
	"San Pedro Bay Province",
	"Crystal River Karst Plain Province",
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

def classify(feature: dict) -> int:
    """
    Returns tier number 1..4 (1 least risky, 4 most risky).
    Priority: 4 overrides all, then 3, then 2, then 1.
    NOTE: Anything not matching an explicit tier becomes Tier 2 by default.
    """
    name = get_name(feature)
    district = get_district(feature)

    # Tier 4: hard veto
    if name in TIER4_PROVINCES or RE_T4_CUE.search(name):
        return 4

    # Tier 3: coastal/lowland/wet
    if name in TIER3_PROVINCES or RE_T3_CUE.search(name):
        return 3

    # Tier 3: explicit hydrology risk overrides (Kissimmee Prairie/basin etc.)
    if name in TIER3_HYDRO_OVERRIDE_PROVINCES:
        return 3

    # Tier 1: “earned” stable-ish upland/ridge candidates
    # (We put this BEFORE Tier 2 default so it actually wins.)
    if district in HIGHLAND_DISTRICTS or RE_UPLAND_CUE.search(name):
        # BUT: if it’s explicitly Karst, don’t auto-bless it as Tier 1
        # (karst uplands are still caution)
        if RE_KARST.search(name):
            return 2
        return 1

    # Tier 2: default interior Florida condition (caution by default, not optimism)
    return 2

# ---------------- MAIN ----------------

def main():
    DATA_DIR.mkdir(exist_ok=True)
    raw = load_fc(RAW_PROVINCES)
    feats = raw.get("features", [])
    print(f"Loaded {RAW_PROVINCES} ({len(feats)} features)")

    t1_feats, t2_feats, t3_feats, t4_feats = [], [], [], []
    t1_geoms, t2_geoms, t3_geoms, t4_geoms = [], [], [], []

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
            # Should never happen; classify() returns 1..4
            t2_feats.append(f); t2_geoms.append(g)

    # Debug feature layers
    write_fc(OUT_T1_FEATURES, t1_feats)
    write_fc(OUT_T2_FEATURES, t2_feats)
    write_fc(OUT_T3_FEATURES, t3_feats)
    write_fc(OUT_T4_FEATURES, t4_feats)

    # Union overlays
    write_union(OUT_T1_UNION, t1_geoms, {"tier": 1, "label": "Least risky"})
    write_union(OUT_T2_UNION, t2_geoms, {"tier": 2, "label": "Default / caution"})
    write_union(OUT_T3_UNION, t3_geoms, {"tier": 3, "label": "Lowland/wet/coastal + hydro override"})
    write_union(OUT_T4_UNION, t4_geoms, {"tier": 4, "label": "Highest risk veto"})

    print("\nCounts:")
    print(f"  Tier 1 (least risky): {len(t1_feats)}")
    print(f"  Tier 2 (default):     {len(t2_feats)}")
    print(f"  Tier 3 (lowland):     {len(t3_feats)}")
    print(f"  Tier 4 (veto):        {len(t4_feats)}")
    print("\nDone.")

if __name__ == "__main__":
    main()