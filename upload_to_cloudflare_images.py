#!/usr/bin/env python3

import os
import requests
import json
import glob
import time
from pathlib import Path
import hashlib
import re

# Cloudflare Images configuration
# You'll need to set these environment variables:
# export CLOUDFLARE_ACCOUNT_ID="your_account_id"
# export CLOUDFLARE_API_TOKEN="your_api_token"

CLOUDFLARE_ACCOUNT_ID = os.getenv('CLOUDFLARE_ACCOUNT_ID')
CLOUDFLARE_API_TOKEN = os.getenv('CLOUDFLARE_API_TOKEN')

if not CLOUDFLARE_ACCOUNT_ID or not CLOUDFLARE_API_TOKEN:
    print("Error: Please set CLOUDFLARE_ACCOUNT_ID and CLOUDFLARE_API_TOKEN environment variables")
    print("Example:")
    print("export CLOUDFLARE_ACCOUNT_ID='your_account_id'")
    print("export CLOUDFLARE_API_TOKEN='your_api_token'")
    exit(1)

# Cloudflare Images API endpoint
CLOUDFLARE_IMAGES_API = f"https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}/images/v1"

def get_custom_id(file_path):
    """Generate a custom ID based on the file path"""
    # Use the relative path from static/ as the custom ID
    rel_path = os.path.relpath(file_path, "static")
    # Replace problematic characters and make it unique
    custom_id = rel_path.replace('/', '_').replace(' ', '_').replace('%', '_')
    # Ensure it doesn't look like a UUID by prefixing
    return f"tobyblog_{custom_id}"

def upload_image_to_cloudflare(file_path, image_id=None):
    """Upload an image to Cloudflare Images"""
    if not image_id:
        image_id = get_custom_id(file_path)
    
    headers = {
        'Authorization': f'Bearer {CLOUDFLARE_API_TOKEN}'
    }
    
    with open(file_path, 'rb') as f:
        files = {
            'file': f
        }
        data = {
            'id': image_id
        }
        
        response = requests.post(CLOUDFLARE_IMAGES_API, headers=headers, files=files, data=data)
    
    if response.status_code == 200:
        result = response.json()
        if result['success']:
            return result['result']
        else:
            print(f"Upload failed: {result['errors']}")
            return None
    else:
        print(f"HTTP Error {response.status_code}: {response.text}")
        return None

def create_upload_mapping():
    """Create a mapping of local files to Cloudflare URLs"""
    mapping_file = "cloudflare_image_mapping.json"
    
    if os.path.exists(mapping_file):
        with open(mapping_file, 'r') as f:
            return json.load(f)
    
    return {}

def save_upload_mapping(mapping):
    """Save the mapping to file"""
    with open("cloudflare_image_mapping.json", 'w') as f:
        json.dump(mapping, f, indent=2)

def upload_all_images():
    """Upload all images in static/images to Cloudflare Images"""
    mapping = create_upload_mapping()
    
    # Find all image files
    image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.gif', '*.webp']
    image_files = []
    
    for ext in image_extensions:
        image_files.extend(glob.glob(f"static/images/**/{ext}", recursive=True))
        image_files.extend(glob.glob(f"static/images/**/{ext.upper()}", recursive=True))
    
    print(f"Found {len(image_files)} images to upload")
    
    uploaded = 0
    skipped = 0
    failed = 0
    
    for file_path in image_files:
        # Create relative path for the key
        rel_path = os.path.relpath(file_path, "static")
        
        # Check if already uploaded
        if rel_path in mapping:
            print(f"Skipping {rel_path} (already uploaded)")
            skipped += 1
            continue
        
        print(f"Uploading {rel_path}...")
        
        # Upload to Cloudflare
        result = upload_image_to_cloudflare(file_path)
        
        if result:
            # Store the mapping
            mapping[rel_path] = {
                'cloudflare_id': result['id'],
                'cloudflare_url': result['variants'][0],  # Use the first variant
                'local_path': rel_path
            }
            
            uploaded += 1
            print(f"  ✓ Uploaded: {result['variants'][0]}")
            
            # Save mapping periodically
            if uploaded % 10 == 0:
                save_upload_mapping(mapping)
                print(f"Progress: {uploaded} uploaded, {skipped} skipped, {failed} failed")
        else:
            failed += 1
            print(f"  ✗ Failed to upload {rel_path}")
        
        # Rate limiting - Cloudflare Images has limits
        time.sleep(0.1)
    
    # Final save
    save_upload_mapping(mapping)
    
    print(f"\nUpload Summary:")
    print(f"Uploaded: {uploaded}")
    print(f"Skipped: {skipped}")
    print(f"Failed: {failed}")
    print(f"Total: {len(image_files)}")

def update_content_links():
    """Update content files to use Cloudflare Images URLs"""
    # Load the mapping
    if not os.path.exists("cloudflare_image_mapping.json"):
        print("No mapping file found. Run upload first.")
        return
    
    with open("cloudflare_image_mapping.json", 'r') as f:
        mapping = json.load(f)
    
    # Find all markdown files
    content_files = glob.glob("content/**/*.md", recursive=True)
    
    total_updates = 0
    files_updated = 0
    
    for filepath in content_files:
        print(f"Processing: {filepath}")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        updates_made = 0
        
        # Replace local image paths with Cloudflare URLs
        for local_path, cf_info in mapping.items():
            local_url = f"/{local_path}"
            cloudflare_url = cf_info['cloudflare_url']
            
            if local_url in content:
                content = content.replace(local_url, cloudflare_url)
                updates_made += 1
                print(f"  Updated: {local_path} -> {cloudflare_url}")
        
        # Write back if changes were made
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  ✓ {updates_made} updates saved to {filepath}")
            files_updated += 1
            total_updates += updates_made
        else:
            print(f"  No changes needed for {filepath}")
    
    print(f"\nUpdate Summary:")
    print(f"Files processed: {len(content_files)}")
    print(f"Files updated: {files_updated}")
    print(f"Total link updates: {total_updates}")

def main():
    import sys
    
    if len(sys.argv) != 2:
        print("Usage:")
        print("  python upload_to_cloudflare_images.py upload    # Upload images")
        print("  python upload_to_cloudflare_images.py update    # Update content links")
        print("  python upload_to_cloudflare_images.py both      # Do both")
        return
    
    command = sys.argv[1]
    
    if command == "upload":
        upload_all_images()
    elif command == "update":
        update_content_links()
    elif command == "both":
        upload_all_images()
        update_content_links()
    else:
        print("Invalid command. Use 'upload', 'update', or 'both'")

if __name__ == "__main__":
    main()
