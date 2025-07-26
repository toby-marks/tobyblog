#!/usr/bin/env python3

import os
import re
import json
import glob
from urllib.parse import urlparse

def load_existing_mapping():
    """Load the existing Cloudflare image mapping"""
    if not os.path.exists("cloudflare_image_mapping.json"):
        print("No mapping file found.")
        return {}
    
    with open("cloudflare_image_mapping.json", 'r') as f:
        return json.load(f)

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

def create_url_mapping_from_downloaded():
    """Create URL mapping based on downloaded remote images"""
    mapping = load_existing_mapping()
    
    # Find all external URLs
    external_urls, content_files = find_all_external_urls()
    print(f"Found {len(external_urls)} external URLs")
    
    url_mapping = {}
    
    # Try to match external URLs to downloaded images
    for url in external_urls:
        parsed_url = urlparse(url)
        filename = os.path.basename(parsed_url.path)
        
        # Look in the remote directory structure
        for local_path, cf_info in mapping.items():
            if local_path.startswith("images/remote/"):
                # Extract the downloaded filename
                downloaded_filename = os.path.basename(local_path)
                
                # Try to match based on filename patterns
                if filename.lower() in downloaded_filename.lower():
                    cloudflare_url = cf_info['cloudflare_url']
                    url_mapping[url] = cloudflare_url
                    print(f"Mapped: {url} -> {cloudflare_url}")
                    break
                
                # Also try partial matches for similar images
                elif any(part in downloaded_filename.lower() for part in filename.lower().split('.')[0].split('_') if len(part) > 3):
                    cloudflare_url = cf_info['cloudflare_url']
                    url_mapping[url] = cloudflare_url
                    print(f"Partial match: {url} -> {cloudflare_url}")
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
            file_updates = 0
            
            # Replace each mapped URL
            for old_url, new_url in url_mapping.items():
                if old_url in content:
                    content = content.replace(old_url, new_url)
                    file_updates += 1
                    print(f"  Updated: {old_url} -> {new_url}")
            
            # Write back if changes were made
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                files_updated += 1
                updates_made += file_updates
                print(f"✓ Updated {file_path} ({file_updates} replacements)")
                
        except Exception as e:
            print(f"Error updating {file_path}: {e}")
    
    return updates_made, files_updated

def main():
    print("=== Fixing Remaining External URLs ===\n")
    
    # Create URL mapping from downloaded images
    url_mapping, content_files = create_url_mapping_from_downloaded()
    
    if not url_mapping:
        print("No URL mappings found. Checking what external URLs remain...")
        remaining_urls, _ = find_all_external_urls()
        print(f"Found {len(remaining_urls)} remaining external URLs:")
        for i, url in enumerate(remaining_urls[:20]):
            print(f"  {i+1}. {url}")
        if len(remaining_urls) > 20:
            print(f"  ... and {len(remaining_urls) - 20} more")
        return
    
    print(f"\nCreated {len(url_mapping)} URL mappings")
    
    # Update content files
    print("\nUpdating content files...")
    updates_made, files_updated = update_content_files(url_mapping, content_files)
    
    print(f"\n=== Update Complete ===")
    print(f"Files updated: {files_updated}")
    print(f"URL replacements made: {updates_made}")
    
    # Show remaining external URLs
    remaining_urls, _ = find_all_external_urls()
    unmapped_urls = [url for url in remaining_urls if url not in url_mapping]
    
    if unmapped_urls:
        print(f"\nRemaining external URLs: {len(unmapped_urls)}")
        for i, url in enumerate(unmapped_urls[:10]):
            print(f"  {i+1}. {url}")
        if len(unmapped_urls) > 10:
            print(f"  ... and {len(unmapped_urls) - 10} more")

if __name__ == "__main__":
    main()
