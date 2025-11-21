// Initialize map centered on Florida
const map = L.map("map", {
    zoomControl: true,
    minZoom: 5,
    maxZoom: 15
}).setView([28.4, -82.5], 6);

// Carto Light basemap
L.tileLayer(
    "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png",
    {
        attribution: '&copy; OpenStreetMap, &copy; CARTO',
        maxZoom: 19
    }
).addTo(map);

// Layer dictionary
const layers = {
    tier1: null,
    tier2: null,
    tier3: null,
    tier4: null,
    nogopub30: null
};

// LSU colors
const LSU_PURPLE = "#461D7C";
const LSU_GOLD   = "#FDD023";

// Helper to load a GeoJSON layer, with control over initial visibility
function loadLayer(key, url, style, startVisible = true) {
    fetch(url)
        .then(res => res.json())
        .then(data => {
            const layer = L.geoJSON(data, { style });
            layers[key] = layer;

            if (startVisible) {
                layer.addTo(map);
            }
        })
        .catch(err => {
            console.error(`Error loading layer ${key} from ${url}:`, err);
        });
}

// Load all layers
// Tier 1: Publix ≤15 / WF ≤30  (default ON)
loadLayer("tier1", "data/GoZone_P15_WF30.geojson", {
    color: LSU_PURPLE,
    fillColor: LSU_PURPLE,
    fillOpacity: 0.28,
    weight: 2
}, true);

// Tier 2: Publix ≤25 / WF ≤50  (default ON)
loadLayer("tier2", "data/GoZone_P25_WF50.geojson", {
    color: LSU_GOLD,
    fillColor: LSU_GOLD,
    fillOpacity: 0.32,
    weight: 2
}, true);

// Tier 3: Publix ≤30 / WF ≤60  (default ON)
loadLayer("tier3", "data/GoZone_P30_WF60.geojson", {
    color: "#9D7BC0", // lighter purple
    fillColor: "#9D7BC0",
    fillOpacity: 0.28,
    weight: 2
}, true);

// Publix ≤20 / WF ≤60 (extra tier, default OFF)
loadLayer("tier4", "data/GoZone_P20_WF60.geojson", {
    color: "#FFB733",
    fillColor: "#FFB733",
    fillOpacity: 0.28,
    weight: 2
}, false);

// No-Go: not within 30 miles of Publix (default OFF)
loadLayer("nogopub30", "data/NoGo_not_within_30mi_Publix.geojson", {
    color: "#FF0033",
    fillColor: "#FF0033",
    fillOpacity: 0.15,
    weight: 1
}, false);

// Checkbox handlers
document.querySelectorAll(".layer-toggle").forEach(cb => {
    cb.addEventListener("change", () => {
        const key = cb.dataset.layer;
        const layer = layers[key];
        if (!layer) return; // layer might not be loaded yet

        if (cb.checked) {
            layer.addTo(map);
        } else {
            map.removeLayer(layer);
        }
    });
});