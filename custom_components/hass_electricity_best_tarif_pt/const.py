"""Constants for the Tarifários Eletricidade PT integration."""
import json
from pathlib import Path

DOMAIN = "hass_electricity_best_tarif_pt"

# Energy type options
ENERGY_TYPE_OPTIONS = {
    "ele": "Eletricidade apenas",
    "gn": "Gás Natural apenas", 
    "dual": "Eletricidade e Gás Natural",
    "all": "Todos os tipos"
}

def get_version():
    """Get version from manifest.json."""
    try:
        manifest_path = Path(__file__).parent / "manifest.json"
        with open(manifest_path, encoding="utf-8") as f:
            manifest = json.load(f)
        return manifest.get("version", "3.0.0")  # Updated for new features
    except Exception:
        return "3.0.0"

VERSION = get_version()
