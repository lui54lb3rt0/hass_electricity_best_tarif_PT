"""Tariff recommendation engine for finding the best electricity tariff."""
from __future__ import annotations

import logging
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any
import json

from .consumption_analyzer import ConsumptionPattern
from .cost_calculator import TariffCosts, TariffComparison, find_best_tariff_for_consumption

_LOGGER = logging.getLogger(__name__)


@dataclass
class TariffRecommendation:
    """Complete tariff recommendation with analysis."""
    
    # Best tariff information
    recommended_tariff_code: str
    recommended_tariff_name: str
    recommended_comercializador: str
    recommended_annual_cost: float
    recommended_monthly_cost: float
    
    # Current tariff comparison (if available)
    current_tariff_code: Optional[str] = None
    current_tariff_name: Optional[str] = None
    current_annual_cost: Optional[float] = None
    current_monthly_cost: Optional[float] = None
    
    # Savings potential
    annual_savings: float = 0.0
    monthly_savings: float = 0.0
    savings_percentage: float = 0.0
    
    # Top alternatives
    top_alternatives: List[Dict[str, Any]] = None
    
    # Analysis metadata
    total_tariffs_analyzed: int = 0
    consumption_analysis_quality: float = 0.0
    analysis_period_days: int = 0
    tariff_type: str = "bi_hourly"
    
    # Consumption breakdown
    annual_consumption_kwh: float = 0.0
    peak_consumption_kwh: float = 0.0
    off_peak_consumption_kwh: float = 0.0
    intermediate_consumption_kwh: float = 0.0
    
    # Cost breakdown for recommended tariff
    recommended_fixed_cost_annual: float = 0.0
    recommended_energy_cost_annual: float = 0.0
    recommended_additional_cost_annual: float = 0.0
    
    # Analysis timestamp
    analysis_timestamp: str = ""
    
    def __post_init__(self):
        if self.top_alternatives is None:
            self.top_alternatives = []
        if not self.analysis_timestamp:
            self.analysis_timestamp = datetime.now(timezone.utc).isoformat()


class TariffRecommendationEngine:
    """Engine for analyzing and recommending the best electricity tariff."""
    
    def __init__(self):
        self.last_recommendation: Optional[TariffRecommendation] = None
        self.last_analysis_timestamp: Optional[datetime] = None
    
    def analyze_and_recommend(
        self,
        tariffs_df,
        consumption_pattern: ConsumptionPattern,
        current_tariff_code: Optional[str] = None,
        tariff_type: str = "bi_hourly",
        max_alternatives: int = 5
    ) -> TariffRecommendation:
        """
        Analyze all tariffs and provide comprehensive recommendation.
        
        Args:
            tariffs_df: DataFrame with tariff data
            consumption_pattern: Analyzed consumption pattern
            current_tariff_code: Code of current tariff for comparison
            tariff_type: "bi_hourly" or "tri_hourly"
            max_alternatives: Maximum number of alternatives to include
        
        Returns:
            TariffRecommendation with complete analysis
        """
        try:
            _LOGGER.info("Starting tariff analysis and recommendation generation")
            
            # Find best tariff and comparison
            all_costs, comparison = find_best_tariff_for_consumption(
                tariffs_df, consumption_pattern, current_tariff_code, tariff_type
            )
            
            if not all_costs:
                raise ValueError("No tariff costs could be calculated")
            
            best_tariff = all_costs[0]
            
            # Create recommendation
            recommendation = TariffRecommendation(
                recommended_tariff_code=best_tariff.tariff_code,
                recommended_tariff_name=best_tariff.tariff_name,
                recommended_comercializador=best_tariff.comercializador,
                recommended_annual_cost=best_tariff.total_cost_annual,
                recommended_monthly_cost=best_tariff.total_cost_monthly,
                total_tariffs_analyzed=len(all_costs),
                consumption_analysis_quality=consumption_pattern.data_quality,
                analysis_period_days=consumption_pattern.days_analyzed,
                tariff_type=tariff_type,
                annual_consumption_kwh=consumption_pattern.annual_total,
                peak_consumption_kwh=best_tariff.peak_consumption_kwh,
                off_peak_consumption_kwh=best_tariff.off_peak_consumption_kwh,
                intermediate_consumption_kwh=best_tariff.intermediate_consumption_kwh,
                recommended_fixed_cost_annual=best_tariff.fixed_cost_annual,
                recommended_energy_cost_annual=best_tariff.energy_cost_annual,
                recommended_additional_cost_annual=best_tariff.additional_services_cost_annual
            )
            
            # Add current tariff information if available
            if comparison:
                recommendation.current_tariff_code = comparison.current_tariff.tariff_code
                recommendation.current_tariff_name = comparison.current_tariff.tariff_name
                recommendation.current_annual_cost = comparison.current_tariff.total_cost_annual
                recommendation.current_monthly_cost = comparison.current_tariff.total_cost_monthly
                recommendation.annual_savings = comparison.annual_savings
                recommendation.monthly_savings = comparison.monthly_savings
                recommendation.savings_percentage = comparison.savings_percentage
            
            # Add top alternatives
            recommendation.top_alternatives = self._create_alternatives_list(
                all_costs[1:max_alternatives+1]  # Skip the best one (index 0)
            )
            
            # Store for future reference
            self.last_recommendation = recommendation
            self.last_analysis_timestamp = datetime.now(timezone.utc)
            
            _LOGGER.info(
                "Recommendation complete: %s (€%.2f/year) vs current %s (savings: €%.2f/year)",
                best_tariff.tariff_code,
                best_tariff.total_cost_annual,
                recommendation.current_tariff_code or "unknown",
                recommendation.annual_savings
            )
            
            return recommendation
            
        except Exception as e:
            _LOGGER.error("Error generating tariff recommendation: %s", e)
            raise
    
    def _create_alternatives_list(self, alternative_costs: List[TariffCosts]) -> List[Dict[str, Any]]:
        """Create a list of alternative tariffs with key information."""
        alternatives = []
        
        for cost in alternative_costs:
            alternative = {
                "tariff_code": cost.tariff_code,
                "tariff_name": cost.tariff_name,
                "comercializador": cost.comercializador,
                "annual_cost": cost.total_cost_annual,
                "monthly_cost": cost.total_cost_monthly,
                "fixed_cost_annual": cost.fixed_cost_annual,
                "energy_cost_annual": cost.energy_cost_annual,
                "additional_cost_annual": cost.additional_services_cost_annual,
                "power_rating": cost.power_rating,
                "billing_cycle": cost.billing_cycle,
                "energy_type": cost.energy_type
            }
            alternatives.append(alternative)
        
        return alternatives
    
    def get_recommendation_summary(self) -> Optional[Dict[str, Any]]:
        """Get a summary of the last recommendation suitable for sensor state."""
        if not self.last_recommendation:
            return None
        
        summary = {
            "recommended_tariff": self.last_recommendation.recommended_tariff_code,
            "recommended_provider": self.last_recommendation.recommended_comercializador,
            "annual_cost": round(self.last_recommendation.recommended_annual_cost, 2),
            "monthly_cost": round(self.last_recommendation.recommended_monthly_cost, 2),
            "annual_savings": round(self.last_recommendation.annual_savings, 2),
            "monthly_savings": round(self.last_recommendation.monthly_savings, 2),
            "savings_percentage": round(self.last_recommendation.savings_percentage, 1),
            "current_tariff": self.last_recommendation.current_tariff_code,
            "tariffs_analyzed": self.last_recommendation.total_tariffs_analyzed,
            "data_quality": round(self.last_recommendation.consumption_analysis_quality * 100, 1),
            "analysis_timestamp": self.last_recommendation.analysis_timestamp
        }
        
        return summary
    
    def get_detailed_comparison(self) -> Optional[Dict[str, Any]]:
        """Get detailed comparison data for dashboard display."""
        if not self.last_recommendation:
            return None
        
        comparison = {
            "recommended": {
                "tariff_code": self.last_recommendation.recommended_tariff_code,
                "tariff_name": self.last_recommendation.recommended_tariff_name,
                "comercializador": self.last_recommendation.recommended_comercializador,
                "annual_cost": self.last_recommendation.recommended_annual_cost,
                "monthly_cost": self.last_recommendation.recommended_monthly_cost,
                "fixed_cost": self.last_recommendation.recommended_fixed_cost_annual,
                "energy_cost": self.last_recommendation.recommended_energy_cost_annual,
                "additional_cost": self.last_recommendation.recommended_additional_cost_annual
            },
            "current": {
                "tariff_code": self.last_recommendation.current_tariff_code,
                "tariff_name": self.last_recommendation.current_tariff_name,
                "annual_cost": self.last_recommendation.current_annual_cost,
                "monthly_cost": self.last_recommendation.current_monthly_cost
            } if self.last_recommendation.current_tariff_code else None,
            "savings": {
                "annual": self.last_recommendation.annual_savings,
                "monthly": self.last_recommendation.monthly_savings,
                "percentage": self.last_recommendation.savings_percentage
            },
            "consumption": {
                "annual_kwh": self.last_recommendation.annual_consumption_kwh,
                "peak_kwh": self.last_recommendation.peak_consumption_kwh,
                "off_peak_kwh": self.last_recommendation.off_peak_consumption_kwh,
                "intermediate_kwh": self.last_recommendation.intermediate_consumption_kwh
            },
            "alternatives": self.last_recommendation.top_alternatives,
            "analysis": {
                "timestamp": self.last_recommendation.analysis_timestamp,
                "tariffs_analyzed": self.last_recommendation.total_tariffs_analyzed,
                "data_quality": self.last_recommendation.consumption_analysis_quality,
                "analysis_period_days": self.last_recommendation.analysis_period_days,
                "tariff_type": self.last_recommendation.tariff_type
            }
        }
        
        return comparison
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert recommendation to dictionary for serialization."""
        if not self.last_recommendation:
            return {}
        
        return asdict(self.last_recommendation)
    
    def from_dict(self, data: Dict[str, Any]) -> None:
        """Load recommendation from dictionary."""
        if data:
            self.last_recommendation = TariffRecommendation(**data)
            # Parse timestamp
            if self.last_recommendation.analysis_timestamp:
                try:
                    self.last_analysis_timestamp = datetime.fromisoformat(
                        self.last_recommendation.analysis_timestamp.replace('Z', '+00:00')
                    )
                except ValueError:
                    self.last_analysis_timestamp = datetime.now(timezone.utc)


class TariffAnalysisResult:
    """Container for complete tariff analysis results."""
    
    def __init__(
        self,
        recommendation: TariffRecommendation,
        all_tariff_costs: List[TariffCosts],
        consumption_pattern: ConsumptionPattern
    ):
        self.recommendation = recommendation
        self.all_tariff_costs = all_tariff_costs
        self.consumption_pattern = consumption_pattern
    
    def get_cost_ranking(self, top_n: int = 10) -> List[Dict[str, Any]]:
        """Get top N tariffs ranked by cost."""
        ranking = []
        
        for i, cost in enumerate(self.all_tariff_costs[:top_n]):
            rank_info = {
                "rank": i + 1,
                "tariff_code": cost.tariff_code,
                "tariff_name": cost.tariff_name,
                "comercializador": cost.comercializador,
                "annual_cost": cost.total_cost_annual,
                "monthly_cost": cost.total_cost_monthly,
                "savings_vs_best": cost.total_cost_annual - self.all_tariff_costs[0].total_cost_annual,
                "fixed_cost": cost.fixed_cost_annual,
                "energy_cost": cost.energy_cost_annual,
                "additional_cost": cost.additional_services_cost_annual
            }
            ranking.append(rank_info)
        
        return ranking
    
    def get_consumption_summary(self) -> Dict[str, Any]:
        """Get consumption pattern summary."""
        return {
            "total_annual_kwh": self.consumption_pattern.annual_total,
            "daily_average_kwh": self.consumption_pattern.daily_total,
            "monthly_average_kwh": self.consumption_pattern.monthly_total,
            "peak_percentage": self.consumption_pattern.peak_percentage,
            "off_peak_percentage": self.consumption_pattern.off_peak_percentage,
            "intermediate_percentage": self.consumption_pattern.intermediate_percentage,
            "analysis_period_days": self.consumption_pattern.days_analyzed,
            "data_quality": self.consumption_pattern.data_quality * 100
        }
    
    def export_analysis(self) -> Dict[str, Any]:
        """Export complete analysis for external use."""
        return {
            "recommendation": asdict(self.recommendation),
            "cost_ranking": self.get_cost_ranking(),
            "consumption_summary": self.get_consumption_summary(),
            "hourly_patterns": self.consumption_pattern.hourly_averages,
            "daily_patterns": self.consumption_pattern.daily_averages,
            "monthly_patterns": self.consumption_pattern.monthly_averages,
            "analysis_metadata": {
                "total_tariffs": len(self.all_tariff_costs),
                "analysis_timestamp": self.recommendation.analysis_timestamp,
                "tariff_type": self.recommendation.tariff_type
            }
        }