import os
import re
import urllib.request
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor

BASE_URL = "https://dadosabertos.c3sl.ufpr.br/curitibaurbs/"
DATA_DIR = "dados_em_tempo_real_2026"
DEST_DIR = "dados_c3sl"

def get_target_dates():
    """Gets the list of dates in YYYY_MM_DD format from the directories in DATA_DIR."""
    dates = []
    if not os.path.exists(DATA_DIR):
        print(f"Error: Directory {DATA_DIR} does not exist.")
        return dates
    
    for name in os.listdir(DATA_DIR):
        if os.path.isdir(os.path.join(DATA_DIR, name)):
            # match YYYY-MM-DD
            if re.match(r"^\d{4}-\d{2}-\d{2}$", name):
                dates.append(name.replace("-", "_"))
    return sorted(dates)

def fetch_links_from_site():
    """Fetches the HTML from BASE_URL and extracts all file links."""
    print(f"Fetching file list from {BASE_URL}...")
    req = urllib.request.Request(
        BASE_URL, 
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    )
    with urllib.request.urlopen(req) as response:
        html = response.read().decode('utf-8', errors='ignore')
    
    # Extract links in href="filename"
    links = re.findall(r'href="([^"]+)"', html)
    return links

def download_file(url, filepath):
    """Downloads a single file with progress printing."""
    temp_filepath = filepath + ".tmp"
    try:
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        with urllib.request.urlopen(req) as response, open(temp_filepath, 'wb') as out_file:
            meta = response.info()
            file_size = int(meta.get("Content-Length", 0))
            print(f"Downloading {os.path.basename(filepath)} ({file_size / (1024*1024):.2f} MB)...")
            
            block_size = 8192
            downloaded = 0
            while True:
                buffer = response.read(block_size)
                if not buffer:
                    break
                downloaded += len(buffer)
                out_file.write(buffer)
        
        os.replace(temp_filepath, filepath)
        print(f"Finished {os.path.basename(filepath)}")
        return True
    except Exception as e:
        if os.path.exists(temp_filepath):
            os.remove(temp_filepath)
        print(f"Error downloading {url}: {e}")
        return False

def main():
    target_dates = get_target_dates()
    if not target_dates:
        print("No target dates found in dados_em_tempo_real_2026.")
        return
    
    print(f"Found {len(target_dates)} target dates: {target_dates[0]} to {target_dates[-1]}")
    
    all_links = fetch_links_from_site()
    print(f"Found {len(all_links)} total links on the site.")
    
    # Filter links that start with any of our target dates
    matched_files = []
    # Build a fast lookup set of target prefixes, e.g. "2025_10_24"
    target_prefixes = set(target_dates)
    
    for link in all_links:
        # Link name typically is like YYYY_MM_DD_...
        # Extract the prefix YYYY_MM_DD
        match = re.match(r"^(\d{4}_\d{2}_\d{2})_", link)
        if match:
            date_prefix = match.group(1)
            if date_prefix in target_prefixes:
                matched_files.append(link)
                
    if not matched_files:
        print("No matching files found on the website for the target dates.")
        return
        
    print(f"Identified {len(matched_files)} files to download.")
    os.makedirs(DEST_DIR, exist_ok=True)
    
    # Download them sequentially to avoid overwhelming the server and to be nice
    downloaded_count = 0
    skipped_count = 0
    
    for file_name in matched_files:
        filepath = os.path.join(DEST_DIR, file_name)
        if os.path.exists(filepath):
            skipped_count += 1
            continue
            
        url = urljoin(BASE_URL, file_name)
        if download_file(url, filepath):
            downloaded_count += 1
            
    print(f"\nDownload completed! Downloaded: {downloaded_count}, Skipped (already exists): {skipped_count}")

if __name__ == "__main__":
    main()
