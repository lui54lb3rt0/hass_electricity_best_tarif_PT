"""Enhanced sensor platform for Smart Tariff Analyzer."""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
import logging
from typing import Dict, Any, Optional

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.const import UnitOfEnergy
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.entity_registry import async_get as async_get_entity_registry

from .const import DOMAIN, VERSION
from .consumption_analyzer import ConsumptionAnalyzer, ConsumptionPattern
from .recommendation_engine import TariffRecommendationEngine
from .cost_calculator import find_best_tariff_for_consumption

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Set up the smart tariff analyzer sensors."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    config = hass.data[DOMAIN][entry.entry_id]["config"]
    
    _LOGGER.info("Setting up sensor platform for entry: %s", entry.title)
    _LOGGER.info("Full config data: %s", config)
    
    entities = []
    
    # Check if consumption analysis is enabled (handle both boolean and string values)
    enable_analysis_raw = config.get("enable_consumption_analysis", False)
    
    # Convert string values to boolean (common issue with config entries)
    if isinstance(enable_analysis_raw, str):
        enable_analysis = enable_analysis_raw.lower() in ("true", "1", "yes", "on")
        _LOGGER.debug("🔄 Converted string config value '%s' to boolean: %s", enable_analysis_raw, enable_analysis)
    else:
        enable_analysis = bool(enable_analysis_raw)
    
    _LOGGER.info("🔍 Raw config value: %s (type: %s) → Boolean: %s", enable_analysis_raw, type(enable_analysis_raw), enable_analysis)
    
    # INTELLIGENT AUTOMATIC FIX: Only repair when there are actual configuration issues
    needs_repair = False
    repair_reason = ""
    
    # Scenario 1: Consumption analysis is enabled but energy sensor is missing/invalid
    if enable_analysis:
        energy_sensor = config.get("energy_sensor")
        if not energy_sensor:
            needs_repair = True
            repair_reason = "missing energy sensor"
        else:
            # Check if the configured sensor still exists and is valid
            state = hass.states.get(energy_sensor)
            if not state or state.state in ["unknown", "unavailable"]:
                needs_repair = True
                repair_reason = f"configured sensor {energy_sensor} is unavailable"
    
    # Scenario 2: User never configured consumption analysis (legacy setup)
    elif "enable_consumption_analysis" not in config:
        needs_repair = True
        repair_reason = "legacy configuration without consumption analysis setting"
    
    # If consumption analysis is explicitly disabled (False), respect that choice
    # and don't automatically enable it
    
    if needs_repair:
        _LOGGER.warning("🔧 AUTOMATIC REPAIR NEEDED: %s", repair_reason)
        
        # Try to find a suitable energy sensor automatically
        energy_sensor = config.get("energy_sensor")
        if not energy_sensor or (enable_analysis and not hass.states.get(energy_sensor)):
            _LOGGER.info("🔍 Searching for energy sensors automatically...")
            
            # Look for energy sensors in Home Assistant
            suitable_sensors = []
            for entity_id in hass.states.async_entity_ids():
                if entity_id.startswith("sensor."):
                    state = hass.states.get(entity_id)
                    if state and state.attributes.get("device_class") == "energy":
                        # Prefer sensors that look like cumulative totals
                        if not any(word in entity_id.lower() for word in ["daily", "weekly", "monthly", "last_", "period", "today", "yesterday"]):
                            suitable_sensors.append(entity_id)
                    elif ("energy" in entity_id.lower() or "kwh" in entity_id.lower()) and state:
                        unit = state.attributes.get("unit_of_measurement", "")
                        if unit in ["kWh", "Wh"]:
                            # Avoid non-cumulative sensors
                            if not any(word in entity_id.lower() for word in ["daily", "weekly", "monthly", "last_", "period", "today", "yesterday", "_30_days", "_7_days"]):
                                suitable_sensors.append(entity_id)
            
            # Sort sensors by preference (total, energy, cumulative indicators)
            def sensor_priority(sensor_id):
                lower_id = sensor_id.lower()
                if "total" in lower_id:
                    return 1
                elif "cumulative" in lower_id:
                    return 2
                elif "meter" in lower_id:
                    return 3
                elif "home" in lower_id:
                    return 4
                else:
                    return 5
            
            suitable_sensors.sort(key=sensor_priority)
            
            if suitable_sensors:
                energy_sensor = suitable_sensors[0]  # Use the first found
                _LOGGER.info("🎯 Found suitable energy sensor: %s", energy_sensor)
                _LOGGER.info("💡 Available sensors: %s", suitable_sensors[:5])
        
        if energy_sensor:
            _LOGGER.info("🔧 Applying automatic repair with sensor: %s", energy_sensor)
            enable_analysis = True
            
            # Update the config entry to fix this permanently
            try:
                updated_data = dict(config)
                updated_data["enable_consumption_analysis"] = True
                updated_data["energy_sensor"] = energy_sensor
                
                # Only set defaults if not already present
                if "analysis_days" not in updated_data:
                    updated_data["analysis_days"] = 30
                if "tariff_type" not in updated_data:
                    updated_data["tariff_type"] = "bi_hourly"
                
                hass.config_entries.async_update_entry(entry, data=updated_data)
                _LOGGER.info("✅ Configuration repaired successfully")
                _LOGGER.info("✅ Energy sensor: %s", energy_sensor)
                
                # Update the local config dict to use the new values immediately
                config = updated_data
                _LOGGER.info("✅ Using repaired config for current setup")
                
            except Exception as e:
                _LOGGER.error("❌ Failed to repair configuration: %s", e)
        else:
            _LOGGER.warning("⚠️ No suitable energy sensor found for automatic repair")
            _LOGGER.info("💡 Please configure an energy sensor manually in the integration options")
    
    # Log final configuration status
    if enable_analysis:
        energy_sensor = config.get("energy_sensor")
        _LOGGER.info("✅ Consumption analysis enabled with sensor: %s", energy_sensor)
    else:
        _LOGGER.info("📊 Running in basic mode (consumption analysis disabled)")
    
    _LOGGER.info("Consumption analysis enabled: %s (type: %s)", enable_analysis, type(enable_analysis))
    
    # Show detailed config for debugging
    _LOGGER.info("📋 Detailed config values:")
    for key, value in config.items():
        _LOGGER.info("   %s: %s (type: %s)", key, value, type(value))
    
    if enable_analysis:
        _LOGGER.info("✅ ENTERING SENSOR CREATION: Smart tariff analysis sensors")
        _LOGGER.info("🔍 ANALYSIS ENABLED: %s", enable_analysis)
        
        energy_sensor = config.get("energy_sensor")
        analysis_days = config.get("analysis_days", 30)
        tariff_type = config.get("tariff_type", "bi_hourly")
        current_tariff_code = config.get("current_tariff_code")
        
        _LOGGER.info("Analysis config - Energy sensor: %s, Days: %d, Type: %s, Current tariff: %s", 
                     energy_sensor, analysis_days, tariff_type, current_tariff_code)
        
        if not energy_sensor:
            _LOGGER.error("❌ SENSOR CREATION FAILED: No energy sensor configured for consumption analysis")
            _LOGGER.error("❌ This will prevent sensor creation. Please reconfigure the integration.")
            _LOGGER.error("💡 The automatic fix should have added an energy sensor - check the logs above")
            _LOGGER.error("🔍 Current config: %s", dict(config))
            return
        
        # Check if the energy sensor exists
        sensor_state = hass.states.get(energy_sensor)
        if not sensor_state:
            _LOGGER.error("❌ SENSOR CREATION FAILED: Energy sensor %s not found in Home Assistant", energy_sensor)
            _LOGGER.error("❌ Available energy-related sensors: %s", [s for s in hass.states.async_entity_ids() if 'energy' in s or 'kwh' in s.lower()][:10])
            _LOGGER.error("🔍 Total available sensors: %d", len(list(hass.states.async_entity_ids())))
            return
        elif sensor_state.state in ["unknown", "unavailable"]:
            _LOGGER.warning("⚠️ Energy sensor %s is in state '%s' - analysis may not work properly", 
                          energy_sensor, sensor_state.state)
        else:
            _LOGGER.info("✅ Energy sensor %s found with state: %s %s", 
                        energy_sensor, sensor_state.state, sensor_state.attributes.get("unit_of_measurement", ""))
        
        # Create recommendation engine
        recommendation_engine = TariffRecommendationEngine()
        
        # Store the recommendation engine in the domain data
        if "recommendation_engines" not in hass.data[DOMAIN]:
            hass.data[DOMAIN]["recommendation_engines"] = {}
        hass.data[DOMAIN]["recommendation_engines"][entry.entry_id] = recommendation_engine
        
        # Create analysis sensors
        try:
            _LOGGER.info("🏗️ STARTING SENSOR CREATION: About to create analysis sensors")
            _LOGGER.info("🔧 Creating analysis sensors...")
            sensors_to_create = [
                ("ConsumptionAnalysisSensor", ConsumptionAnalysisSensor(
                    coordinator, entry.entry_id, energy_sensor, analysis_days, tariff_type
                )),
                ("TariffRecommendationSensor", TariffRecommendationSensor(
                    coordinator, entry.entry_id, recommendation_engine, config
                )),
                ("PotentialSavingsSensor", PotentialSavingsSensor(
                    coordinator, entry.entry_id, recommendation_engine
                )),
                ("BestTariffComparisonSensor", BestTariffComparisonSensor(
                    coordinator, entry.entry_id, recommendation_engine
                )),
            ]
            
            for sensor_name, sensor_instance in sensors_to_create:
                entities.append(sensor_instance)
                _LOGGER.info("✅ Created %s: %s", sensor_name, sensor_instance.unique_id)
        
        except Exception as e:
            _LOGGER.error("❌ Error creating analysis sensors: %s", e, exc_info=True)
            return
        
        _LOGGER.info("🎉 Successfully created %d smart analysis sensors", len(entities))
    else:
        _LOGGER.warning("❌ Consumption analysis is DISABLED in configuration")
        _LOGGER.warning("❌ Expected config key 'enable_consumption_analysis' = True, got: %s (type: %s)", 
                       config.get("enable_consumption_analysis"), type(config.get("enable_consumption_analysis")))
        _LOGGER.warning("❌ Current config keys: %s", list(config.keys()))
        _LOGGER.info("💡 To enable analysis, delete and recreate the integration with consumption analysis enabled")
    
    if entities:
        _LOGGER.info("📤 Adding %d entities to Home Assistant", len(entities))
        async_add_entities(entities, True)
    else:
        _LOGGER.error("❌ No entities to add - check configuration above")
        _LOGGER.error("❌ This usually means:")
        _LOGGER.error("   1. enable_consumption_analysis is False or missing (current: %s)", enable_analysis)
        _LOGGER.error("   2. energy_sensor is missing or invalid (current: %s)", config.get("energy_sensor"))
        _LOGGER.error("   3. An error occurred during sensor creation")
        _LOGGER.error("🔍 DEBUGGING INFO:")
        _LOGGER.error("   - Enable analysis: %s (type: %s)", enable_analysis, type(enable_analysis))
        _LOGGER.error("   - Raw config value: %s (type: %s)", config.get("enable_consumption_analysis"), type(config.get("enable_consumption_analysis")))
        _LOGGER.error("   - Energy sensor: %s", config.get("energy_sensor"))
        _LOGGER.error("   - All config keys: %s", list(config.keys()))
        _LOGGER.error("💡 Please check the integration configuration in Home Assistant settings")


class ConsumptionAnalysisSensor(CoordinatorEntity, SensorEntity):
    """Sensor for consumption analysis results."""
    
    _attr_icon = "mdi:chart-line"
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_state_class = SensorStateClass.TOTAL
    
    def __init__(self, coordinator, entry_id: str, energy_sensor: str, analysis_days: int, tariff_type: str):
        """Initialize the consumption analysis sensor."""
        super().__init__(coordinator)
        self._energy_sensor = energy_sensor
        self._analysis_days = analysis_days
        self._tariff_type = tariff_type
        
        # Create a clean sensor name from the energy sensor
        sensor_name = energy_sensor.split('.')[-1].replace('_', ' ').title()
        self._attr_name = f"Consumption Analysis {sensor_name}"
        self._attr_unique_id = f"{entry_id}_consumption_analysis"
        
        self._consumption_pattern: Optional[ConsumptionPattern] = None
        self._last_analysis = None
        
        _LOGGER.info("Created consumption analysis sensor: %s", self._attr_name)
        
    async def async_added_to_hass(self):
        """When entity is added to hass."""
        await super().async_added_to_hass()
        
        # Schedule periodic analysis updates every 6 hours
        async_track_time_interval(
            self.hass, self._async_update_analysis, timedelta(hours=6)
        )
        
        # Run initial analysis
        await self._async_update_analysis()
    
    async def _async_update_analysis(self, now=None):
        """Update consumption analysis."""
        try:
            _LOGGER.debug("Starting consumption analysis for %s", self._energy_sensor)
            
            analyzer = ConsumptionAnalyzer(self.hass)
            self._consumption_pattern = await analyzer.analyze_consumption(
                self._energy_sensor, self._analysis_days, self._tariff_type
            )
            
            if self._consumption_pattern:
                self._last_analysis = datetime.now(timezone.utc)
                _LOGGER.info("Consumption analysis completed: %.2f kWh annual, %.1f%% data quality", 
                           self._consumption_pattern.annual_total, 
                           self._consumption_pattern.data_quality * 100)
            else:
                _LOGGER.warning("Consumption analysis failed - no pattern generated")
                
            self.async_write_ha_state()
            
        except Exception as e:
            _LOGGER.error("Error updating consumption analysis for %s: %s", self._energy_sensor, e)
    
    @property
    def native_value(self):
        """Return the annual consumption estimate."""
        if self._consumption_pattern:
            return round(self._consumption_pattern.annual_total, 2)
        return None
    
    @property
    def extra_state_attributes(self):
        """Return consumption analysis attributes."""
        if not self._consumption_pattern:
            return {
                "status": "No analysis available",
                "energy_sensor": self._energy_sensor,
                "analysis_days": self._analysis_days,
                "tariff_type": self._tariff_type
            }
        
        return {
            "energy_sensor": self._energy_sensor,
            "analysis_days": self._analysis_days,
            "tariff_type": self._tariff_type,
            "daily_average_kwh": round(self._consumption_pattern.daily_total, 2),
            "monthly_average_kwh": round(self._consumption_pattern.monthly_total, 2),
            "peak_consumption_kwh": round(self._consumption_pattern.peak_consumption, 2),
            "off_peak_consumption_kwh": round(self._consumption_pattern.off_peak_consumption, 2),
            "intermediate_consumption_kwh": round(self._consumption_pattern.intermediate_consumption, 2),
            "peak_percentage": round(self._consumption_pattern.peak_percentage, 1),
            "off_peak_percentage": round(self._consumption_pattern.off_peak_percentage, 1),
            "intermediate_percentage": round(self._consumption_pattern.intermediate_percentage, 1),
            "data_quality": round(self._consumption_pattern.data_quality * 100, 1),
            "analysis_period_start": self._consumption_pattern.analysis_start.isoformat() if self._consumption_pattern.analysis_start else None,
            "analysis_period_end": self._consumption_pattern.analysis_end.isoformat() if self._consumption_pattern.analysis_end else None,
            "last_updated": self._last_analysis.isoformat() if self._last_analysis else None,
            "hourly_averages": self._consumption_pattern.hourly_averages,
            "daily_averages": self._consumption_pattern.daily_averages,
            "monthly_averages": self._consumption_pattern.monthly_averages,
        }
    
    def get_consumption_pattern(self) -> Optional[ConsumptionPattern]:
        """Get the current consumption pattern for other sensors."""
        return self._consumption_pattern


class TariffRecommendationSensor(CoordinatorEntity, SensorEntity):
    """Sensor for best tariff recommendation."""
    
    _attr_icon = "mdi:lightning-bolt"
    _attr_native_unit_of_measurement = "€/year"
    
    def __init__(self, coordinator, entry_id: str, recommendation_engine: TariffRecommendationEngine, config: Dict):
        """Initialize the tariff recommendation sensor."""
        super().__init__(coordinator)
        self._recommendation_engine = recommendation_engine
        self._config = config
        self._attr_name = "Best Tariff Recommendation"
        self._attr_unique_id = f"{entry_id}_best_tariff"
        self._last_recommendation = None
        
    async def async_added_to_hass(self):
        """When entity is added to hass."""
        await super().async_added_to_hass()
        
        # Schedule periodic recommendation updates every 12 hours
        async_track_time_interval(
            self.hass, self._async_update_recommendation, timedelta(hours=12)
        )
        
        # Run initial recommendation after a delay to let consumption analysis complete
        async_track_time_interval(
            self.hass, self._async_update_recommendation, timedelta(minutes=5)
        )
    
    async def _async_update_recommendation(self, now=None):
        """Update tariff recommendation."""
        try:
            # Find the consumption analysis sensor in the same entry
            consumption_pattern = None
            
            # Look for consumption analysis sensor by checking the recommendation engine's storage
            entry_id = None
            for eid, engine in self.hass.data[DOMAIN].get("recommendation_engines", {}).items():
                if engine == self._recommendation_engine:
                    entry_id = eid
                    break
            
            if entry_id:
                # Try to find the consumption analysis sensor from the same entry
                entity_registry = async_get_entity_registry(self.hass)
                for entity in entity_registry.entities.values():
                    if (entity.config_entry_id == entry_id and 
                        entity.unique_id and 
                        "consumption_analysis" in entity.unique_id):
                        
                        # Get the entity object and consumption pattern
                        platform = entity_registry.async_get_platform(self.hass, entity.platform)
                        if hasattr(platform, 'entities'):
                            for sensor_entity in platform.entities:
                                if (hasattr(sensor_entity, 'unique_id') and 
                                    sensor_entity.unique_id == entity.unique_id and
                                    hasattr(sensor_entity, 'get_consumption_pattern')):
                                    consumption_pattern = sensor_entity.get_consumption_pattern()
                                    if consumption_pattern:
                                        _LOGGER.debug("Found consumption pattern from sensor: %s", entity.entity_id)
                                        break
                        break
            
            if not consumption_pattern:
                _LOGGER.warning("No consumption pattern available for recommendation - skipping")
                _LOGGER.warning("This usually means the consumption analysis hasn't completed yet")
                _LOGGER.warning("The recommendation will be available after the first analysis runs")
                return
            
            # Get tariff data from coordinator
            if not self.coordinator.data or self.coordinator.data.empty:
                _LOGGER.warning("No tariff data available for recommendation")
                return
            
            _LOGGER.debug("Generating tariff recommendation with %d tariffs", len(self.coordinator.data))
            
            # Generate recommendation
            self._last_recommendation = self._recommendation_engine.analyze_and_recommend(
                self.coordinator.data,
                consumption_pattern,
                self._config.get("current_tariff_code"),
                self._config.get("tariff_type", "bi_hourly")
            )
            
            if self._last_recommendation:
                _LOGGER.info("Updated tariff recommendation: %s (€%.2f/year, €%.2f savings)", 
                           self._last_recommendation.recommended_tariff_code,
                           self._last_recommendation.recommended_annual_cost,
                           self._last_recommendation.annual_savings)
            
            self.async_write_ha_state()
            
        except Exception as e:
            _LOGGER.error("Error updating tariff recommendation: %s", e)
    
    @property
    def native_value(self):
        """Return the annual cost of the recommended tariff."""
        if self._last_recommendation:
            return round(self._last_recommendation.recommended_annual_cost, 2)
        return None
    
    @property
    def extra_state_attributes(self):
        """Return recommendation attributes."""
        if not self._last_recommendation:
            return {
                "status": "No recommendation available",
                "current_tariff": self._config.get("current_tariff_code"),
            }
        
        return {
            "recommended_tariff_code": self._last_recommendation.recommended_tariff_code,
            "recommended_tariff_name": self._last_recommendation.recommended_tariff_name,
            "recommended_provider": self._last_recommendation.recommended_comercializador,
            "annual_cost": self._last_recommendation.recommended_annual_cost,
            "monthly_cost": self._last_recommendation.recommended_monthly_cost,
            "current_tariff_code": self._last_recommendation.current_tariff_code,
            "current_annual_cost": self._last_recommendation.current_annual_cost,
            "annual_savings": self._last_recommendation.annual_savings,
            "monthly_savings": self._last_recommendation.monthly_savings,
            "savings_percentage": self._last_recommendation.savings_percentage,
            "tariffs_analyzed": self._last_recommendation.total_tariffs_analyzed,
            "data_quality": self._last_recommendation.consumption_analysis_quality * 100,
            "analysis_timestamp": self._last_recommendation.analysis_timestamp,
            "fixed_cost_annual": self._last_recommendation.recommended_fixed_cost_annual,
            "energy_cost_annual": self._last_recommendation.recommended_energy_cost_annual,
            "additional_cost_annual": self._last_recommendation.recommended_additional_cost_annual,
            "top_alternatives": self._last_recommendation.top_alternatives[:3],  # Top 3 alternatives
        }


class PotentialSavingsSensor(CoordinatorEntity, SensorEntity):
    """Sensor for potential annual savings."""
    
    _attr_icon = "mdi:piggy-bank"
    _attr_native_unit_of_measurement = "€/year"
    
    def __init__(self, coordinator, entry_id: str, recommendation_engine: TariffRecommendationEngine):
        """Initialize the potential savings sensor."""
        super().__init__(coordinator)
        self._recommendation_engine = recommendation_engine
        self._attr_name = "Potential Annual Savings"
        self._attr_unique_id = f"{entry_id}_potential_savings"
    
    @property
    def native_value(self):
        """Return the potential annual savings."""
        if self._recommendation_engine.last_recommendation:
            return round(self._recommendation_engine.last_recommendation.annual_savings, 2)
        return None
    
    @property
    def extra_state_attributes(self):
        """Return savings breakdown."""
        if not self._recommendation_engine.last_recommendation:
            return {"status": "No savings calculation available"}
        
        rec = self._recommendation_engine.last_recommendation
        return {
            "monthly_savings": round(rec.monthly_savings, 2),
            "savings_percentage": round(rec.savings_percentage, 1),
            "current_annual_cost": rec.current_annual_cost,
            "recommended_annual_cost": rec.recommended_annual_cost,
            "current_tariff": rec.current_tariff_code,
            "recommended_tariff": rec.recommended_tariff_code,
            "payback_period_years": round(rec.current_annual_cost / rec.recommended_annual_cost, 1) if rec.recommended_annual_cost > 0 else None,
        }


class BestTariffComparisonSensor(CoordinatorEntity, SensorEntity):
    """Sensor for detailed tariff comparison."""
    
    _attr_icon = "mdi:compare"
    
    def __init__(self, coordinator, entry_id: str, recommendation_engine: TariffRecommendationEngine):
        """Initialize the comparison sensor."""
        super().__init__(coordinator)
        self._recommendation_engine = recommendation_engine
        self._attr_name = "Tariff Comparison"
        self._attr_unique_id = f"{entry_id}_tariff_comparison"
    
    @property
    def native_value(self):
        """Return the number of tariffs compared."""
        if self._recommendation_engine.last_recommendation:
            return self._recommendation_engine.last_recommendation.total_tariffs_analyzed
        return None
    
    @property
    def extra_state_attributes(self):
        """Return detailed comparison data."""
        if not self._recommendation_engine.last_recommendation:
            return {"status": "No comparison available"}
        
        return self._recommendation_engine.get_detailed_comparison()