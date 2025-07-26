#!/usr/bin/env python3
"""
Script to download Flickr images from content files using the Flickr API
"""

import os
import re
import requests
import flickrapi
from urllib.parse import urlparse
import time

# Flickr API credentials - get from environment variables
API_KEY = os.getenv('FLICKR_API_KEY', 'c242f16b21b8d6562ed0d48587f61432')
API_SECRET = os.getenv('FLICKR_API_SECRET', 'd27f067a55cf9c91')
USER_ID = os.getenv('FLICKR_USER_ID', '75738497@N00')

def extract_flickr_urls_from_files():
    """Extract all Flickr URLs from content files"""
    flickr_urls = []
    content_dir = "content"
    
    for root, dirs, files in os.walk(content_dir):
        for file in files:
            if file.endswith('.md'):
                file_path = os.path.join(root, file)
                post_name = os.path.splitext(file)[0]
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Find all Flickr URLs in the content
                urls = re.findall(r'/images/([^/]+)/([^"\s]+)', content)
                for post_dir, filename in urls:
                    flickr_urls.append({
                        'post_name': post_dir,
                        'filename': filename,
                        'local_path': f'static/images/{post_dir}/{filename}'
                    })
    
    return flickr_urls

def get_photo_id_from_filename(filename):
    """Extract photo ID from Flickr filename"""
    # Flickr filenames are typically in format: PHOTOID_SECRET_SIZE.jpg
    match = re.match(r'(\d+)_[^_]+_[^.]+\.(jpg|jpeg|png|gif)', filename)
    if match:
        return match.group(1)
    return None

def download_image_from_flickr(photo_id, local_path, filename):
    """Download image from Flickr using the API"""
    try:
        # Initialize Flickr API
        flickr = flickrapi.FlickrAPI(API_KEY, API_SECRET, format='parsed-json')
        
        # Get photo sizes
        sizes = flickr.photos.getSizes(photo_id=photo_id)
        
        # Find the best size URL that matches our filename
        target_url = None
        for size in sizes['sizes']['size']:
            if filename in size['source']:
                target_url = size['source']
                break
        
        # If exact match not found, try the largest available
        if not target_url and sizes['sizes']['size']:
            target_url = sizes['sizes']['size'][-1]['source']
        
        if target_url:
            print(f"Downloading {filename} from {target_url}")
            
            # Download the image
            response = requests.get(target_url, stream=True)
            response.raise_for_status()
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            # Save the image
            with open(local_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"Successfully downloaded: {local_path}")
            return True
        else:
            print(f"Could not find download URL for {filename}")
            return False
            
    except Exception as e:
        print(f"Error downloading {filename}: {str(e)}")
        return False

def main():
    """Main function to download all Flickr images"""
    print("Extracting Flickr URLs from content files...")
    flickr_urls = extract_flickr_urls_from_files()
    
    print(f"Found {len(flickr_urls)} images to download")
    
    successful_downloads = 0
    failed_downloads = 0
    
    for i, url_info in enumerate(flickr_urls, 1):
        print(f"\nProcessing {i}/{len(flickr_urls)}: {url_info['filename']}")
        
        photo_id = get_photo_id_from_filename(url_info['filename'])
        if not photo_id:
            print(f"Could not extract photo ID from {url_info['filename']}")
            failed_downloads += 1
            continue
        
        success = download_image_from_flickr(
            photo_id, 
            url_info['local_path'], 
            url_info['filename']
        )
        
        if success:
            successful_downloads += 1
        else:
            failed_downloads += 1
        
        # Be nice to Flickr's API - small delay between requests
        time.sleep(0.1)
    
    print(f"\n=== Download Summary ===")
    print(f"Successful downloads: {successful_downloads}")
    print(f"Failed downloads: {failed_downloads}")
    print(f"Total processed: {len(flickr_urls)}")

if __name__ == "__main__":
    main()
