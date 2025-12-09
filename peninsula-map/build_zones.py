#!/usr/bin/env python3
import json
from pathlib import Path

from shapely.geometry import shape, mapping, Point, MultiPoint
from shapely.ops import unary_union, transform
import pyproj

# ---------- CONFIG ---------------------------------------------------

# Input point files
PUBLIX_POINTS_FILE = Path("publix.geojson")
WHOLEFOODS_POINTS_FILE = Path("wholefoods.geojson")

# Output directory for zone polygons (your map's /data folder)
OUTPUT_DIR = Path("data")

# Publix distance zones (miles)
PUBLIX_ZONES = [
    {
        "name": "Publix≤15mi",
        "miles": 15,
        "outfile": "Publix_15mi.geojson",
    },
    {
        "name": "Publix≤25mi",
        "miles": 25,
        "outfile": "Publix_25mi.geojson",
    },
]

# Whole Foods distance zones (miles)
WHOLEFOODS_ZONES = [
    {
        "name": "WF≤30mi",
        "miles": 30,
        "outfile": "WF_30mi.geojson",
    },
    {
        "name": "WF≤50mi",
        "miles": 50,
        "outfile": "WF_50mi.geojson",
    },
]

# Approx center of Florida for projection (Azimuthal Equidistant)
CENTER_LAT = 27.5
CENTER_LON = -82.0

MILES_TO_METERS = 1609.344

# ---------- HELPERS --------------------------------------------------


def load_points(path: Path):
    """
    Load a GeoJSON with Point or MultiPoint features and return a list of shapely Points.
    Handles both Point and MultiPoint.
    """
    with path.open() as f:
        gj = json.load(f)

    features = gj.get("features", [])
    pts = []

    for feat in features:
        geom = feat.get("geometry")
        if not geom:
            continue

        g = shape(geom)

        if isinstance(g, Point):
            pts.append(g)
        elif isinstance(g, MultiPoint):
            pts.extend(list(g.geoms))
        else:
            continue

    return pts


def make_projectors():
    """
    Return functions to project lon/lat <-> meters around Florida using an
    Azimuthal Equidistant projection centered roughly on the peninsula.
    """
    wgs84 = pyproj.CRS("EPSG:4326")
    aeqd = pyproj.CRS.from_proj4(
        f"+proj=aeqd +lat_0={CENTER_LAT} +lon_0={CENTER_LON} "
        "+x_0=0 +y_0=0 +ellps=WGS84 +units=m +no_defs"
    )

    to_m = pyproj.Transformer.from_crs(wgs84, aeqd, always_xy=True).transform
    to_deg = pyproj.Transformer.from_crs(aeqd, wgs84, always_xy=True).transform
    return to_m, to_deg


def buffer_points(points, miles, to_m, to_deg):
    """
    Buffer a list of lon/lat Points by N miles and return a union polygon in lon/lat.
    """
    if not points:
        return None

    radius_m = miles * MILES_TO_METERS

    projected = [transform(to_m, p) for p in points]
    buffered = [p.buffer(radius_m) for p in projected]
    unioned_m = unary_union(buffered)

    unioned_ll = transform(to_deg, unioned_m)
    return unioned_ll


def geom_to_feature_collection(geom, name: str):
    """Wrap a shapely geometry in a GeoJSON FeatureCollection."""
    if geom is None or geom.is_empty:
        return {
            "type": "FeatureCollection",
            "features": [],
        }

    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"name": name},
                "geometry": mapping(geom),
            }
        ],
    }


# ---------- MAIN BUILD LOGIC ----------------------------------------


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)

    print("Loading point data…")
    publix_points = load_points(PUBLIX_POINTS_FILE)
    wf_points = load_points(WHOLEFOODS_POINTS_FILE)
    print(f"  Publix points: {len(publix_points)}")
    print(f"  Whole Foods points (flattened): {len(wf_points)}")

    to_m, to_deg = make_projectors()

    # Publix zones
    for zone in PUBLIX_ZONES:
        miles = zone["miles"]
        name = zone["name"]
        print(f"\nBuffering Publix at {miles} miles…")
        p_union = buffer_points(publix_points, miles, to_m, to_deg)
        fc = geom_to_feature_collection(p_union, name)
        out_path = OUTPUT_DIR / zone["outfile"]
        with out_path.open("w") as f:
            json.dump(fc, f)
        print(f"  Wrote {out_path}")

    # Whole Foods zones
    for zone in WHOLEFOODS_ZONES:
        miles = zone["miles"]
        name = zone["name"]
        print(f"\nBuffering Whole Foods at {miles} miles…")
        wf_union = buffer_points(wf_points, miles, to_m, to_deg)
        fc = geom_to_feature_collection(wf_union, name)
        out_path = OUTPUT_DIR / zone["outfile"]
        with out_path.open("w") as f:
            json.dump(fc, f)
        print(f"  Wrote {out_path}")

    print("\nDone.")


if __name__ == "__main__":
    main()