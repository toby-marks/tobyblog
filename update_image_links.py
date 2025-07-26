#!/usr/bin/env python3

import os
import re
import glob
from urllib.parse import urlparse
from pathlib import Path

def get_filename_from_url(url):
    """Extract filename from URL, handling various URL formats"""
    # Parse the URL
    parsed = urlparse(url)
    path = parsed.path
    
    # Get the filename from the path
    filename = os.path.basename(path)
    
    # Handle special cases for different image hosts
    if 'cloudinary.com' in url:
        # For Cloudinary URLs, get the last part after the last slash
        # Example: https://res.cloudinary.com/tobyblog/image/upload/v1552602904/img/25A20639-6AB5-428E-B013-951140B9B004.jpg
        # Should return: 25A20639-6AB5-428E-B013-951140B9B004.jpg
        filename = path.split('/')[-1]
    elif 'blogspot.com' in url or 'blogger.com' in url:
        # For Blogger URLs, get the filename after the last slash
        # Example: http://1.bp.blogspot.com/-DRar78BwABo/VhQ0Oy9ErmI/AAAAAAAACtc/xcByxuyYafE/s2048/apple-touch-icon-72x72.png
        # Should return: apple-touch-icon-72x72.png
        filename = path.split('/')[-1]
    elif 'flickr.com' in url:
        # For Flickr URLs, get the filename
        # Example: https://farm7.staticflickr.com/6045/6297155248_3b1d37a5a7_b.jpg
        # Should return: 6297155248_3b1d37a5a7_b.jpg
        filename = path.split('/')[-1]
    
    return filename

def find_local_image_path(filename, post_name):
    """Find the local path for an image file"""
    # Look in the post-specific directory first
    post_dir = f"static/images/{post_name}"
    if os.path.exists(f"{post_dir}/{filename}"):
        return f"/images/{post_name}/{filename}"
    
    # Look in the images directory
    images_dir = "static/images/images"
    if os.path.exists(f"{images_dir}/{filename}"):
        return f"/images/images/{filename}"
    
    # Search in all subdirectories
    for root, dirs, files in os.walk("static/images"):
        if filename in files:
            # Convert to web path
            rel_path = os.path.relpath(os.path.join(root, filename), "static")
            return f"/{rel_path}"
    
    return None

def get_post_name_from_file(filepath):
    """Extract post name from markdown filename"""
    filename = os.path.basename(filepath)
    # Remove .md extension
    post_name = filename.replace('.md', '')
    return post_name

def update_content_file(filepath):
    """Update image URLs in a single content file"""
    print(f"Processing: {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    post_name = get_post_name_from_file(filepath)
    updates_made = 0
    
    # Pattern to match various image URL formats
    patterns = [
        # Hugo figure shortcode: {{< figure src="URL" >}}
        r'\{\{\s*<\s*figure[^>]*src="([^"]+)"[^>]*>\s*\}\}',
        # HTML img tags: <img src="URL">
        r'<img[^>]+src="([^"]+)"[^>]*>',
        # Markdown images: ![alt](URL)
        r'!\[[^\]]*\]\(([^)]+)\)',
        # YAML frontmatter images array
        r'images\s*=\s*\["([^"]+)"\]',
        # YAML frontmatter single image
        r'image\s*=\s*"([^"]+)"',
    ]
    
    for pattern in patterns:
        matches = re.finditer(pattern, content)
        for match in matches:
            url = match.group(1)
            
            # Skip if it's already a local path
            if url.startswith('/') or url.startswith('./') or url.startswith('../'):
                continue
            
            # Skip if it's not an image URL we care about
            if not any(host in url for host in ['cloudinary.com', 'blogspot.com', 'blogger.com', 'flickr.com', 'staticflickr.com']):
                continue
            
            # Get filename from URL
            filename = get_filename_from_url(url)
            if not filename:
                continue
            
            # Find local path
            local_path = find_local_image_path(filename, post_name)
            if local_path:
                # Replace the URL with local path
                content = content.replace(url, local_path)
                updates_made += 1
                print(f"  Updated: {filename} -> {local_path}")
            else:
                print(f"  Warning: Local file not found for {filename}")
    
    # Write back if changes were made
    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  ✓ {updates_made} updates saved to {filepath}")
    else:
        print(f"  No changes needed for {filepath}")
    
    return updates_made

def main():
    """Update all image links in content files"""
    print("Updating image links in content files...")
    
    # Find all markdown files in content directory
    content_files = glob.glob("content/**/*.md", recursive=True)
    
    total_updates = 0
    files_updated = 0
    
    for filepath in content_files:
        updates = update_content_file(filepath)
        if updates > 0:
            files_updated += 1
            total_updates += updates
    
    print(f"\nSummary:")
    print(f"Files processed: {len(content_files)}")
    print(f"Files updated: {files_updated}")
    print(f"Total link updates: {total_updates}")

if __name__ == "__main__":
    main()
