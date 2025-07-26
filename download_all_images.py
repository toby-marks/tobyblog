#!/usr/bin/env python3
"""
Comprehensive script to download images from all sources:
- Flickr (live.staticflickr.com)
- Cloudinary (res.cloudinary.com) 
- Blogger/Blogspot (bp.blogspot.com)
- Any other remote URLs
Skips already downloaded files.
"""

import os
import re
import requests
import flickrapi
from urllib.parse import urlparse
import time
from pathlib import Path

# Flickr API credentials
API_KEY = os.getenv('FLICKR_API_KEY', 'c242f16b21b8d6562ed0d48587f61432')
API_SECRET = os.getenv('FLICKR_API_SECRET', 'd27f067a55cf9c91')
USER_ID = os.getenv('FLICKR_USER_ID', '75738497@N00')

def extract_all_remote_urls():
    """Extract all remote image URLs from content files"""
    remote_urls = []
    content_dir = "content"
    
    for root, dirs, files in os.walk(content_dir):
        for file in files:
            if file.endswith('.md'):
                file_path = os.path.join(root, file)
                post_name = os.path.splitext(file)[0]
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Find all HTTP/HTTPS image URLs
                urls = re.findall(r'(https?://[^\s"\'<>]+\.(?:jpg|jpeg|png|gif|webp))', content, re.IGNORECASE)
                
                for url in urls:
                    # Parse URL to get filename
                    parsed = urlparse(url)
                    filename = os.path.basename(parsed.path)
                    
                    # Handle cases where there might be query parameters
                    if '?' in filename:
                        filename = filename.split('?')[0]
                    
                    if filename:
                        local_path = f'static/images/{post_name}/{filename}'
                        remote_urls.append({
                            'url': url,
                            'post_name': post_name,
                            'filename': filename,
                            'local_path': local_path,
                            'source': get_image_source(url)
                        })
    
    return remote_urls

def get_image_source(url):
    """Determine the source of an image URL"""
    if 'staticflickr.com' in url:
        return 'flickr'
    elif 'cloudinary.com' in url:
        return 'cloudinary'
    elif 'blogspot.com' in url or 'blogger.com' in url:
        return 'blogger'
    else:
        return 'other'

def file_already_exists(local_path):
    """Check if file already exists and has content"""
    if os.path.exists(local_path):
        try:
            # Check if file has content (not just "Access denied" text)
            with open(local_path, 'rb') as f:
                first_bytes = f.read(10)
                # Check for common image file signatures
                if (first_bytes.startswith(b'\xff\xd8') or  # JPEG
                    first_bytes.startswith(b'\x89PNG') or  # PNG
                    first_bytes.startswith(b'GIF8') or     # GIF
                    first_bytes.startswith(b'RIFF')):     # WebP
                    return True
        except:
            pass
    return False

def download_flickr_image(url, local_path, filename):
    """Download image from Flickr using API if possible, fallback to direct download"""
    try:
        # Try to extract photo ID from filename
        photo_id_match = re.match(r'(\d+)_[^_]+_[^.]+\.(jpg|jpeg|png|gif)', filename)
        
        if photo_id_match:
            photo_id = photo_id_match.group(1)
            try:
                # Try Flickr API first
                flickr = flickrapi.FlickrAPI(API_KEY, API_SECRET, format='parsed-json')
                sizes = flickr.photos.getSizes(photo_id=photo_id)
                
                # Find the best size URL
                target_url = None
                for size in sizes['sizes']['size']:
                    if filename in size['source']:
                        target_url = size['source']
                        break
                
                if not target_url and sizes['sizes']['size']:
                    target_url = sizes['sizes']['size'][-1]['source']
                
                if target_url:
                    return download_direct(target_url, local_path)
            except:
                pass
        
        # Fallback to direct download
        return download_direct(url, local_path)
        
    except Exception as e:
        print(f"Error downloading Flickr image {filename}: {str(e)}")
        return False

def download_direct(url, local_path):
    """Download image directly from URL"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        
        response = requests.get(url, stream=True, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        
        # Save the image
        with open(local_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        return True
        
    except Exception as e:
        print(f"Error downloading {url}: {str(e)}")
        return False

def download_image(url_info):
    """Download image based on source"""
    if url_info['source'] == 'flickr':
        return download_flickr_image(url_info['url'], url_info['local_path'], url_info['filename'])
    else:
        return download_direct(url_info['url'], url_info['local_path'])

def main():
    """Main function to download all remote images"""
    print("Extracting all remote image URLs from content files...")
    all_urls = extract_all_remote_urls()
    
    # Filter out already downloaded files
    urls_to_download = []
    already_downloaded = 0
    
    for url_info in all_urls:
        if file_already_exists(url_info['local_path']):
            already_downloaded += 1
        else:
            urls_to_download.append(url_info)
    
    print(f"Found {len(all_urls)} total remote images")
    print(f"Already downloaded: {already_downloaded}")
    print(f"Need to download: {len(urls_to_download)}")
    
    if not urls_to_download:
        print("All images already downloaded!")
        return
    
    # Group by source for reporting
    sources = {}
    for url_info in urls_to_download:
        source = url_info['source']
        if source not in sources:
            sources[source] = []
        sources[source].append(url_info)
    
    print(f"\nImages by source:")
    for source, urls in sources.items():
        print(f"  {source}: {len(urls)} images")
    
    successful_downloads = 0
    failed_downloads = 0
    
    for i, url_info in enumerate(urls_to_download, 1):
        print(f"\nProcessing {i}/{len(urls_to_download)}: {url_info['filename']} ({url_info['source']})")
        
        success = download_image(url_info)
        
        if success:
            successful_downloads += 1
            print(f"  ✓ Downloaded: {url_info['local_path']}")
        else:
            failed_downloads += 1
            print(f"  ✗ Failed: {url_info['url']}")
        
        # Be nice to servers - small delay between requests
        time.sleep(0.2)
    
    print(f"\n=== Download Summary ===")
    print(f"Already downloaded: {already_downloaded}")
    print(f"Successful downloads: {successful_downloads}")
    print(f"Failed downloads: {failed_downloads}")
    print(f"Total images: {len(all_urls)}")
    
    # Calculate total size
    if os.path.exists('static/images'):
        import subprocess
        try:
            result = subprocess.run(['du', '-sh', 'static/images'], capture_output=True, text=True)
            if result.returncode == 0:
                size = result.stdout.split()[0]
                print(f"Total images directory size: {size}")
        except:
            pass

if __name__ == "__main__":
    main()
