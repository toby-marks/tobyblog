#!/usr/bin/env python3

import os
import re
import glob
import requests
import time
from urllib.parse import urlparse
import hashlib

def extract_original_remote_urls():
    """Extract original remote image URLs that haven't been migrated to Cloudflare yet"""
    
    # Find all markdown files
    md_files = glob.glob("content/**/*.md", recursive=True)
    
    remote_urls = set()
    
    # Patterns for remote image URLs we want to download
    url_patterns = [
        r'https?://\d+\.bp\.blogspot\.com/[^"\s)]+',  # Blogspot
        r'https?://res\.cloudinary\.com/[^"\s)]+',     # Cloudinary
        r'https?://[^"]*flickr\.com/[^"\s)]+',         # Flickr
        r'https?://farm\d+\.staticflickr\.com/[^"\s)]+', # Static Flickr
    ]
    
    for md_file in md_files:
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            for pattern in url_patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    # Clean up the URL (remove trailing punctuation)
                    url = match.rstrip('.,;:!?)')
                    remote_urls.add(url)
                    
        except Exception as e:
            print(f"Error reading {md_file}: {e}")
    
    return list(remote_urls)

def create_local_path(url):
    """Create a local path for the downloaded image"""
    parsed = urlparse(url)
    
    # Extract filename from URL
    path_parts = parsed.path.split('/')
    filename = path_parts[-1] if path_parts else 'image'
    
    # If no extension, try to get from URL or default to jpg
    if '.' not in filename:
        # Check if there's a format parameter or extension in query
        if parsed.query:
            if 'format=' in parsed.query:
                format_match = re.search(r'format=(\w+)', parsed.query)
                if format_match:
                    filename += f'.{format_match.group(1)}'
            elif any(ext in parsed.query for ext in ['.jpg', '.jpeg', '.png', '.gif']):
                # Extract extension from query
                ext_match = re.search(r'\.(\w+)', parsed.query)
                if ext_match:
                    filename += f'.{ext_match.group(0)}'
        
        # Default to jpg if still no extension
        if '.' not in filename:
            filename += '.jpg'
    
    # Create a hash-based directory structure to avoid conflicts
    url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
    
    # Determine source directory
    if 'blogspot.com' in url:
        source_dir = 'blogspot'
    elif 'cloudinary.com' in url:
        source_dir = 'cloudinary'
    elif 'flickr' in url:
        source_dir = 'flickr'
    else:
        source_dir = 'other'
    
    local_path = f"static/images/remote/{source_dir}/{url_hash}_{filename}"
    
    return local_path

def download_image(url, local_path):
    """Download an image from URL to local path"""
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        
        # Skip if already exists
        if os.path.exists(local_path):
            return True
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        with open(local_path, 'wb') as f:
            f.write(response.content)
        
        return True
        
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return False

def main():
    print("Extracting remaining remote image URLs...")
    remote_urls = extract_original_remote_urls()
    
    print(f"Found {len(remote_urls)} remaining remote images to download")
    
    # Group by source
    sources = {}
    for url in remote_urls:
        if 'blogspot.com' in url:
            source = 'blogspot'
        elif 'cloudinary.com' in url:
            source = 'cloudinary'
        elif 'flickr' in url:
            source = 'flickr'
        else:
            source = 'other'
        
        if source not in sources:
            sources[source] = []
        sources[source].append(url)
    
    print("\nImages by source:")
    for source, urls in sources.items():
        print(f"  {source}: {len(urls)} images")
    
    # Download images
    downloaded = 0
    failed = 0
    skipped = 0
    
    for i, url in enumerate(remote_urls, 1):
        local_path = create_local_path(url)
        
        if os.path.exists(local_path):
            skipped += 1
            continue
        
        print(f"Processing {i}/{len(remote_urls)}: {os.path.basename(local_path)}")
        print(f"  URL: {url}")
        
        if download_image(url, local_path):
            downloaded += 1
            print(f"  ✓ Downloaded to: {local_path}")
        else:
            failed += 1
            print(f"  ✗ Failed to download")
        
        # Rate limiting
        time.sleep(0.2)
        
        # Progress report every 50 images
        if i % 50 == 0:
            print(f"\nProgress: {downloaded} downloaded, {skipped} skipped, {failed} failed\n")
    
    print(f"\n=== Download Summary ===")
    print(f"Total URLs processed: {len(remote_urls)}")
    print(f"Downloaded: {downloaded}")
    print(f"Skipped (already exist): {skipped}")
    print(f"Failed: {failed}")

if __name__ == "__main__":
    main()
