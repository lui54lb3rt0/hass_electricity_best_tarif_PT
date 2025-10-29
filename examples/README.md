# Dashboard Templates for Best Tariff Analyzer

This directory contains dashboard card templates and examples for visualizing tariff recommendations and consumption analysis.

## Quick Setup

1. Copy the desired card templates to your dashboard
2. Replace the entity IDs with your actual sensor entities
3. Customize styling and layout as needed

## Available Templates

### 1. **tariff_recommendation_card.yaml** 
Main recommendation card showing best tariff, savings, and key metrics.

### 2. **consumption_analysis_card.yaml**
Detailed consumption pattern analysis with hourly/daily breakdowns.

### 3. **tariff_comparison_table.yaml**
Table comparing multiple tariffs with costs and features.

### 4. **savings_overview_card.yaml**
Visual savings summary with charts and progress indicators.

### 5. **complete_dashboard.yaml**
Full dashboard layout combining all components.

## Entity Naming Convention

The integration creates entities with these patterns:
- `sensor.consumption_analysis_[energy_sensor]` - Consumption pattern analysis
- `sensor.best_tariff_recommendation` - Recommended tariff
- `sensor.potential_annual_savings` - Savings calculation
- `sensor.tariff_comparison` - Detailed comparison data

## Customization Tips

1. **Colors**: Adjust the CSS color variables in each template
2. **Refresh Rates**: Configure update intervals based on your needs
3. **Alerts**: Set up automations based on savings thresholds
4. **History**: Use the `sensor.tariff_comparison` attributes for historical tracking