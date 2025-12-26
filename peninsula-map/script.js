// Florida Go Zones: Publix / Whole Foods distance shells

window.addEventListener("load", () => {
  console.log("Zone map script loaded");

  // Initialize map centered on Florida
  const map = L.map("map", {
    zoomControl: true,
    minZoom: 5,
    maxZoom: 15
  }).setView([28.4, -82.5], 6);

  // Basemap (OSM)
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "&copy; OpenStreetMap contributors",
    maxZoom: 19
  }).addTo(map);

  // Layers registry
const layers = {
  publix15: null,
  publix25: null,
  wf30: null,
  wf50: null,
geo_t1: null,
geo_t2: null,
geo_t3: null,
geo_t4: null,
};

  // Colors
  const LSU_PURPLE = "#461D7C";
  const LSU_GOLD = "#FDD023";

  function loadLayer(key, url, style, startVisible = true) {
    console.log(`Loading layer ${key} from ${url}`);
    fetch(url)
      .then((res) => {
        if (!res.ok) {
          throw new Error(`HTTP ${res.status} for ${url}`);
        }
        return res.json();
      })
      .then((data) => {
        const layer = L.geoJSON(data, { style });
        layers[key] = layer;

        if (startVisible) {
          layer.addTo(map);
          console.log(`Layer ${key} added to map`);
        } else {
          console.log(`Layer ${key} loaded but not shown (checkbox off)`);
        }
      })
      .catch((err) => {
        console.error(`Error loading layer ${key} from ${url}:`, err);
      });
  }

  // Publix ≤15 mi
  loadLayer(
    "publix15",
    "data/Publix_15mi.geojson",
    {
      color: "#ff0000",
      fillColor: "#ff0000",
      fillOpacity: 0.5,
      weight: 2
    },
    false
  );

  // Publix ≤25 mi (slightly lighter purple)
  loadLayer(
    "publix25",
    "data/Publix_25mi.geojson",
    {
      color: "#ff0000",
      fillColor: "#ff0000",
      fillOpacity: 0.3,
      weight: 2
    },
    false
  );

  // Whole Foods ≤30 mi
  loadLayer(
    "wf30",
    "data/WF_30mi.geojson",
    {
      color: "#0000ff",
      fillColor: "#0000ff",
      fillOpacity: 0.50,
      weight: 2
    },
    false
  );

  // Whole Foods ≤50 mi (lighter halo)
  loadLayer(
    "wf50",
    "data/WF_50mi.geojson",
    {
      color: "#0000ff",
      fillColor: "#0000ff",
      fillOpacity: 0.3,
      weight: 2
    },
    false
  );

// ---- Geology risk tiers ----

// Tier 1: least risky (green, subtle)
loadLayer(
  "geo_t1",
  "data/geology_tier1_union.geojson",
  { color: "#2E7D32", fillColor: "#2E7D32", fillOpacity: 0.32, weight: 3 },
  false
);

// Tier 2: default / caution (cool neutral, very light)
loadLayer(
  "geo_t2",
  "data/geology_tier2_union.geojson",
  { color: "#546E7A", fillColor: "#546E7A", fillOpacity: 0.32, weight: 2 },
  false
);

// Tier 3: lowland / wet / coastal (orange)
loadLayer(
  "geo_t3",
  "data/geology_tier3_union.geojson",
  { color: "#EF6C00", fillColor: "#EF6C00", fillOpacity: 0.22, weight: 2 },
  false
);

// Tier 4: highest risk veto (red, louder)
loadLayer(
  "geo_t4",
  "data/geology_tier4_union.geojson",
  { color: "#C62828", fillColor: "#C62828", fillOpacity: 0.35, weight: 2 },
  false
);

// Address Lookup
async function geocodeCensus(address) {
  const url =
    "https://geocoding.geo.census.gov/geocoder/locations/onelineaddress" +
    "?benchmark=2020" +
    "&format=json" +
    "&address=" + encodeURIComponent(address);

  const res = await fetch(url, { headers: { "Accept": "application/json" } });
  if (!res.ok) throw new Error("Census geocoder request failed");

  const data = await res.json();
  const matches = data?.result?.addressMatches || [];
  if (!matches.length) throw new Error("No Census match");

  const best = matches[0];
  return {
    lat: best.coordinates.y,
    lon: best.coordinates.x,
    display: best.matchedAddress || address,
    source: "US Census"
  };
}

async function geocodeNominatim(address) {
  const url =
    "https://nominatim.openstreetmap.org/search" +
    "?format=json&limit=1&addressdetails=1" +
    "&countrycodes=us" +
    "&q=" + encodeURIComponent(address);

  const res = await fetch(url, {
    headers: {
      "Accept": "application/json",
      // Don't pretend this is a browser default—Nominatim wants an identifying UA.
      "User-Agent": "peninsula-map/1.0 (personal use)"
    }
  });

  if (!res.ok) throw new Error("Nominatim request failed");
  const data = await res.json();
  if (!data.length) throw new Error("No Nominatim match");

  return {
    lat: parseFloat(data[0].lat),
    lon: parseFloat(data[0].lon),
    display: data[0].display_name || address,
    source: "Nominatim"
  };
}

async function geocodeAddress(address) {
  // Clean common Zillow/clipboard junk
  const cleaned = address
    .replace(/\s+United States\s*$/i, "")
    .replace(/\s+USA\s*$/i, "")
    .trim();

  try {
    return await geocodeCensus(cleaned);
  } catch (e) {
    // Fallback if Census misses (it does sometimes with weird formats/new builds)
    return await geocodeNominatim(cleaned);
  }
}
// Address Lookup

  // Checkbox handlers
  document.querySelectorAll(".layer-toggle").forEach((cb) => {
    cb.addEventListener("change", () => {
      const key = cb.dataset.layer;
      const layer = layers[key];

      if (!layer) {
        console.log(`Checkbox toggled for ${key}, but layer not loaded yet`);
        return;
      }

      if (cb.checked) {
        layer.addTo(map);
      } else {
        map.removeLayer(layer);
      }
    });
  });
});