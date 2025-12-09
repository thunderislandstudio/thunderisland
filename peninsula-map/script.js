// Multi-zone map: Publix ≤15/WF ≤50, Publix ≤25/WF ≤50, WF ≤60

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

  // Layer dictionary
  const layers = {
    p15wf50: null,
    p25wf50: null,
    wf60: null
  };

  // LSU-ish colors
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

  // === Load your three zones ===
  // Make sure these filenames exist in /data on the deployed site

  // Publix ≤15 & WF ≤50
  loadLayer(
    "p15wf50",
    "data/GoZone_P15_WF50.geojson",
    {
      color: LSU_PURPLE,
      fillColor: LSU_PURPLE,
      fillOpacity: 0.28,
      weight: 2
    },
    true
  );

  // Publix ≤25 & WF ≤50
  loadLayer(
    "p25wf50",
    "data/GoZone_P25_WF50.geojson",
    {
      color: LSU_GOLD,
      fillColor: LSU_GOLD,
      fillOpacity: 0.32,
      weight: 2
    },
    true
  );

  // Whole Foods ≤60 regardless of Publix
  loadLayer(
    "wf60",
    "data/WF_Within60.geojson",
    {
      color: "#9D7BC0",
      fillColor: "#9D7BC0",
      fillOpacity: 0.18,
      weight: 1.5
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