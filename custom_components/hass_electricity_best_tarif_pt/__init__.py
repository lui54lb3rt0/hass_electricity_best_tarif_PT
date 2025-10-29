"""Tarifários Eletricidade PT Home Assistant Integration."""

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform

from .const import DOMAIN, VERSION  # ensure DOMAIN = "hass_tarifarios_eletricidade_pt"
from .data_loader import TarifariosDataUpdateCoordinator

# Expose version for Home Assistant
__version__ = VERSION

PLATFORMS: list[Platform] = [Platform.SENSOR]

async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the integration (YAML not used)."""
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a config entry."""
    hass.data.setdefault(DOMAIN, {})
    
    # Extract configuration from config entry
    comercializador = entry.data.get("comercializador")
    pot_cont = entry.data.get("pot_cont")
    energy_type = entry.data.get("energy_type", "ele")  # Default to electricity only for backward compatibility
    sel_codes = entry.data.get("codigos_oferta")
    if isinstance(sel_codes, str):
        sel_codes = [c.strip() for c in sel_codes.split(",") if c.strip()]
    
    # Create the data update coordinator
    coordinator = TarifariosDataUpdateCoordinator(
        hass, 
        comercializador=comercializador,
        codigos_oferta=sel_codes,
        pot_cont=pot_cont,
        energy_type=energy_type
    )
    
    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()
    
    # Store coordinator and config in hass.data
    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "config": entry.data,
    }
    
    # Initialize recommendation engines storage if not exists
    if "recommendation_engines" not in hass.data[DOMAIN]:
        hass.data[DOMAIN]["recommendation_engines"] = {}

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
