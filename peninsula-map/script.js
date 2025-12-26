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
let coordMarker = null;

function setStatus(msg, isError = false) {
  const el = document.getElementById("status");
  if (!el) return;
  el.textContent = msg;
  el.style.color = isError ? "#b00020" : "";
}

function parseLatLng(text) {
  const match = text.match(/^\s*(-?\d+(\.\d+)?)\s*,\s*(-?\d+(\.\d+)?)\s*$/);
  if (!match) throw new Error("Paste as: lat, lng (comma required)");

  const lat = Number(match[1]);
  const lng = Number(match[3]);

  if (!Number.isFinite(lat) || !Number.isFinite(lng)) throw new Error("Not valid numbers");
  if (lat < -90 || lat > 90) throw new Error("Latitude out of range");
  if (lng < -180 || lng > 180) throw new Error("Longitude out of range");

  return { lat, lng };
}

function plotCoordinates() {
  try {
    if (typeof map === "undefined" || !map) {
      setStatus("Map object not ready yet (map is undefined).", true);
      console.error("map is undefined or not initialized yet");
      return;
    }

    const raw = (document.getElementById("coordInput")?.value || "").trim();
    if (!raw) {
      setStatus("Paste coordinates first.", true);
      return;
    }

    const { lat, lng } = parseLatLng(raw);

    if (coordMarker) map.removeLayer(coordMarker);
    coordMarker = L.marker([lat, lng]).addTo(map);
    coordMarker.bindPopup(`<strong>Location</strong><br>${lat}, ${lng}`).openPopup();

    map.setView([lat, lng], 13);
    setStatus("Plotted location");
  } catch (err) {
    console.error(err);
    setStatus(err.message, true);
    alert(err.message);
  }
}

function clearPoint() {
  try {
    if (typeof map === "undefined" || !map) {
      setStatus("Map object not ready yet (map is undefined).", true);
      console.error("map is undefined or not initialized yet");
      return;
    }

    if (coordMarker) {
      map.removeLayer(coordMarker);
      coordMarker = null;
    }
    setStatus("Cleared");
  } catch (err) {
    console.error(err);
    setStatus(err.message, true);
  }
}

// Attach listeners after everything is loaded
window.addEventListener("load", () => {
  const plotBtn = document.getElementById("plotCoordBtn");
  const clearBtn = document.getElementById("clearBtn");

  if (!plotBtn) console.error("plotCoordBtn not found in DOM");
  if (!clearBtn) console.error("clearBtn not found in DOM");

  plotBtn?.addEventListener("click", plotCoordinates);
  clearBtn?.addEventListener("click", clearPoint);

  setStatus("Ready");
});
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