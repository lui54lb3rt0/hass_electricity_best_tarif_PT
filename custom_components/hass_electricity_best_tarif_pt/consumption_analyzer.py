"""Consumption analyzer for electricity usage patterns."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import statistics

from homeassistant.core import HomeAssistant
from homeassistant.components.recorder import get_instance, history
from homeassistant.util import dt as dt_util

from .power_to_energy_converter import (
    PowerToEnergyConverter, 
    get_sensor_type_from_entity,
    get_expected_update_interval
)

_LOGGER = logging.getLogger(__name__)

# Portuguese tariff periods (typical bi-hourly and tri-hourly schedules)
TARIFF_PERIODS = {
    "bi_hourly": {
        "peak": [
            (9, 30, 12, 0),   # 09:30 - 12:00
            (18, 30, 21, 0),  # 18:30 - 21:00
        ],
        "off_peak": [
            (0, 0, 9, 30),    # 00:00 - 09:30
            (12, 0, 18, 30),  # 12:00 - 18:30
            (21, 0, 24, 0),   # 21:00 - 24:00
        ]
    },
    "tri_hourly": {
        "peak": [
            (9, 30, 12, 0),   # 09:30 - 12:00
            (18, 30, 21, 0),  # 18:30 - 21:00
        ],
        "intermediate": [
            (8, 0, 9, 30),    # 08:00 - 09:30
            (12, 0, 18, 30),  # 12:00 - 18:30
            (21, 0, 22, 0),   # 21:00 - 22:00
        ],
        "off_peak": [
            (0, 0, 8, 0),     # 00:00 - 08:00
            (22, 0, 24, 0),   # 22:00 - 24:00
        ]
    }
}

# Weekend and holiday adjustments (off-peak rates typically apply)
WEEKEND_ADJUSTMENT = "off_peak"


class ConsumptionPattern:
    """Represents consumption patterns for different tariff periods."""
    
    def __init__(self):
        self.daily_total: float = 0.0
        self.monthly_total: float = 0.0
        self.annual_total: float = 0.0
        
        # Consumption by tariff period
        self.peak_consumption: float = 0.0
        self.intermediate_consumption: float = 0.0
        self.off_peak_consumption: float = 0.0
        
        # Percentage distribution
        self.peak_percentage: float = 0.0
        self.intermediate_percentage: float = 0.0
        self.off_peak_percentage: float = 0.0
        
        # Time-based patterns
        self.hourly_averages: Dict[int, float] = {}
        self.daily_averages: Dict[int, float] = {}  # 0=Monday, 6=Sunday
        self.monthly_averages: Dict[int, float] = {}
        
        # Analysis metadata
        self.analysis_start: datetime = None
        self.analysis_end: datetime = None
        self.days_analyzed: int = 0
        self.data_quality: float = 0.0  # 0-1, percentage of expected data points


class ConsumptionAnalyzer:
    """Analyzes electricity consumption patterns from Home Assistant sensors."""
    
    def __init__(self, hass: HomeAssistant):
        self.hass = hass
        self._recorder = get_instance(hass)
        self._power_converter = PowerToEnergyConverter(hass)
    
    async def analyze_consumption(
        self,
        sensor_entity_id: str,
        days_back: int = 30,
        tariff_type: str = "bi_hourly"
    ) -> Optional[ConsumptionPattern]:
        """
        Analyze consumption patterns from either a power sensor (W) or energy sensor (kWh).
        
        Args:
            sensor_entity_id: Entity ID of the power/energy sensor
            days_back: Number of days to analyze
            tariff_type: "bi_hourly" or "tri_hourly"
        
        Returns:
            ConsumptionPattern object with analyzed data
        """
        try:
            end_time = dt_util.utcnow()
            start_time = end_time - timedelta(days=days_back)
            
            # Determine sensor type (power vs energy)
            sensor_type = get_sensor_type_from_entity(self.hass, sensor_entity_id)
            
            _LOGGER.debug(
                "🔍 Analyzing consumption for %s (type: %s) from %s to %s (%d days)",
                sensor_entity_id, sensor_type, start_time, end_time, days_back
            )
            
            # Get consumption data based on sensor type
            if sensor_type == "power":
                consumption_data = await self._power_converter.convert_power_to_energy_intervals(
                    sensor_entity_id, start_time, end_time
                )
            elif sensor_type == "energy":
                # Get historical data and convert cumulative to intervals
                history_data = await self._get_energy_history(
                    sensor_entity_id, start_time, end_time
                )
                consumption_data = self._calculate_consumption_intervals(history_data)
            else:
                _LOGGER.warning("⚠️ Unknown sensor type for %s, trying as energy sensor", sensor_entity_id)
                history_data = await self._get_energy_history(
                    sensor_entity_id, start_time, end_time
                )
                consumption_data = self._calculate_consumption_intervals(history_data)
            
            if not consumption_data:
                _LOGGER.warning("⚠️ No consumption data could be calculated for sensor %s", sensor_entity_id)
                return None
            
            # Analyze patterns
            pattern = ConsumptionPattern()
            pattern.analysis_start = start_time
            pattern.analysis_end = end_time
            pattern.days_analyzed = days_back
            
            await self._analyze_tariff_periods(consumption_data, pattern, tariff_type)
            await self._analyze_time_patterns(consumption_data, pattern)
            await self._calculate_totals(consumption_data, pattern)
            
            # Calculate data quality based on sensor type
            expected_interval = get_expected_update_interval(sensor_type)
            if sensor_type == "power":
                # For power sensors, we need to get original power data for quality assessment
                power_data = await self._power_converter._get_power_history(
                    sensor_entity_id, start_time, end_time
                )
                pattern.data_quality = self._power_converter.estimate_data_quality(
                    power_data, expected_interval
                )
            else:
                # For energy sensors, estimate based on data points
                expected_points = days_back * 24 * (60 / expected_interval)
                actual_points = len(consumption_data)
                pattern.data_quality = min(1.0, actual_points / expected_points)
            
            _LOGGER.info(
                "✅ Consumption analysis complete for %s (%s): %.2f kWh total, %.1f%% data quality",
                sensor_entity_id, sensor_type, pattern.annual_total, pattern.data_quality * 100
            )
            
            return pattern
            
        except Exception as e:
            _LOGGER.error("❌ Error analyzing consumption for %s: %s", sensor_entity_id, e)
            return None
    
    async def _get_energy_history(
        self, entity_id: str, start_time: datetime, end_time: datetime
    ) -> List[Tuple[datetime, float]]:
        """Get historical energy data from recorder."""
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
                        value = float(state.state)
                        data_points.append((timestamp, value))
                except (ValueError, TypeError):
                    continue
            
            # Sort by timestamp
            data_points.sort(key=lambda x: x[0])
            
            _LOGGER.debug(
                "Retrieved %d data points for %s between %s and %s",
                len(data_points), entity_id, start_time, end_time
            )
            
            return data_points
            
        except Exception as e:
            _LOGGER.error("Error retrieving history for %s: %s", entity_id, e)
            return []
    
    def _calculate_consumption_intervals(
        self, history_data: List[Tuple[datetime, float]]
    ) -> List[Tuple[datetime, float]]:
        """Calculate consumption intervals from cumulative energy data."""
        if len(history_data) < 2:
            return []
        
        intervals = []
        prev_timestamp, prev_value = history_data[0]
        
        for timestamp, value in history_data[1:]:
            # Calculate time interval in hours
            time_diff = (timestamp - prev_timestamp).total_seconds() / 3600
            
            # Calculate consumption (handle meter resets)
            if value >= prev_value and time_diff > 0 and time_diff <= 24:
                consumption = value - prev_value
                # Convert to hourly rate for normalization
                hourly_consumption = consumption / time_diff
                intervals.append((timestamp, hourly_consumption))
            
            prev_timestamp, prev_value = timestamp, value
        
        _LOGGER.debug("Calculated %d consumption intervals", len(intervals))
        return intervals
    
    async def _analyze_tariff_periods(
        self, consumption_data: List[Tuple[datetime, float]], 
        pattern: ConsumptionPattern, 
        tariff_type: str
    ):
        """Analyze consumption by tariff periods (peak, off-peak, intermediate)."""
        if tariff_type not in TARIFF_PERIODS:
            _LOGGER.warning("Unknown tariff type: %s", tariff_type)
            return
        
        periods = TARIFF_PERIODS[tariff_type]
        
        peak_total = 0.0
        intermediate_total = 0.0
        off_peak_total = 0.0
        total_consumption = 0.0
        
        for timestamp, consumption in consumption_data:
            local_time = dt_util.as_local(timestamp)
            hour = local_time.hour
            minute = local_time.minute
            weekday = local_time.weekday()  # 0=Monday, 6=Sunday
            
            # Weekend adjustment
            is_weekend = weekday >= 5  # Saturday=5, Sunday=6
            
            period = self._get_tariff_period(hour, minute, periods, is_weekend)
            
            if period == "peak":
                peak_total += consumption
            elif period == "intermediate":
                intermediate_total += consumption
            else:  # off_peak
                off_peak_total += consumption
            
            total_consumption += consumption
        
        # Store totals
        pattern.peak_consumption = peak_total
        pattern.intermediate_consumption = intermediate_total
        pattern.off_peak_consumption = off_peak_total
        
        # Calculate percentages
        if total_consumption > 0:
            pattern.peak_percentage = (peak_total / total_consumption) * 100
            pattern.intermediate_percentage = (intermediate_total / total_consumption) * 100
            pattern.off_peak_percentage = (off_peak_total / total_consumption) * 100
        
        _LOGGER.debug(
            "Tariff period analysis: Peak=%.2f%%, Intermediate=%.2f%%, Off-peak=%.2f%%",
            pattern.peak_percentage, pattern.intermediate_percentage, pattern.off_peak_percentage
        )
    
    def _get_tariff_period(
        self, hour: int, minute: int, periods: Dict, is_weekend: bool
    ) -> str:
        """Determine tariff period for given time."""
        if is_weekend:
            return WEEKEND_ADJUSTMENT
        
        time_minutes = hour * 60 + minute
        
        # Check peak periods
        for start_h, start_m, end_h, end_m in periods.get("peak", []):
            start_minutes = start_h * 60 + start_m
            end_minutes = end_h * 60 + end_m
            if start_minutes <= time_minutes < end_minutes:
                return "peak"
        
        # Check intermediate periods (if exists)
        if "intermediate" in periods:
            for start_h, start_m, end_h, end_m in periods.get("intermediate", []):
                start_minutes = start_h * 60 + start_m
                end_minutes = end_h * 60 + end_m
                if start_minutes <= time_minutes < end_minutes:
                    return "intermediate"
        
        # Default to off-peak
        return "off_peak"
    
    async def _analyze_time_patterns(
        self, consumption_data: List[Tuple[datetime, float]], 
        pattern: ConsumptionPattern
    ):
        """Analyze consumption patterns by hour, day, and month."""
        hourly_data = {}
        daily_data = {}
        monthly_data = {}
        
        for timestamp, consumption in consumption_data:
            local_time = dt_util.as_local(timestamp)
            hour = local_time.hour
            day = local_time.weekday()  # 0=Monday
            month = local_time.month
            
            # Collect hourly data
            if hour not in hourly_data:
                hourly_data[hour] = []
            hourly_data[hour].append(consumption)
            
            # Collect daily data
            if day not in daily_data:
                daily_data[day] = []
            daily_data[day].append(consumption)
            
            # Collect monthly data
            if month not in monthly_data:
                monthly_data[month] = []
            monthly_data[month].append(consumption)
        
        # Calculate averages
        pattern.hourly_averages = {
            hour: statistics.mean(values) for hour, values in hourly_data.items()
        }
        
        pattern.daily_averages = {
            day: statistics.mean(values) for day, values in daily_data.items()
        }
        
        pattern.monthly_averages = {
            month: statistics.mean(values) for month, values in monthly_data.items()
        }
        
        _LOGGER.debug("Time pattern analysis complete")
    
    async def _calculate_totals(
        self, consumption_data: List[Tuple[datetime, float]], 
        pattern: ConsumptionPattern
    ):
        """Calculate daily, monthly, and annual consumption totals."""
        if not consumption_data:
            return
        
        total_hourly_consumption = sum(consumption for _, consumption in consumption_data)
        hours_analyzed = len(consumption_data)
        
        if hours_analyzed > 0:
            # Calculate average hourly consumption
            avg_hourly = total_hourly_consumption / hours_analyzed
            
            # Extrapolate to daily, monthly, annual
            pattern.daily_total = avg_hourly * 24
            pattern.monthly_total = pattern.daily_total * 30.44  # Average days per month
            pattern.annual_total = pattern.daily_total * 365.25
        
        _LOGGER.debug(
            "Calculated totals - Daily: %.2f kWh, Monthly: %.2f kWh, Annual: %.2f kWh",
            pattern.daily_total, pattern.monthly_total, pattern.annual_total
        )


def estimate_consumption_for_periods(
    pattern: ConsumptionPattern, 
    tariff_type: str = "bi_hourly"
) -> Dict[str, float]:
    """
    Estimate consumption for each tariff period based on analysis.
    
    Returns:
        Dictionary with period names as keys and annual consumption (kWh) as values
    """
    total_annual = pattern.annual_total
    
    if tariff_type == "tri_hourly":
        return {
            "peak": total_annual * (pattern.peak_percentage / 100),
            "intermediate": total_annual * (pattern.intermediate_percentage / 100),
            "off_peak": total_annual * (pattern.off_peak_percentage / 100)
        }
    else:  # bi_hourly
        return {
            "peak": total_annual * (pattern.peak_percentage / 100),
            "off_peak": total_annual * ((pattern.intermediate_percentage + pattern.off_peak_percentage) / 100)
        }