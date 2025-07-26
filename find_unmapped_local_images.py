#!/usr/bin/env python3
"""
Script to find local image references that are not in the Cloudflare mapping
"""

import json
import os
import re
import glob

def load_mapping():
    """Load the Cloudflare image mapping"""
    try:
        with open('cloudflare_image_mapping.json', 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading mapping: {e}")
        return {}

def find_local_image_references():
    """Find all local image references in content files"""
    local_images = set()
    
    # Search all markdown files in content directory
    for md_file in glob.glob('content/**/*.md', recursive=True):
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Find all local image references
                # Pattern matches /images/... paths
                matches = re.findall(r'["\(]/images/([^")\s]+)["\)]', content)
                for match in matches:
                    local_images.add(f"images/{match}")
                    
        except Exception as e:
            print(f"Error reading {md_file}: {e}")
    
    return local_images

def check_file_existence(image_paths):
    """Check which local images actually exist on disk"""
    existing = set()
    missing = set()
    
    for img_path in image_paths:
        full_path = f"static/{img_path}"
        if os.path.exists(full_path):
            existing.add(img_path)
        else:
            missing.add(img_path)
    
    return existing, missing

def get_file_sizes(image_paths):
    """Get file sizes for existing images"""
    sizes = {}
    large_images = []
    
    for img_path in image_paths:
        full_path = f"static/{img_path}"
        if os.path.exists(full_path):
            size = os.path.getsize(full_path)
            sizes[img_path] = size
            
            # Flag images over 20MB
            if size > 20 * 1024 * 1024:
                large_images.append((img_path, size))
    
    return sizes, large_images

def main():
    print("🔍 Finding local image references not in Cloudflare mapping...")
    
    # Load Cloudflare mapping
    mapping = load_mapping()
    mapped_images = set(mapping.keys())
    print(f"📊 Found {len(mapped_images)} images in Cloudflare mapping")
    
    # Find local image references in content
    local_references = find_local_image_references()
    print(f"📊 Found {len(local_references)} local image references in content")
    
    # Find unmapped images
    unmapped = local_references - mapped_images
    print(f"📊 Found {len(unmapped)} local images not in Cloudflare mapping")
    
    if unmapped:
        # Check which ones actually exist
        existing, missing = check_file_existence(unmapped)
        
        print(f"\n📁 {len(existing)} unmapped images exist on disk:")
        print(f"🚫 {len(missing)} unmapped images are missing from disk")
        
        if existing:
            # Get file sizes
            sizes, large_images = get_file_sizes(existing)
            
            print(f"\n📏 Large images (>20MB) that may have failed upload:")
            if large_images:
                for img_path, size in large_images:
                    print(f"   💾 {img_path}: {size:,} bytes ({size / (1024*1024):.1f}MB)")
            else:
                print("   ✅ No large images found!")
            
            print(f"\n📋 Sample unmapped existing images:")
            for i, img_path in enumerate(sorted(existing)):
                if i >= 10:  # Show first 10
                    print(f"   ... and {len(existing) - 10} more")
                    break
                size = sizes.get(img_path, 0)
                print(f"   📄 {img_path}: {size:,} bytes ({size / (1024*1024):.1f}MB)")
        
        if missing:
            print(f"\n🚫 Sample missing images (broken references):")
            for i, img_path in enumerate(sorted(missing)):
                if i >= 10:  # Show first 10
                    print(f"   ... and {len(missing) - 10} more")
                    break
                print(f"   ❌ {img_path}")
    
    else:
        print("\n✅ All local image references are already in Cloudflare mapping!")

if __name__ == "__main__":
    main()
