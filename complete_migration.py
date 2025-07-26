#!/usr/bin/env python3

import os
import re
import requests
import hashlib
import json
from urllib.parse import urlparse
from pathlib import Path

# Configuration
CLOUDFLARE_ACCOUNT_ID = "97fa04a4ed4dd87e51bb0ea49007dff7"
CLOUDFLARE_API_TOKEN = "Ey45yCv3oFN1B8KOIhKsIk6ZMmJGTGfQP1H2gOiW"

def create_mapping_from_downloaded_images():
    """Create a mapping from original URLs to local file paths for downloaded images"""
    url_to_local = {}
    
    # Check static/images/remote directory
    remote_dir = Path("static/images/remote")
    if remote_dir.exists():
        for image_file in remote_dir.rglob("*"):
            if image_file.is_file() and image_file.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif']:
                # Extract original URL from our download mapping if available
                relative_path = image_file.relative_to(Path("static/images"))
                print(f"Found downloaded image: {relative_path}")
    
    return url_to_local

def find_all_external_urls():
    """Find all external image URLs in content files"""
    external_urls = set()
    content_files = []
    
    # Scan all content directories
    for content_dir in ["content/posts", "content/photos", "content/videos", "content/microposts"]:
        if os.path.exists(content_dir):
            for root, dirs, files in os.walk(content_dir):
                for file in files:
                    if file.endswith('.md'):
                        file_path = os.path.join(root, file)
                        content_files.append(file_path)
    
    # Extract external URLs from files
    external_patterns = [
        r'http://\d+\.bp\.blogspot\.com/[^"\s]+',
        r'https://res\.cloudinary\.com/[^"\s]+', 
        r'https://[^"\s]*\.staticflickr\.com/[^"\s]+',
        r'https://farm\d+\.staticflickr\.com/[^"\s]+',
        r'https://c\d+\.staticflickr\.com/[^"\s]+',
        r'https://staging-jubilee\.flickr\.com/[^"\s]+',
        r'https://www\.flickr\.com/[^"\s]+'
    ]
    
    for file_path in content_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            for pattern in external_patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    # Clean up the URL (remove trailing punctuation)
                    clean_url = re.sub(r'["\s>}]+$', '', match)
                    external_urls.add(clean_url)
                    
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
    
    return list(external_urls), content_files

def get_cloudflare_images():
    """Get all existing images from Cloudflare Images"""
    url = f"https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}/images/v1"
    headers = {
        "Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    images = {}
    page = 1
    
    while True:
        params = {"page": page, "per_page": 100}
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code != 200:
            print(f"Error fetching Cloudflare images: {response.text}")
            break
            
        data = response.json()
        
        if not data.get("success"):
            print(f"Error: {data.get('errors')}")
            break
        
        results = data.get("result", {}).get("images", [])
        if not results:
            break
            
        for image in results:
            images[image["id"]] = image
            
        page += 1
        
        # Check if we have more pages
        if len(results) < 100:
            break
    
    return images

def create_url_mapping():
    """Create mapping between external URLs and their local equivalents"""
    print("Finding all external URLs...")
    external_urls, content_files = find_all_external_urls()
    
    print(f"Found {len(external_urls)} external URLs")
    
    # Get existing Cloudflare images  
    print("Fetching existing Cloudflare images...")
    cloudflare_images = get_cloudflare_images()
    
    print(f"Found {len(cloudflare_images)} images in Cloudflare")
    
    url_mapping = {}
    
    # Try to match external URLs to existing Cloudflare images
    for url in external_urls:
        parsed_url = urlparse(url)
        filename = os.path.basename(parsed_url.path)
        
        # Look for existing Cloudflare images that might match this URL
        for image_id, image_info in cloudflare_images.items():
            if filename.lower() in image_id.lower():
                cloudflare_url = f"https://imagedelivery.net/zJmFZzaNuqC_Q5Caqyu8nQ/{image_id}/public"
                url_mapping[url] = cloudflare_url
                print(f"Mapped: {url} -> {cloudflare_url}")
                break
    
    return url_mapping, content_files

def update_content_files(url_mapping, content_files):
    """Update all content files with the new URLs"""
    updates_made = 0
    files_updated = 0
    
    for file_path in content_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Replace each mapped URL
            for old_url, new_url in url_mapping.items():
                if old_url in content:
                    content = content.replace(old_url, new_url)
                    updates_made += 1
                    print(f"Updated in {file_path}: {old_url} -> {new_url}")
            
            # Write back if changes were made
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                files_updated += 1
                print(f"✓ Updated {file_path}")
                
        except Exception as e:
            print(f"Error updating {file_path}: {e}")
    
    return updates_made, files_updated

def main():
    print("=== Completing Blog Image Migration ===\n")
    
    # Create URL mapping
    url_mapping, content_files = create_url_mapping()
    
    if not url_mapping:
        print("No URL mappings found. All images may already be migrated.")
        return
    
    print(f"\nCreated {len(url_mapping)} URL mappings")
    
    # Update content files
    print("\nUpdating content files...")
    updates_made, files_updated = update_content_files(url_mapping, content_files)
    
    print(f"\n=== Migration Complete ===")
    print(f"Files updated: {files_updated}")
    print(f"URL replacements made: {updates_made}")
    
    # Show remaining external URLs
    remaining_urls, _ = find_all_external_urls()
    unmapped_urls = [url for url in remaining_urls if url not in url_mapping]
    
    if unmapped_urls:
        print(f"\nRemaining external URLs that couldn't be mapped: {len(unmapped_urls)}")
        for url in unmapped_urls[:10]:  # Show first 10
            print(f"  - {url}")
        if len(unmapped_urls) > 10:
            print(f"  ... and {len(unmapped_urls) - 10} more")

if __name__ == "__main__":
    main()
