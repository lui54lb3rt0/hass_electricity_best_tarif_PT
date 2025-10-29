#!/usr/bin/env python3
"""Test script to search for specific terms in ERSE HTML content."""

import asyncio
import aiohttp
import re

async def test_html_search():
    """Test searching for terms in ERSE HTML."""
    url = "https://simuladorprecos.erse.pt"
    
    async with aiohttp.ClientSession() as session:
        try:
            print(f"Fetching {url}...")
            async with session.get(url, timeout=30) as resp:
                resp.raise_for_status()
                html_content = await resp.text()
            
            print(f"Downloaded HTML content: {len(html_content)} characters")
            
            # Search for CSV-related terms
            search_terms = [
                'csv', 'CSV', 'csvPath', 'Admin/csvs', 
                'download', 'Download', 'ficheiro', 'dados',
                'preços', 'precos', 'tarifas', 'zip', 'ZIP',
                'ELEGN', 'CondComerciais', 'Precos'
            ]
            
            print("\nSearching for terms...")
            for term in search_terms:
                matches = list(re.finditer(re.escape(term), html_content, re.IGNORECASE))
                if matches:
                    print(f"\n=== Found {len(matches)} matches for '{term}' ===")
                    for i, match in enumerate(matches[:3]):  # Show first 3 matches
                        start = max(0, match.start() - 80)
                        end = min(len(html_content), match.end() + 80)
                        context = html_content[start:end].strip()
                        print(f"Match {i+1}: ...{context}...")
                        
                        # Look for URLs in this context
                        urls = re.findall(r'https?://[^\s"\'<>]+', context)
                        if urls:
                            print(f"  URLs in context: {urls}")
                        
                        # Look for paths in this context
                        paths = re.findall(r'/[^\s"\'<>]*\.zip', context)
                        if paths:
                            print(f"  ZIP paths in context: {paths}")
            
            # Look for JavaScript that might contain CSV URLs
            print("\n=== Looking for JavaScript CSV references ===")
            js_patterns = [
                r'csvPath["\']?\s*[:=]\s*["\']([^"\']+)["\']',
                r'["\']([^"\']*Admin/csvs/[^"\']*\.zip)["\']',
                r'href\s*=\s*["\']([^"\']*\.zip)["\']'
            ]
            
            for pattern in js_patterns:
                matches = re.findall(pattern, html_content, re.IGNORECASE)
                if matches:
                    print(f"Pattern '{pattern}' found: {matches}")
            
            # Save HTML for manual inspection
            with open('/tmp/erse_debug.html', 'w', encoding='utf-8') as f:
                f.write(html_content)
            print(f"\nSaved HTML content to /tmp/erse_debug.html")
            
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_html_search())