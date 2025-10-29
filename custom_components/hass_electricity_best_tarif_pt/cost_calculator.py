"""Cost calculation engine for electricity tariffs."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import pandas as pd

from .consumption_analyzer import ConsumptionPattern, estimate_consumption_for_periods

_LOGGER = logging.getLogger(__name__)


@dataclass
class TariffCosts:
    """Represents calculated costs for a tariff."""
    tariff_code: str
    tariff_name: str
    comercializador: str
    
    # Cost components (annual)
    fixed_cost_annual: float = 0.0
    energy_cost_annual: float = 0.0
    additional_services_cost_annual: float = 0.0
    total_cost_annual: float = 0.0
    
    # Monthly equivalents
    fixed_cost_monthly: float = 0.0
    energy_cost_monthly: float = 0.0
    total_cost_monthly: float = 0.0
    
    # Breakdown by periods
    peak_cost: float = 0.0
    intermediate_cost: float = 0.0
    off_peak_cost: float = 0.0
    
    # Consumption used for calculation
    annual_consumption_kwh: float = 0.0
    peak_consumption_kwh: float = 0.0
    intermediate_consumption_kwh: float = 0.0
    off_peak_consumption_kwh: float = 0.0
    
    # Metadata
    billing_cycle: str = ""
    power_rating: str = ""
    energy_type: str = ""
    calculation_notes: List[str] = None
    
    def __post_init__(self):
        if self.calculation_notes is None:
            self.calculation_notes = []
        
        # Calculate monthly values
        self.fixed_cost_monthly = self.fixed_cost_annual / 12
        self.energy_cost_monthly = self.energy_cost_annual / 12
        self.total_cost_monthly = self.total_cost_annual / 12


@dataclass
class TariffComparison:
    """Comparison between tariffs."""
    current_tariff: TariffCosts
    recommended_tariff: TariffCosts
    annual_savings: float
    monthly_savings: float
    savings_percentage: float
    
    # Detailed comparison
    fixed_cost_difference: float = 0.0
    energy_cost_difference: float = 0.0
    total_cost_difference: float = 0.0


class TariffCostCalculator:
    """Calculates costs for electricity tariffs based on consumption patterns."""
    
    # Column name mappings for different CSV formats
    TERM_FIXED_COLS = ["Termo fixo (€/dia)", "TF", "termo_fixo_eur_dia"]
    TERM_ENERGY_COLS = {
        "simple": ["TV", "termo_de_energia_eur_kwh_simples"],
        "peak": ["TVP", "termo_de_energia_eur_kwh_ponta"],
        "intermediate": ["TVC", "termo_de_energia_eur_kwh_cheias"],
        "off_peak": ["TVV", "termo_de_energia_eur_kwh_vazio"]
    }
    ADDITIONAL_SERVICES_COLS = ["CustoServicos_c/IVA (€/ano)", "custo_servicos_com_iva_eur_ano"]
    POWER_RATING_COLS = ["Potência contratada", "Potência contratada__norm", "potencia_norm"]
    BILLING_CYCLE_COLS = ["Ciclo de contagem", "ciclo_de_contagem"]
    
    def __init__(self):
        pass
    
    def calculate_tariff_costs(
        self,
        tariff_data: pd.Series,
        consumption_pattern: ConsumptionPattern,
        tariff_type: str = "bi_hourly"
    ) -> Optional[TariffCosts]:
        """
        Calculate annual costs for a specific tariff based on consumption pattern.
        
        Args:
            tariff_data: Pandas Series with tariff information
            consumption_pattern: Analyzed consumption pattern
            tariff_type: "bi_hourly" or "tri_hourly"
        
        Returns:
            TariffCosts object with calculated costs
        """
        try:
            # Extract basic tariff info
            tariff_code = self._get_value(tariff_data, ["Código da oferta comercial", "codigo_original"])
            tariff_name = self._get_value(tariff_data, ["Nome da oferta comercial", "nome_oferta_comercial"])
            comercializador = self._get_value(tariff_data, ["Comercializador", "comercializador"])
            
            if not tariff_code:
                _LOGGER.warning("No tariff code found in data")
                return None
            
            # Create result object
            costs = TariffCosts(
                tariff_code=tariff_code,
                tariff_name=tariff_name or f"Tarifa {tariff_code}",
                comercializador=comercializador or "Unknown"
            )
            
            # Get consumption by periods
            period_consumption = estimate_consumption_for_periods(consumption_pattern, tariff_type)
            costs.annual_consumption_kwh = consumption_pattern.annual_total
            costs.peak_consumption_kwh = period_consumption.get("peak", 0)
            costs.intermediate_consumption_kwh = period_consumption.get("intermediate", 0)
            costs.off_peak_consumption_kwh = period_consumption.get("off_peak", 0)
            
            # Calculate fixed costs
            fixed_cost_daily = self._get_numeric_value(tariff_data, self.TERM_FIXED_COLS)
            if fixed_cost_daily:
                costs.fixed_cost_annual = fixed_cost_daily * 365.25
            else:
                costs.calculation_notes.append("Fixed term not found - using 0")
            
            # Calculate energy costs based on tariff type
            if tariff_type == "tri_hourly":
                costs.energy_cost_annual, energy_breakdown = self._calculate_tri_hourly_costs(
                    tariff_data, period_consumption
                )
                costs.peak_cost = energy_breakdown.get("peak", 0)
                costs.intermediate_cost = energy_breakdown.get("intermediate", 0)
                costs.off_peak_cost = energy_breakdown.get("off_peak", 0)
            else:  # bi_hourly
                costs.energy_cost_annual, energy_breakdown = self._calculate_bi_hourly_costs(
                    tariff_data, period_consumption
                )
                costs.peak_cost = energy_breakdown.get("peak", 0)
                costs.off_peak_cost = energy_breakdown.get("off_peak", 0)
            
            # Additional services cost
            additional_services = self._get_numeric_value(tariff_data, self.ADDITIONAL_SERVICES_COLS)
            if additional_services:
                costs.additional_services_cost_annual = additional_services
            
            # Total cost
            costs.total_cost_annual = (
                costs.fixed_cost_annual + 
                costs.energy_cost_annual + 
                costs.additional_services_cost_annual
            )
            
            # Metadata
            costs.power_rating = str(self._get_value(tariff_data, self.POWER_RATING_COLS) or "")
            costs.billing_cycle = str(self._get_value(tariff_data, self.BILLING_CYCLE_COLS) or "")
            costs.energy_type = str(self._get_value(tariff_data, ["Fornecimento", "fornecimento"]) or "")
            
            _LOGGER.debug(
                "Calculated costs for %s: €%.2f/year (Fixed: €%.2f, Energy: €%.2f)",
                tariff_code, costs.total_cost_annual, costs.fixed_cost_annual, costs.energy_cost_annual
            )
            
            return costs
            
        except Exception as e:
            _LOGGER.error("Error calculating costs for tariff: %s", e)
            return None
    
    def _calculate_tri_hourly_costs(
        self, tariff_data: pd.Series, period_consumption: Dict[str, float]
    ) -> Tuple[float, Dict[str, float]]:
        """Calculate energy costs for tri-hourly tariff."""
        total_cost = 0.0
        breakdown = {}
        
        # Peak period
        peak_rate = self._get_numeric_value(tariff_data, self.TERM_ENERGY_COLS["peak"])
        peak_consumption = period_consumption.get("peak", 0)
        if peak_rate and peak_consumption:
            peak_cost = peak_rate * peak_consumption
            total_cost += peak_cost
            breakdown["peak"] = peak_cost
        
        # Intermediate period
        intermediate_rate = self._get_numeric_value(tariff_data, self.TERM_ENERGY_COLS["intermediate"])
        intermediate_consumption = period_consumption.get("intermediate", 0)
        if intermediate_rate and intermediate_consumption:
            intermediate_cost = intermediate_rate * intermediate_consumption
            total_cost += intermediate_cost
            breakdown["intermediate"] = intermediate_cost
        
        # Off-peak period
        off_peak_rate = self._get_numeric_value(tariff_data, self.TERM_ENERGY_COLS["off_peak"])
        off_peak_consumption = period_consumption.get("off_peak", 0)
        if off_peak_rate and off_peak_consumption:
            off_peak_cost = off_peak_rate * off_peak_consumption
            total_cost += off_peak_cost
            breakdown["off_peak"] = off_peak_cost
        
        # Fallback to simple rate if periods not available
        if total_cost == 0:
            simple_rate = self._get_numeric_value(tariff_data, self.TERM_ENERGY_COLS["simple"])
            if simple_rate:
                total_consumption = sum(period_consumption.values())
                total_cost = simple_rate * total_consumption
                breakdown["simple"] = total_cost
        
        return total_cost, breakdown
    
    def _calculate_bi_hourly_costs(
        self, tariff_data: pd.Series, period_consumption: Dict[str, float]
    ) -> Tuple[float, Dict[str, float]]:
        """Calculate energy costs for bi-hourly tariff."""
        total_cost = 0.0
        breakdown = {}
        
        # Peak period
        peak_rate = self._get_numeric_value(tariff_data, self.TERM_ENERGY_COLS["peak"])
        peak_consumption = period_consumption.get("peak", 0)
        if peak_rate and peak_consumption:
            peak_cost = peak_rate * peak_consumption
            total_cost += peak_cost
            breakdown["peak"] = peak_cost
        
        # Off-peak period (includes intermediate if it exists)
        off_peak_rate = self._get_numeric_value(tariff_data, self.TERM_ENERGY_COLS["off_peak"])
        off_peak_consumption = period_consumption.get("off_peak", 0)
        if off_peak_rate and off_peak_consumption:
            off_peak_cost = off_peak_rate * off_peak_consumption
            total_cost += off_peak_cost
            breakdown["off_peak"] = off_peak_cost
        
        # Fallback to simple rate if periods not available
        if total_cost == 0:
            simple_rate = self._get_numeric_value(tariff_data, self.TERM_ENERGY_COLS["simple"])
            if simple_rate:
                total_consumption = sum(period_consumption.values())
                total_cost = simple_rate * total_consumption
                breakdown["simple"] = total_cost
        
        return total_cost, breakdown
    
    def calculate_all_tariffs(
        self,
        tariffs_df: pd.DataFrame,
        consumption_pattern: ConsumptionPattern,
        tariff_type: str = "bi_hourly"
    ) -> List[TariffCosts]:
        """Calculate costs for all tariffs in the DataFrame."""
        results = []
        
        for _, tariff_row in tariffs_df.iterrows():
            costs = self.calculate_tariff_costs(tariff_row, consumption_pattern, tariff_type)
            if costs:
                results.append(costs)
        
        # Sort by total annual cost
        results.sort(key=lambda x: x.total_cost_annual)
        
        _LOGGER.info("Calculated costs for %d tariffs", len(results))
        return results
    
    def compare_tariffs(
        self, current_tariff: TariffCosts, best_tariff: TariffCosts
    ) -> TariffComparison:
        """Compare two tariffs and calculate savings."""
        annual_savings = current_tariff.total_cost_annual - best_tariff.total_cost_annual
        monthly_savings = annual_savings / 12
        
        savings_percentage = 0.0
        if current_tariff.total_cost_annual > 0:
            savings_percentage = (annual_savings / current_tariff.total_cost_annual) * 100
        
        return TariffComparison(
            current_tariff=current_tariff,
            recommended_tariff=best_tariff,
            annual_savings=annual_savings,
            monthly_savings=monthly_savings,
            savings_percentage=savings_percentage,
            fixed_cost_difference=current_tariff.fixed_cost_annual - best_tariff.fixed_cost_annual,
            energy_cost_difference=current_tariff.energy_cost_annual - best_tariff.energy_cost_annual,
            total_cost_difference=annual_savings
        )
    
    def _get_value(self, data: pd.Series, possible_keys: List[str]) -> Optional[str]:
        """Get value from Series using multiple possible keys."""
        for key in possible_keys:
            if key in data.index and pd.notna(data[key]):
                return str(data[key]).strip()
        return None
    
    def _get_numeric_value(self, data: pd.Series, possible_keys: List[str]) -> Optional[float]:
        """Get numeric value from Series using multiple possible keys."""
        for key in possible_keys:
            if key in data.index and pd.notna(data[key]):
                try:
                    # Handle string values with comma as decimal separator
                    value_str = str(data[key]).strip().replace(",", ".")
                    return float(value_str)
                except (ValueError, TypeError):
                    continue
        return None


def find_best_tariff_for_consumption(
    tariffs_df: pd.DataFrame,
    consumption_pattern: ConsumptionPattern,
    current_tariff_code: Optional[str] = None,
    tariff_type: str = "bi_hourly"
) -> Tuple[List[TariffCosts], Optional[TariffComparison]]:
    """
    Find the best tariff for given consumption pattern.
    
    Returns:
        Tuple of (all_tariff_costs_sorted, comparison_with_current)
    """
    calculator = TariffCostCalculator()
    
    # Calculate costs for all tariffs
    all_costs = calculator.calculate_all_tariffs(tariffs_df, consumption_pattern, tariff_type)
    
    if not all_costs:
        _LOGGER.warning("No tariff costs could be calculated")
        return [], None
    
    # Find current tariff if specified
    current_tariff = None
    if current_tariff_code:
        current_tariff = next(
            (cost for cost in all_costs if cost.tariff_code == current_tariff_code),
            None
        )
    
    # Compare with best tariff
    best_tariff = all_costs[0]  # Already sorted by cost
    comparison = None
    
    if current_tariff:
        comparison = calculator.compare_tariffs(current_tariff, best_tariff)
    
    _LOGGER.info(
        "Best tariff: %s (€%.2f/year), Current: %s",
        best_tariff.tariff_code,
        best_tariff.total_cost_annual,
        current_tariff.tariff_code if current_tariff else "Not specified"
    )
    
    return all_costs, comparison