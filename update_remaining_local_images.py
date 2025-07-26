#!/usr/bin/env python3
"""
Script to update remaining local image paths with Cloudflare URLs using the mapping file
"""

import os
import json
import re

def update_local_images():
    """Update local image paths with their Cloudflare URLs"""
    
    # Load the Cloudflare mapping
    with open('cloudflare_image_mapping.json', 'r') as f:
        mapping = json.load(f)
    
    # Create a mapping from local paths to Cloudflare URLs with new variant
    path_to_cloudflare = {}
    new_variant = "/fit=scale-down,w=780,sharpen=1,f=auto,q=0.9,slow-connection-quality=0.3"
    
    for local_path, details in mapping.items():
        cloudflare_url = details['cloudflare_url']
        # Replace /public with custom variant
        cloudflare_url = cloudflare_url.replace('/public', new_variant)
        path_to_cloudflare[local_path] = cloudflare_url
    
    # Process the specific file
    file_path = 'content/posts/20250531-2025-road-trip-day-2.md'
    
    print(f"Processing {file_path}...")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        replacements = 0
        
        # Find all local image references
        local_image_pattern = r'!\[([^\]]*)\]\(/images/([^)]+)\)'
        
        def replace_local_image(match):
            nonlocal replacements
            alt_text = match.group(1)
            image_path = match.group(2)
            full_path = f"images/{image_path}"
            
            if full_path in path_to_cloudflare:
                cloudflare_url = path_to_cloudflare[full_path]
                replacements += 1
                print(f"  Replacing: /images/{image_path}")
                print(f"  With: {cloudflare_url}")
                return f"![{alt_text}]({cloudflare_url})"
            else:
                print(f"  No mapping found for: /images/{image_path}")
                return match.group(0)  # Return unchanged
        
        # Replace local image references
        content = re.sub(local_image_pattern, replace_local_image, content)
        
        if replacements > 0:
            # Write back the updated content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"✅ Updated {file_path}: {replacements} images replaced")
        else:
            print(f"No local images found to replace in {file_path}")
    
    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")

if __name__ == "__main__":
    # Change to the script's directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    update_local_images()
