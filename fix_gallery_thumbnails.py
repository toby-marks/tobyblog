#!/usr/bin/env python3

import os
import re
from pathlib import Path

def fix_gallery_images(content_dir):
    """
    Fix gallery images to use w=365 for src (thumbnails) while preserving data-image URLs
    """
    markdown_files = list(Path(content_dir).rglob("*.md"))
    
    files_processed = 0
    total_replacements = 0
    
    for file_path in markdown_files:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Check if file contains gallery div
        if '<div id="gallery">' not in content:
            continue
            
        # Pattern to match img tags within gallery divs
        # This captures the entire img tag and allows us to modify just the src attribute
        def fix_img_tag(match):
            img_tag = match.group(0)
            
            # Only modify src attribute, leave data-image unchanged
            # Pattern to find src attribute with Cloudflare URL and change width to 365
            src_pattern = r'src="(https://imagedelivery\.net/[^/]+/[^/]+/)w=\d+([^"]*")'
            
            def replace_src_width(src_match):
                return 'src="' + src_match.group(1) + 'w=365' + src_match.group(2)
            
            # Replace width in src attribute only
            modified_img_tag = re.sub(src_pattern, replace_src_width, img_tag)
            return modified_img_tag
        
        # Find all img tags within gallery divs
        gallery_pattern = r'<div id="gallery">.*?</div>'
        
        def process_gallery(gallery_match):
            gallery_content = gallery_match.group(0)
            img_pattern = r'<img[^>]*>'
            modified_gallery = re.sub(img_pattern, fix_img_tag, gallery_content)
            return modified_gallery
        
        # Process all galleries in the file
        content = re.sub(gallery_pattern, process_gallery, content, flags=re.DOTALL)
        
        if content != original_content:
            # Count replacements in this file
            src_replacements = len(re.findall(r'src="[^"]*w=365"', content))
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            files_processed += 1
            total_replacements += src_replacements
            print(f"Fixed {file_path.name}: {src_replacements} src attributes set to w=365")
    
    print(f"\nSummary:")
    print(f"Files processed: {files_processed}")
    print(f"Total src attributes fixed: {total_replacements}")

if __name__ == "__main__":
    content_dir = "content"
    fix_gallery_images(content_dir)
