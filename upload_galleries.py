#!/usr/bin/env python3
"""
Upload images from ~/Desktop/bestof to Cloudflare and generate gallery markdown files.
"""

import os
import json
import subprocess
from pathlib import Path
from datetime import datetime

# Cloudflare credentials
CF_ACCOUNT_ID = "44aaa2fa622a6206bffc812de90c4b52"
CF_API_KEY = "L_zONhXl3qN8zIIJVvnA1D6E85ruqibEgcDhgiUY"

# Cloudflare Images API endpoint
API_URL = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/images/v1"

# Gallery configuration
PHOTOS_PER_GALLERY = 50
BESTOF_DIR = Path.home() / "Desktop" / "bestof"
GALLERIES_DIR = Path("content/galleries")

def upload_image(image_path):
    """Upload a single image to Cloudflare and return the image ID."""
    print(f"Uploading {image_path.name}...")
    
    cmd = [
        'curl', '-X', 'POST',
        API_URL,
        '-H', f'Authorization: Bearer {CF_API_KEY}',
        '-F', f'file=@{image_path}'
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        response_data = json.loads(result.stdout)
        
        if response_data.get('success'):
            image_id = response_data['result']['id']
            print(f"  ✓ Uploaded: {image_id}")
            return image_id
        else:
            print(f"  ✗ Failed: {response_data.get('errors')}")
            return None
    except subprocess.CalledProcessError as e:
        print(f"  ✗ Error: {e.stderr}")
        return None
    except json.JSONDecodeError as e:
        print(f"  ✗ JSON decode error: {e}")
        return None

def generate_gallery_url(image_id, width=1600):
    """Generate Cloudflare image delivery URL."""
    base = "https://imagedelivery.net/zJmFZzaNuqC_Q5Caqyu8nQ"
    params = "fit=scale-down,w={},sharpen=1,f=auto,q=0.9,slow-connection-quality=0.3"
    return f"{base}/{image_id}/{params.format(width)}"

def create_gallery_file(gallery_num, image_ids, total_galleries):
    """Create a gallery markdown file with the given image IDs."""
    filename = f"bestof-gallery-{gallery_num:02d}.md"
    filepath = GALLERIES_DIR / filename
    
    # Create TOML frontmatter
    content = f"""+++
title = "Best Of — Gallery {gallery_num} of {total_galleries}"
description = "A curated collection of memorable photographs (Gallery {gallery_num})."
date = "{datetime.now().strftime('%Y-%m-%dT%H:%M:%S-06:00')}"
categories = ["photography"]
draft = false

# Used for preview cards / social sharing
images = ["{generate_gallery_url(image_ids[0], 1024)}"]

"""
    
    # Add gallery entries
    for idx, image_id in enumerate(image_ids, 1):
        content += f"""[[gallery]]
src = "{generate_gallery_url(image_id, 1600)}"
thumb = "{generate_gallery_url(image_id, 480)}"
caption = "Photo {idx}"

"""
    
    # Close frontmatter and add shortcode
    content += """+++

{{< gallery >}}
"""
    
    # Write file
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w') as f:
        f.write(content)
    
    print(f"Created {filename}")

def main():
    # Get sorted list of images
    image_files = sorted(BESTOF_DIR.glob("idx*.jpg"), key=lambda x: int(x.stem[3:]))
    print(f"Found {len(image_files)} images to upload\n")
    
    # Upload all images and collect IDs
    image_ids = []
    for i, img_path in enumerate(image_files, 1):
        print(f"[{i}/{len(image_files)}]", end=" ")
        image_id = upload_image(img_path)
        if image_id:
            image_ids.append(image_id)
        else:
            print(f"Skipping {img_path.name} due to upload failure")
    
    print(f"\n✓ Successfully uploaded {len(image_ids)} images")
    
    # Calculate galleries needed
    total_galleries = (len(image_ids) + PHOTOS_PER_GALLERY - 1) // PHOTOS_PER_GALLERY
    print(f"\nCreating {total_galleries} gallery files...")
    
    # Create gallery files
    for gallery_num in range(1, total_galleries + 1):
        start_idx = (gallery_num - 1) * PHOTOS_PER_GALLERY
        end_idx = min(start_idx + PHOTOS_PER_GALLERY, len(image_ids))
        gallery_image_ids = image_ids[start_idx:end_idx]
        
        create_gallery_file(gallery_num, gallery_image_ids, total_galleries)
    
    print(f"\n✓ All done! Created {total_galleries} galleries with {len(image_ids)} total photos.")

if __name__ == "__main__":
    main()
