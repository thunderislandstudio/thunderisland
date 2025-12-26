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
  geo_upland: null,
  geo_karst: null,
  geo_lowland: null
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
    true
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
    true
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

// Geology: upland / ridge (subtle green, low opacity)
loadLayer(
  "geo_upland",
  "data/geology_upland_union.geojson",
  {
    color: "#2E7D32",
    fillColor: "#2E7D32",
    fillOpacity: 0.12,
    weight: 2
  },
  false
);

// Geology: karst caution (amber)
loadLayer(
  "geo_karst",
  "data/geology_karst_union.geojson",
  {
    color: "#F9A825",
    fillColor: "#F9A825",
    fillOpacity: 0.22,
    weight: 2
  },
  false
);

// Geology: lowland / coastal no-go (red, louder)
loadLayer(
  "geo_lowland",
  "data/geology_lowland_union.geojson",
  {
    color: "#C62828",
    fillColor: "#C62828",
    fillOpacity: 0.35,
    weight: 2
  },
  false
);

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