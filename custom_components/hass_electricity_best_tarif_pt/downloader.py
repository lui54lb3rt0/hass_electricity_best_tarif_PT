"""Download and extraction utilities for ERSE data."""
import asyncio
import logging
import zipfile
import re
from datetime import datetime, timedelta
from io import BytesIO
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

_LOGGER = logging.getLogger(__name__)

# ERSE simulator page URL
ERSE_SIMULATOR_URL = "https://simuladorprecos.erse.pt"
# Fallback URL if all methods fail
FALLBACK_ZIP_URL = "https://simuladorprecos.erse.pt/Admin/csvs/20250919%20100313%20CSV.zip"

def search_html_for_terms(html_content: str, search_terms: list[str]) -> dict:
    """Search HTML content for specific terms and return context around matches."""
    results = {}
    
    for term in search_terms:
        matches = []
        for match in re.finditer(re.escape(term), html_content, re.IGNORECASE):
            start = max(0, match.start() - 100)
            end = min(len(html_content), match.end() + 100)
            context = html_content[start:end].strip()
            matches.append({
                'position': match.start(),
                'context': context
            })
        results[term] = matches
    
    return results

def _analyze_page_content(html_content: str) -> list[str]:
    """Analyze page content for CSV URLs using multiple patterns and term searching."""
    found_urls = []
    
    # Pattern 1: Look for the specific update text to extract date
    update_pattern = r'Ofertas comerciais \(CSV\) - Atualizado em ([^<]*)'
    update_matches = re.findall(update_pattern, html_content, re.IGNORECASE)
    if update_matches:
        for date_text in update_matches:
            _LOGGER.info("Found CSV update date text: '%s'", date_text.strip())
            # Try to extract date components from the text
            # Common formats: "19/09/2025" or "19-09-2025" or "2025-09-19"
            date_patterns = [
                r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})',  # DD/MM/YYYY or DD-MM-YYYY
                r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})',  # YYYY/MM/DD or YYYY-MM-DD
            ]
            
            for pattern in date_patterns:
                date_match = re.search(pattern, date_text)
                if date_match:
                    # Try both DD/MM/YYYY and YYYY/MM/DD formats
                    if len(date_match.group(1)) == 4:  # YYYY format
                        year, month, day = date_match.groups()
                    else:  # DD/MM format
                        day, month, year = date_match.groups()
                    
                    # Format as YYYYMMDD for URL
                    formatted_date = f"{year}{month.zfill(2)}{day.zfill(2)}"
                    _LOGGER.info("Extracted date: %s -> %s", date_text.strip(), formatted_date)
                    
                    # Try common time patterns for this date
                    time_patterns = ["100313", "100000", "110000", "120000", "090000"]
                    for time_str in time_patterns:
                        csv_url = f"https://simuladorprecos.erse.pt/Admin/csvs/{formatted_date}%20{time_str}%20CSV.zip"
                        found_urls.append(csv_url)
                    break
    
    # Pattern 2: Direct Admin/csvs paths
    admin_paths = re.findall(r'/Admin/csvs/[^"\'>\s]*\.zip', html_content)
    for path in admin_paths:
        found_urls.append(f"https://simuladorprecos.erse.pt{path}")
    
    # Pattern 3: Full URLs with .zip
    zip_urls = re.findall(r'https://simuladorprecos\.erse\.pt/Admin/csvs/[^"\'>\s]*\.zip', html_content)
    found_urls.extend(zip_urls)
    
    # Pattern 4: Date patterns that might be CSV filenames
    date_patterns = re.findall(r'\d{8}[%\s]\d{6}[%\s]CSV\.zip', html_content)
    for pattern in date_patterns:
        # Convert spaces to %20 for URL encoding
        encoded_pattern = pattern.replace(' ', '%20')
        found_urls.append(f"https://simuladorprecos.erse.pt/Admin/csvs/{encoded_pattern}")
    
    # Pattern 5: JavaScript variables with CSV paths
    js_vars = re.findall(r'["\']([^"\']*Admin/csvs/[^"\']*\.zip)["\']', html_content)
    for var in js_vars:
        if var.startswith('/'):
            found_urls.append(f"https://simuladorprecos.erse.pt{var}")
        elif not var.startswith('http'):
            found_urls.append(f"https://simuladorprecos.erse.pt/{var}")
        else:
            found_urls.append(var)
    
    # Pattern 6: Search for specific terms and extract nearby URLs
    csv_terms = [
        'csvPath', 'CSV', 'csv', 'ELEGN', 'CondComerciais', 
        'download', 'Download', 'ficheiro', 'Ficheiro',
        'dados', 'Dados', 'preços', 'precos', 'tarifas'
    ]
    
    for term in csv_terms:
        # Look for the term and extract URLs within 500 characters of it
        term_matches = [m.start() for m in re.finditer(re.escape(term), html_content, re.IGNORECASE)]
        for match_pos in term_matches:
            # Extract context around the term
            start = max(0, match_pos - 250)
            end = min(len(html_content), match_pos + 250)
            context = html_content[start:end]
            
            # Look for URLs in this context
            context_urls = re.findall(r'https?://[^\s"\'<>]+\.zip', context)
            found_urls.extend(context_urls)
            
            # Look for relative paths in this context
            context_paths = re.findall(r'/[^\s"\'<>]*\.zip', context)
            for path in context_paths:
                if 'Admin/csvs' in path or 'csv' in path.lower():
                    found_urls.append(f"https://simuladorprecos.erse.pt{path}")
    
    # Pattern 7: Look for data attributes or JavaScript that might contain CSV URLs
    data_attrs = re.findall(r'data-[^=]*=["\']([^"\']*\.zip)["\']', html_content)
    for attr in data_attrs:
        if not attr.startswith('http'):
            found_urls.append(f"https://simuladorprecos.erse.pt/{attr.lstrip('/')}")
        else:
            found_urls.append(attr)
    
    # Pattern 8: BeautifulSoup-based parsing for better HTML structure analysis
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Look for the specific update text
        update_elements = soup.find_all(string=re.compile(r'Ofertas comerciais.*Atualizado em', re.IGNORECASE))
        for element in update_elements:
            _LOGGER.debug("Found update element text: '%s'", element.strip())
            
        # Look for links with specific classes or text content
        csv_links = soup.find_all('a', class_=lambda x: x and 'csv' in x.lower())
        for link in csv_links:
            href = link.get('href')
            if href and '.zip' in href:
                if href.startswith('/'):
                    found_urls.append(f"https://simuladorprecos.erse.pt{href}")
                elif not href.startswith('http'):
                    found_urls.append(f"https://simuladorprecos.erse.pt/{href}")
                else:
                    found_urls.append(href)
        
        # Look for links with CSV-related text content
        csv_text_links = soup.find_all('a', string=re.compile(r'csv|CSV|download|Download|ficheiro|dados', re.IGNORECASE))
        for link in csv_text_links:
            href = link.get('href')
            if href and '.zip' in href:
                if href.startswith('/'):
                    found_urls.append(f"https://simuladorprecos.erse.pt{href}")
                elif not href.startswith('http'):
                    found_urls.append(f"https://simuladorprecos.erse.pt/{href}")
                else:
                    found_urls.append(href)
                    
        # Look for elements with specific IDs or classes
        csv_elements = soup.find_all(attrs={'class': re.compile(r'csv|download', re.IGNORECASE)})
        csv_elements.extend(soup.find_all(attrs={'id': re.compile(r'csv|download', re.IGNORECASE)}))
        
        for element in csv_elements:
            # Check data attributes
            for attr_name, attr_value in element.attrs.items():
                if isinstance(attr_value, str) and '.zip' in attr_value:
                    if attr_value.startswith('/'):
                        found_urls.append(f"https://simuladorprecos.erse.pt{attr_value}")
                    elif not attr_value.startswith('http'):
                        found_urls.append(f"https://simuladorprecos.erse.pt/{attr_value}")
                    else:
                        found_urls.append(attr_value)
    except ImportError:
        _LOGGER.debug("BeautifulSoup not available, skipping advanced HTML parsing")
    except Exception as e:
        _LOGGER.debug("Error in BeautifulSoup parsing: %s", e)
    
    _LOGGER.debug("Found potential CSV URLs in page: %s", found_urls)
    return list(set(found_urls))  # Remove duplicates

async def _try_date_patterns(hass: HomeAssistant) -> str:
    """Try date-based URL patterns using known working format."""
    session = async_get_clientsession(hass)
    base_url = "https://simuladorprecos.erse.pt/Admin/csvs"
    
    # Try recent dates with common time patterns
    today = datetime.now()
    
    # Time patterns based on known working format (100313 from fallback)
    time_patterns = [
        "100313",  # Known working time
        "100000", "110000", "120000", "090000",
        "100300", "100330", "100315", "100310"
    ]
    
    for days_back in range(0, 10):  # Try last 10 days
        date = today - timedelta(days=days_back)
        date_str = date.strftime('%Y%m%d')
        
        for time_str in time_patterns:
            url = f"{base_url}/{date_str}%20{time_str}%20CSV.zip"
            
            try:
                async with session.head(url, timeout=5) as resp:
                    if resp.status == 200:
                        _LOGGER.info("Found working CSV URL via date pattern: %s", url)
                        return url
            except:
                continue
    
    return None

async def _test_extracted_urls(hass: HomeAssistant, urls: list[str]) -> str:
    """Test extracted URLs to find working ones."""
    session = async_get_clientsession(hass)
    
    for url in urls:
        try:
            async with session.head(url, timeout=5) as resp:
                if resp.status == 200:
                    _LOGGER.info("Found working CSV URL from page analysis: %s", url)
                    return url
        except:
            continue
    
    return None

async def async_get_latest_csv_url(hass: HomeAssistant) -> str:
    """Get the latest CSV ZIP URL using multiple strategies."""
    session = async_get_clientsession(hass)
    
    try:
        _LOGGER.debug("Fetching ERSE simulator page...")
        async with session.get(ERSE_SIMULATOR_URL, timeout=30) as resp:
            resp.raise_for_status()
            html_content = await resp.text()
        
        # Optional: Save HTML for debugging (only in debug mode)
        if _LOGGER.isEnabledFor(logging.DEBUG):
            try:
                # Use asyncio to avoid blocking the event loop
                import asyncio
                def write_debug_file():
                    with open('/tmp/erse_page.html', 'w', encoding='utf-8') as f:
                        f.write(html_content)
                
                # Run in thread pool to avoid blocking
                await asyncio.get_event_loop().run_in_executor(None, write_debug_file)
                _LOGGER.debug("Saved HTML content to /tmp/erse_page.html for debugging")
            except Exception as e:
                _LOGGER.debug("Could not save HTML debug file: %s", e)
        
        # Strategy 1: Analyze page content for CSV URLs
        _LOGGER.debug("Analyzing page content for CSV URLs...")
        extracted_urls = _analyze_page_content(html_content)
        if extracted_urls:
            _LOGGER.debug("Found %d potential URLs: %s", len(extracted_urls), extracted_urls)
            working_url = await _test_extracted_urls(hass, extracted_urls)
            if working_url:
                _LOGGER.info("Found working CSV URL via content analysis: %s", working_url)
                return working_url
        
        # Strategy 2: Try recent date patterns
        _LOGGER.debug("Trying date-based URL patterns...")
        pattern_url = await _try_date_patterns(hass)
        if pattern_url:
            return pattern_url
        
        # Strategy 3: Fallback to known working URL
        _LOGGER.info("All discovery methods failed, using fallback URL: %s", FALLBACK_ZIP_URL)
        return FALLBACK_ZIP_URL
        
    except Exception as e:
        _LOGGER.error("Failed to get latest CSV URL: %s", e)
        _LOGGER.info("Using fallback CSV URL: %s", FALLBACK_ZIP_URL)
        return FALLBACK_ZIP_URL

async def async_download_erse_zip(hass: HomeAssistant, url: str = None) -> bytes:
    """Download ERSE ZIP file."""
    if not url:
        url = await async_get_latest_csv_url(hass)
    
    _LOGGER.debug("Starting download from %s", url)
    session = async_get_clientsession(hass)
    
    async with session.get(url, timeout=60) as resp:
        content = await resp.read()
        _LOGGER.debug("Downloaded ZIP size=%d bytes status=%s", len(content), resp.status)
        resp.raise_for_status()
        return content

async def async_extract_csv_from_zip(zip_content: bytes, filename: str) -> str:
    """Extract specific CSV file from ZIP content."""
    def _extract():
        with zipfile.ZipFile(BytesIO(zip_content)) as zf:
            file_list = zf.namelist()
            _LOGGER.debug("ZIP contains files: %s", file_list)
            
            # Find the target file
            target_file = None
            for file in file_list:
                if file.endswith(filename) or filename in file:
                    target_file = file
                    break
            
            if not target_file:
                raise FileNotFoundError(f"File '{filename}' not found in ZIP. Available files: {file_list}")
            
            _LOGGER.debug("Extracting '%s' from ZIP", target_file)
            return zf.read(target_file).decode('utf-8-sig')
    
    return await asyncio.to_thread(_extract)

async def async_download_and_extract_csvs(hass: HomeAssistant) -> tuple[str, str]:
    """Download ERSE ZIP and extract both CSV files."""
    try:
        _LOGGER.info("Finding latest ERSE CSV URL...")
        csv_url = await async_get_latest_csv_url(hass)
        
        _LOGGER.info("Downloading ERSE data from: %s", csv_url)
        zip_content = await async_download_erse_zip(hass, csv_url)
        
        _LOGGER.info("Extracting CSV files...")
        cond_txt, precos_txt = await asyncio.gather(
            async_extract_csv_from_zip(zip_content, "CondComerciais.csv"),
            async_extract_csv_from_zip(zip_content, "Precos_ELEGN.csv"),
        )
        
        _LOGGER.info("Successfully extracted CSV files: CondComerciais (%d chars), Precos_ELEGN (%d chars)", 
                     len(cond_txt), len(precos_txt))
        
        return cond_txt, precos_txt
        
    except Exception as e:
        _LOGGER.error("Download or extraction failed: %s", e)
        raise