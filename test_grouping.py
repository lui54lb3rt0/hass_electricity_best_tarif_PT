#!/usr/bin/env python3
"""Test script to verify offer grouping logic."""

import asyncio
import sys
import pandas as pd
sys.path.append('custom_components/hass_tarifarios_eletricidade_pt')

from data_loader import async_process_csv

class MockHass:
    pass

async def test_grouping():
    """Test the offer grouping logic."""
    hass = MockHass()
    
    print("Downloading data for G9ENERGY...")
    df = await async_process_csv(hass, comercializador='G9ENERGY')
    
    if df.empty:
        print("No data available")
        return
    
    print(f"DataFrame shape: {df.shape}")
    print(f"Columns: {list(df.columns)}")
    
    # Find relevant columns
    offer_col = next((c for c in df.columns if 'código' in c.lower() and 'oferta' in c.lower()), None)
    cycle_col = next((c for c in df.columns if 'ciclo' in c.lower() and 'contagem' in c.lower()), None)
    name_col = next((c for c in df.columns if 'nome' in c.lower() and 'oferta' in c.lower()), None)
    
    if not offer_col:
        print("Offer code column not found!")
        return
    
    print(f"\nOffer column: {offer_col}")
    print(f"Cycle column: {cycle_col}")
    print(f"Name column: {name_col}")
    
    # Analyze the data structure
    unique_offers = df[offer_col].nunique()
    total_rows = len(df)
    
    print(f"\nData structure:")
    print(f"  Total rows: {total_rows}")
    print(f"  Unique offers: {unique_offers}")
    print(f"  Ratio: {total_rows / unique_offers:.1f} rows per offer")
    
    if cycle_col:
        cycle_counts = df[cycle_col].value_counts()
        print(f"\nBilling cycles found:")
        for cycle, count in cycle_counts.items():
            print(f"  {cycle}: {count} rows")
    
    # Show sample grouping
    print(f"\nSample offers and their cycles:")
    sample_offers = df[offer_col].unique()[:5]
    for offer in sample_offers:
        offer_rows = df[df[offer_col] == offer]
        cycles = offer_rows[cycle_col].tolist() if cycle_col else ["N/A"]
        offer_name = offer_rows[name_col].iloc[0] if name_col and not offer_rows.empty else "N/A"
        print(f"  {offer} ({offer_name}): {cycles}")
    
    # Simulate the new grouping logic
    print(f"\nSimulating new grouping logic:")
    grouped_offers = {}
    
    for _, row in df.iterrows():
        codigo = str(row[offer_col])
        
        if codigo in grouped_offers:
            # Merge billing cycle data
            print(f"  Merging cycle data for offer {codigo}")
            continue
        else:
            # New offer
            offer_name = row[name_col] if name_col and row.get(name_col) else f"Tarifa {codigo}"
            grouped_offers[codigo] = {
                'name': offer_name,
                'cycles': []
            }
    
    print(f"  Would create {len(grouped_offers)} entities (was {total_rows})")
    print(f"  Reduction: {((total_rows - len(grouped_offers)) / total_rows * 100):.1f}%")

if __name__ == "__main__":
    asyncio.run(test_grouping())