"""Sensor platform for Tarifários Eletricidade PT (only offer sensors)."""
from __future__ import annotations

from datetime import datetime, timezone
import math
import unicodedata
import logging

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, VERSION

_LOGGER = logging.getLogger(__name__)

CODE_COL_CANDIDATES = ["Código da oferta comercial", "COD_Proposta", "CODProposta"]
NAME_COL_CANDIDATES = ["Nome da oferta comercial", "NomeProposta", "Nome Proposta", "Nome"]
POT_COL_CANDIDATES  = ["Potência contratada__norm", "Pot_Cont__norm", "Potência contratada", "Pot_Cont"]
TERMO_FIXO_CANDIDATES = ["Termo fixo (€/dia)", "TF"]


def _normalize(k: str) -> str:
    k2 = unicodedata.normalize("NFKD", k).encode("ascii", "ignore").decode()
    k2 = k2.lower()
    for old, new in (("€", "eur"), ("%", "pct"), ("/", "_"), ("-", "_"), ("|", "_"), (":", "_")):
        k2 = k2.replace(old, new)
    for ch in "()[]{}":
        k2 = k2.replace(ch, "")
    while "  " in k2:
        k2 = k2.replace("  ", " ")
    k2 = k2.strip().replace(" ", "_")
    while "__" in k2:
        k2 = k2.replace("__", "_")
    return k2


def _clean(v):
    """Clean and normalize values, returning appropriate defaults for empty/unknown values."""
    if v is None:
        return None
    if isinstance(v, float) and math.isnan(v):
        return None
    if isinstance(v, str):
        # Strip whitespace and check for empty or "unknown" values
        cleaned = v.strip()
        if not cleaned or cleaned.lower() in ('nan', 'na', 'n/a', 'unknown', 'null', 'none', ''):
            return None
        return cleaned
    return v


def _clean_for_display(v, field_name=None):
    """Clean values for display, providing better defaults than 'Unknown'."""
    cleaned = _clean(v)
    if cleaned is None:
        # Provide contextual defaults based on field type
        if field_name and any(term in field_name.lower() for term in ['url', 'link', 'contacto', 'email']):
            return ''  # Empty string for contact fields
        elif field_name and any(term in field_name.lower() for term in ['data', 'date']):
            return ''  # Empty string for dates
        elif field_name and any(term in field_name.lower() for term in ['custo', 'preco', 'price', 'cost']):
            return '0'  # Zero for monetary fields that might be optional
        elif field_name and any(term in field_name.lower() for term in ['escalao', 'operador', 'rede']):
            return 'N/A'  # More appropriate for technical fields
        else:
            return None  # Let Home Assistant handle as Unknown
    return cleaned


def _norm_pot(val):
    if not val:
        return None
    # Normalize to dot format for consistent comparison
    return str(val).replace(",", ".").strip()


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Set up the sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    config = hass.data[DOMAIN][entry.entry_id]["config"]
    
    # Get data from coordinator
    df = coordinator.data
    if df is None or df.empty:
        _LOGGER.warning("No data available from coordinator.")
        return

    ts = datetime.now(timezone.utc)
    entities = []

    # Always create traditional offer sensors
    offer_sensors = await _create_offer_sensors(df, coordinator, entry.entry_id, config, ts)
    entities.extend(offer_sensors)
    
    # Create enhanced sensors if consumption analysis is enabled
    if config.get("enable_consumption_analysis", False):
        analysis_sensors = await _create_analysis_sensors(hass, entry, coordinator, config)
        entities.extend(analysis_sensors)

    async_add_entities(entities, True)


async def _create_analysis_sensors(hass, entry, coordinator, config):
    """Create consumption analysis and recommendation sensors."""
    from .enhanced_sensor import (
        ConsumptionAnalysisSensor, TariffRecommendationSensor, 
        PotentialSavingsSensor, BestTariffComparisonSensor
    )
    from .recommendation_engine import TariffRecommendationEngine
    
    energy_sensor = config.get("energy_sensor")
    analysis_days = config.get("analysis_days", 30)
    tariff_type = config.get("tariff_type", "bi_hourly")
    
    if not energy_sensor:
        _LOGGER.warning("No energy sensor configured for consumption analysis")
        return []
    
    # Create recommendation engine
    recommendation_engine = TariffRecommendationEngine()
    
    # Store the recommendation engine in the domain data for persistence
    if "recommendation_engines" not in hass.data[DOMAIN]:
        hass.data[DOMAIN]["recommendation_engines"] = {}
    hass.data[DOMAIN]["recommendation_engines"][entry.entry_id] = recommendation_engine
    
    # Create analysis sensors
    return [
        ConsumptionAnalysisSensor(
            coordinator, entry.entry_id, energy_sensor, analysis_days, tariff_type
        ),
        TariffRecommendationSensor(
            coordinator, entry.entry_id, recommendation_engine, config
        ),
        PotentialSavingsSensor(
            coordinator, entry.entry_id, recommendation_engine
        ),
        BestTariffComparisonSensor(
            coordinator, entry.entry_id, recommendation_engine
        ),
    ]


async def _create_offer_sensors(df, coordinator, entry_id, config, ts):
    """Create traditional offer sensors."""

    code_col = next((c for c in CODE_COL_CANDIDATES if c in df.columns), None)
    name_col = next((c for c in NAME_COL_CANDIDATES if c in df.columns), None)
    pot_norm_col = next((c for c in POT_COL_CANDIDATES if c in df.columns), None)
    termo_fixo_col = next((c for c in TERMO_FIXO_CANDIDATES if c in df.columns), None)

    if not code_col:
        _LOGGER.error("Code column not found. Columns=%s", list(df.columns))
        return []

    entities = []
    comercializador = config.get("comercializador", "unknown")
    
    # Group by offer code to avoid creating multiple entities for the same offer
    # (which can happen when there are multiple billing cycles)
    grouped_offers = {}
    
    for _, row in df.iterrows():
        codigo = str(row[code_col])
        
        # Skip if we already processed this offer code
        if codigo in grouped_offers:
            # Merge billing cycle data into existing offer
            existing_attrs = grouped_offers[codigo]['attrs']
            
            # Add billing cycle specific data
            ciclo_col = "Ciclo de contagem"
            if ciclo_col in row and row[ciclo_col]:
                ciclo = str(row[ciclo_col]).strip()
                # Add cycle-specific pricing data
                for k, v in row.to_dict().items():
                    if any(price_term in k for price_term in ["Termo de energia", "TV", "TF"]):
                        normalized_key = _normalize(f"{k}_{ciclo}")
                        existing_attrs[normalized_key] = _clean_for_display(v, k)
            continue
        
        # Get the commercial offer name (Nome da oferta comercial)
        offer_name = None
        if name_col and row.get(name_col):
            offer_name = str(row[name_col]).strip()
        
        # Create display name: Provider - Commercial Offer Name
        if offer_name:
            full_display_name = f"{comercializador} - {offer_name}"
        else:
            # Fallback if no offer name available
            full_display_name = f"{comercializador} - Tarifa {codigo}"

        # Get the termo fixo value for this row (prefer the first encountered)
        termo_fixo_value = None
        if termo_fixo_col and row.get(termo_fixo_col):
            try:
                termo_fixo_value = float(str(row[termo_fixo_col]).replace(",", "."))
            except (ValueError, TypeError):
                termo_fixo_value = None

        raw = row.to_dict()
        attrs = {}
        for k, v in raw.items():
            normalized_key = _normalize(k)
            cleaned_value = _clean_for_display(v, k)
            attrs[normalized_key] = cleaned_value
            # Debug specific columns
            if "vazio" in normalized_key.lower() and ("cheias" in normalized_key.lower() or normalized_key.lower().endswith("vazio")):
                _LOGGER.debug("Attribute mapping: '%s' -> '%s' = %s", k, normalized_key, cleaned_value)
        
        attrs["codigo_original"] = codigo
        attrs["comercializador"] = comercializador
        attrs["nome_oferta_comercial"] = offer_name or f"Tarifa {codigo}"
        attrs["termo_fixo_eur_dia"] = termo_fixo_value
        attrs["integration_version"] = VERSION
        attrs["last_refresh_iso"] = ts.isoformat()
        if pot_norm_col and pot_norm_col in row:
            attrs["potencia_norm"] = row[pot_norm_col]

        # Store the offer data
        grouped_offers[codigo] = {
            'display_name': full_display_name,
            'attrs': attrs,
            'termo_fixo_value': termo_fixo_value,
            'offer_name': offer_name
        }
    
    # Create entities from grouped offers
    entities = []
    for codigo, offer_data in grouped_offers.items():
        entities.append(OfferSensor(
            coordinator, 
            entry_id, 
            codigo, 
            offer_data['display_name'], 
            offer_data['attrs'], 
            ts, 
            offer_data['termo_fixo_value'], 
            offer_data['offer_name']
        ))

    return entities


class OfferSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Tarifarios offer sensor."""
    _attr_icon = "mdi:currency-eur"
    _attr_device_class = None  # No device class for price values
    _attr_unit_of_measurement = "€/day"

    def __init__(self, coordinator, entry_id: str, codigo: str, name: str, attrs: dict, ts: datetime, termo_fixo_value: float = None, offer_name: str = None):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = name
        
        # Simplified unique ID based on offer code only
        # since we now group by offer and don't create separate entities for billing cycles
        self._attr_unique_id = f"{entry_id}_{codigo}"
        
        # Debug log for troubleshooting
        _LOGGER.debug("Creating sensor unique_id for offer %s: %s", codigo, self._attr_unique_id)
            
        self._codigo = codigo
        self._attrs = attrs
        self._ts = ts
        self._termo_fixo_value = termo_fixo_value

    @property
    def native_value(self):
        """Return the daily fixed term value in euros."""
        if self.coordinator.last_update_success and self.coordinator.data is not None and not self.coordinator.data.empty:
            # Try to get fresh termo fixo value from coordinator data
            # Use the first matching row (since we group by offer code)
            try:
                code_col = next((c for c in CODE_COL_CANDIDATES if c in self.coordinator.data.columns), None)
                termo_fixo_col = next((c for c in TERMO_FIXO_CANDIDATES if c in self.coordinator.data.columns), None)
                
                if code_col and termo_fixo_col:
                    matching_rows = self.coordinator.data[self.coordinator.data[code_col].astype(str) == self._codigo]
                    if not matching_rows.empty:
                        row = matching_rows.iloc[0]  # Take first row for this offer
                        if row.get(termo_fixo_col):
                            try:
                                return float(str(row[termo_fixo_col]).replace(",", "."))
                            except (ValueError, TypeError):
                                pass
            except Exception as e:
                _LOGGER.debug("Error getting fresh termo fixo for %s: %s", self._codigo, e)
        
        # Fallback to stored value
        return self._termo_fixo_value

    @property
    def extra_state_attributes(self):
        """Return the state attributes with data from all billing cycles."""
        # Update attributes with fresh data from coordinator if available
        if self.coordinator.data is not None and not self.coordinator.data.empty:
            try:
                # Find all rows for this codigo in the fresh data
                code_col = next((c for c in CODE_COL_CANDIDATES if c in self.coordinator.data.columns), None)
                if code_col:
                    matching_rows = self.coordinator.data[self.coordinator.data[code_col].astype(str) == self._codigo]
                    if not matching_rows.empty:
                        # Merge data from all rows (billing cycles) for this offer
                        fresh_attrs = {}
                        
                        # Start with the first row as base
                        base_row = matching_rows.iloc[0]
                        for k, v in base_row.to_dict().items():
                            normalized_key = _normalize(k)
                            fresh_attrs[normalized_key] = _clean_for_display(v, k)
                        
                        # Add cycle-specific data from other rows
                        ciclo_col = "Ciclo de contagem"
                        for _, row in matching_rows.iterrows():
                            if ciclo_col in row and row[ciclo_col]:
                                ciclo = str(row[ciclo_col]).strip()
                                # Add cycle-specific pricing data with cycle suffix
                                for k, v in row.to_dict().items():
                                    if any(price_term in k for price_term in ["Termo de energia", "TV"]):
                                        normalized_key = _normalize(f"{k}_{ciclo}")
                                        fresh_attrs[normalized_key] = _clean_for_display(v, k)
                        
                        fresh_attrs["codigo_original"] = self._codigo
                        fresh_attrs["integration_version"] = VERSION
                        fresh_attrs["last_refresh_iso"] = datetime.now(timezone.utc).isoformat()
                        
                        # Add summary of available billing cycles
                        available_cycles = [str(row[ciclo_col]).strip() for _, row in matching_rows.iterrows() 
                                          if ciclo_col in row and row[ciclo_col]]
                        if available_cycles:
                            fresh_attrs["ciclos_disponiveis"] = ", ".join(sorted(set(available_cycles)))
                        
                        return fresh_attrs
            except Exception as e:
                _LOGGER.debug("Error updating attributes for %s: %s", self._codigo, e)
        
        # Fallback to stored attributes
        return self._attrs

    @property
    def unique_id(self) -> str:
        """Return a unique ID for the sensor."""
        return self._attr_unique_id
