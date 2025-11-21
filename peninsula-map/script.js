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
        attribution:
            '&copy; OpenStreetMap, &copy; CARTO',
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
const LSU_GOLD = "#FDD023";

// Load a layer helper
function loadLayer(key, url, style) {
    fetch(url)
        .then(res => res.json())
        .then(data => {
            layers[key] = L.geoJSON(data, {
                style: style
            }).addTo(map);
        });
}

// Load all your layers
loadLayer("tier1", "data/GoZone_P15_WF30.geojson", {
    color: LSU_PURPLE,
    fillColor: LSU_PURPLE,
    fillOpacity: 0.28,
    weight: 2
});

loadLayer("tier2", "data/GoZone_P25_WF50.geojson", {
    color: LSU_GOLD,
    fillColor: LSU_GOLD,
    fillOpacity: 0.32,
    weight: 2
});

loadLayer("tier3", "data/GoZone_P30_WF60.geojson", {
    color: "#9D7BC0", // lighter purple variant
    fillColor: "#9D7BC0",
    fillOpacity: 0.28,
    weight: 2
});

loadLayer("tier4", "data/GoZone_P20_WF60.geojson", {
    color: "#FFB733",
    fillColor: "#FFB733",
    fillOpacity: 0.28,
    weight: 2
});

loadLayer("nogopub30", "data/NoGo_not_within_30mi_Publix.geojson", {
    color: "#FF0033",
    fillColor: "#FF0033",
    fillOpacity: 0.15,
    weight: 1
});

// Checkbox handlers
document.querySelectorAll(".layer-toggle").forEach(cb => {
    cb.addEventListener("change", () => {
        const layer = layers[cb.dataset.layer];
        if (!layer) return;

        if (cb.checked) {
            layer.addTo(map);
        } else {
            map.removeLayer(layer);
        }
    });
});