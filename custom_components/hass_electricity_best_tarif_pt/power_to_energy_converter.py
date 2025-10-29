"""Power to Energy Converter for consumption analysis."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from homeassistant.core import HomeAssistant
from homeassistant.components.recorder import get_instance, history
from homeassistant.util import dt as dt_util

_LOGGER = logging.getLogger(__name__)


class PowerToEnergyConverter:
    """Converts power sensor data (W) to energy consumption (kWh) for analysis."""
    
    def __init__(self, hass: HomeAssistant):
        self.hass = hass
        self._recorder = get_instance(hass)
    
    async def convert_power_to_energy_intervals(
        self,
        power_sensor_entity_id: str,
        start_time: datetime,
        end_time: datetime
    ) -> List[Tuple[datetime, float]]:
        """
        Convert power sensor readings to energy consumption intervals.
        
        Args:
            power_sensor_entity_id: Entity ID of the power sensor (W)
            start_time: Start of analysis period
            end_time: End of analysis period
        
        Returns:
            List of (timestamp, hourly_consumption_kwh) tuples
        """
        try:
            _LOGGER.debug(
                "🔌 Converting power data from %s to energy intervals (%s to %s)",
                power_sensor_entity_id, start_time, end_time
            )
            
            # Get historical power data
            power_data = await self._get_power_history(
                power_sensor_entity_id, start_time, end_time
            )
            
            if not power_data:
                _LOGGER.warning("⚠️ No power data found for sensor %s", power_sensor_entity_id)
                return []
            
            # Convert power readings to energy intervals
            energy_intervals = self._calculate_energy_from_power(power_data)
            
            _LOGGER.info(
                "✅ Converted %d power readings to %d energy intervals for %s",
                len(power_data), len(energy_intervals), power_sensor_entity_id
            )
            
            return energy_intervals
            
        except Exception as e:
            _LOGGER.error("❌ Error converting power to energy for %s: %s", power_sensor_entity_id, e)
            return []
    
    async def _get_power_history(
        self, entity_id: str, start_time: datetime, end_time: datetime
    ) -> List[Tuple[datetime, float]]:
        """Get historical power data from recorder."""
        try:
            # Get historical states
            history_list = await self.hass.async_add_executor_job(
                history.state_changes_during_period,
                self.hass,
                start_time,
                end_time,
                entity_id
            )
            
            if entity_id not in history_list:
                return []
            
            states = history_list[entity_id]
            
            # Convert to timestamp, value tuples
            data_points = []
            for state in states:
                try:
                    if state.state not in (None, "unknown", "unavailable"):
                        timestamp = state.last_updated
                        # Convert power to float (assuming Watts)
                        power_watts = float(state.state)
                        data_points.append((timestamp, power_watts))
                except (ValueError, TypeError):
                    continue
            
            # Sort by timestamp
            data_points.sort(key=lambda x: x[0])
            
            _LOGGER.debug(
                "📊 Retrieved %d power readings for %s between %s and %s",
                len(data_points), entity_id, start_time, end_time
            )
            
            return data_points
            
        except Exception as e:
            _LOGGER.error("❌ Error retrieving power history for %s: %s", entity_id, e)
            return []
    
    def _calculate_energy_from_power(
        self, power_data: List[Tuple[datetime, float]]
    ) -> List[Tuple[datetime, float]]:
        """
        Calculate energy consumption from power readings using trapezoidal integration.
        
        This method integrates power over time to get energy consumption.
        Formula: Energy (kWh) = Power (W) × Time (h) / 1000
        """
        if len(power_data) < 2:
            return []
        
        energy_intervals = []
        
        for i in range(1, len(power_data)):
            timestamp1, power1 = power_data[i-1]
            timestamp2, power2 = power_data[i]
            
            # Calculate time interval in hours
            time_diff_hours = (timestamp2 - timestamp1).total_seconds() / 3600
            
            # Skip intervals that are too long (likely data gaps)
            if time_diff_hours > 4:  # More than 4 hours gap
                continue
            
            # Skip very short intervals (likely duplicate readings)
            if time_diff_hours < 0.001:  # Less than 3.6 seconds
                continue
            
            # Calculate energy using trapezoidal rule
            # Average power over the interval × time = energy
            avg_power_watts = (power1 + power2) / 2
            
            # Convert to kWh and normalize to hourly rate
            energy_kwh = (avg_power_watts * time_diff_hours) / 1000
            hourly_rate_kwh = energy_kwh / time_diff_hours if time_diff_hours > 0 else 0
            
            # Use the end timestamp for the interval
            energy_intervals.append((timestamp2, hourly_rate_kwh))
        
        _LOGGER.debug(
            "⚡ Calculated %d energy intervals from power data using trapezoidal integration",
            len(energy_intervals)
        )
        
        return energy_intervals
    
    def estimate_data_quality(
        self, power_data: List[Tuple[datetime, float]], 
        expected_interval_minutes: int = 15
    ) -> float:
        """
        Estimate data quality based on regularity of power readings.
        
        Args:
            power_data: List of (timestamp, power) tuples
            expected_interval_minutes: Expected reading interval in minutes
        
        Returns:
            Quality score between 0.0 and 1.0
        """
        if len(power_data) < 2:
            return 0.0
        
        total_time = (power_data[-1][0] - power_data[0][0]).total_seconds()
        expected_readings = total_time / (expected_interval_minutes * 60)
        actual_readings = len(power_data)
        
        # Calculate quality based on reading density
        quality = min(1.0, actual_readings / expected_readings)
        
        # Penalty for large gaps in data
        gap_penalty = 0.0
        for i in range(1, len(power_data)):
            time_diff = (power_data[i][0] - power_data[i-1][0]).total_seconds() / 60
            if time_diff > expected_interval_minutes * 3:  # Gap > 3x expected interval
                gap_penalty += 0.1
        
        final_quality = max(0.0, quality - gap_penalty)
        
        _LOGGER.debug(
            "📈 Power data quality: %.1f%% (actual: %d, expected: %d readings, gap penalty: %.1f)",
            final_quality * 100, actual_readings, int(expected_readings), gap_penalty
        )
        
        return final_quality


def get_sensor_type_from_entity(hass: HomeAssistant, entity_id: str) -> str:
    """
    Determine if a sensor is power (W) or energy (kWh) based on its attributes.
    
    Returns:
        "power" for power sensors (W), "energy" for energy sensors (kWh), "unknown" if unclear
    """
    state = hass.states.get(entity_id)
    if not state:
        return "unknown"
    
    # Check unit of measurement
    unit = state.attributes.get("unit_of_measurement", "").lower()
    
    if unit in ["w", "watt", "watts"]:
        return "power"
    elif unit in ["kwh", "wh", "mwh"]:
        return "energy"
    
    # Check device class
    device_class = state.attributes.get("device_class", "").lower()
    if device_class == "power":
        return "power"
    elif device_class == "energy":
        return "energy"
    
    # Check entity ID patterns
    entity_lower = entity_id.lower()
    if any(keyword in entity_lower for keyword in ["power", "_w_", "watts"]):
        return "power"
    elif any(keyword in entity_lower for keyword in ["energy", "kwh", "consumption"]):
        return "energy"
    
    return "unknown"


def get_expected_update_interval(sensor_type: str) -> int:
    """
    Get expected update interval in minutes based on sensor type.
    
    Args:
        sensor_type: "power" or "energy"
    
    Returns:
        Expected interval in minutes
    """
    if sensor_type == "power":
        return 1  # Power sensors typically update every minute
    elif sensor_type == "energy":
        return 15  # Energy sensors typically update every 15 minutes
    else:
        return 5  # Default to 5 minutes for unknown sensors