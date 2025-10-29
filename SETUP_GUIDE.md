# Smart Tariff Analyzer - Setup and Debugging Guide

## Current Setup Issues and Solutions

### Issue 1: "Old setup still showing"
This indicates you may have an existing integration entry that needs to be reconfigured.

**Solution:**
1. Go to **Settings** → **Devices & Services**
2. Find any existing "Tarifários Eletricidade PT" or "Smart Tariff Analyzer" integration
3. **Delete** the old integration completely
4. **Add Integration** → Search for "Electricity Best Tariff PT"
5. Follow the new setup process with consumption analysis enabled

### Issue 2: "New sensors not being created"
The integration now only creates sensors when consumption analysis is enabled.

**Solution - Check Your Configuration:**
1. When adding the integration, ensure you check "Enable consumption analysis"
2. Select a valid energy sensor (must be cumulative kWh)
3. Choose your current tariff from the dropdown list

## Step-by-Step Setup Process

### 1. **Prerequisites**
- Have an energy sensor in Home Assistant that tracks cumulative energy consumption (kWh)
- Know your current electricity provider (comercializador)
- Know your contracted power (potência contratada)

### 2. **Adding the Integration**
1. Go to **Settings** → **Devices & Services** → **Add Integration**
2. Search for "Electricity Best Tariff PT"
3. Select your **Provider** (Comercializador)
4. Select **Energy Type** (usually "Eletricidade apenas")
5. **✅ Enable consumption analysis** (IMPORTANT!)

### 3. **Consumption Analysis Configuration**
1. **Energy Sensor**: Select your main energy consumption sensor
2. **Analysis Days**: How many days of history to analyze (default: 30)
3. **Tariff Type**: 
   - Bi-horário (Peak/Off-peak)
   - Tri-horário (Peak/Intermediate/Off-peak)
4. **Current Tariff**: Select your actual tariff from the dropdown

### 4. **Final Configuration**
1. **Contracted Power**: Select your power level (e.g., "3,45")
2. **Tariff Selection**: Choose which tariffs to monitor (optional)

## Expected Sensors

When properly configured, you should see these 4 new sensors:

1. **🔋 Consumption Analysis [Sensor Name]**
   - Shows: Annual consumption estimate (kWh)
   - State: Your estimated yearly consumption

2. **⚡ Best Tariff Recommendation**
   - Shows: Annual cost of recommended tariff (€/year)
   - State: Cost of the best tariff found

3. **💰 Potential Annual Savings**
   - Shows: How much you could save per year (€/year)
   - State: Your potential savings

4. **📊 Tariff Comparison**
   - Shows: Number of tariffs analyzed
   - State: Count of tariffs compared

## Troubleshooting

### Check Home Assistant Logs
1. Go to **Settings** → **System** → **Logs**
2. Look for messages containing "hass_electricity_best_tarif_pt"
3. Key log messages to look for:
   ```
   [INFO] Setting up smart tariff analysis sensors
   [INFO] Successfully created 4 smart analysis sensors
   [INFO] Energy sensor [sensor_name] found with state: [value] kWh
   ```

### Common Issues

**❌ "No energy sensor configured"**
- Solution: Ensure you selected an energy sensor during setup

**❌ "Energy sensor not found"**
- Solution: Check that your energy sensor exists and is working

**❌ "Consumption analysis disabled"**
- Solution: Delete and recreate the integration with analysis enabled

**❌ "No sensors created"**
- Solution: Check that `enable_consumption_analysis` is `True` in configuration

### Verify Your Energy Sensor
Your energy sensor should:
- ✅ Have device class "energy" or unit "kWh"
- ✅ Be accumulating/cumulative (always increasing)
- ✅ Have sufficient history (at least 7 days)
- ✅ Not be in "unknown" or "unavailable" state

### Manual Configuration Check
If needed, you can check your configuration in:
**Settings** → **Devices & Services** → **Electricity Best Tariff PT** → **Configure**

Look for these settings:
```yaml
enable_consumption_analysis: true
energy_sensor: sensor.your_energy_sensor
analysis_days: 30
tariff_type: bi_hourly
current_tariff_code: YOUR_TARIFF_CODE
```

## Advanced Debugging

### Check Entity Registry
1. **Developer Tools** → **States**
2. Filter for "consumption_analysis" or "best_tariff"
3. You should see 4 entities with the domain name

### Check Logs for Specific Errors
Look for these specific log entries:
- Sensor creation: "Created ConsumptionAnalysisSensor"
- Analysis results: "Consumption analysis completed"
- Recommendations: "Updated tariff recommendation"

### Force Refresh
After setup, restart Home Assistant to ensure all components load properly.

## Success Indicators

You'll know it's working when:
- ✅ 4 new sensors appear in your entity list
- ✅ Consumption analysis sensor shows your annual consumption estimate
- ✅ Recommendation sensor shows a suggested tariff and cost
- ✅ Logs show successful sensor creation and analysis
- ✅ Dashboard templates work with your new sensors

## Getting Help

If you're still having issues:
1. Share the integration logs (filter for "hass_electricity_best_tarif_pt")
2. Confirm your energy sensor name and current state
3. Check that consumption analysis is enabled in your configuration