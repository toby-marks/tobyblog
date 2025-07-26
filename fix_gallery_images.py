#!/usr/bin/env python3
"""
Script to fix gallery images by copying data-image to src attribute
This fixes broken local image references in <div id="gallery"> sections
"""

import re
import glob
import os

def fix_gallery_images_in_file(file_path):
    """Fix gallery images in a single file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        fixes_made = 0
        
        # Pattern to match img tags within gallery divs that have both src and data-image
        # This handles multi-line img tags and various attribute orders
        def fix_img_tag(match):
            nonlocal fixes_made
            full_img_tag = match.group(0)
            
            # Extract the data-image URL
            data_image_match = re.search(r'data-image="([^"]+)"', full_img_tag)
            if not data_image_match:
                return full_img_tag  # No data-image found, skip
            
            data_image_url = data_image_match.group(1)
            
            # Replace the src attribute with the data-image URL
            fixed_img_tag = re.sub(
                r'src="[^"]*"',
                f'src="{data_image_url}"',
                full_img_tag
            )
            
            if fixed_img_tag != full_img_tag:
                fixes_made += 1
                print(f"   Fixed img tag: src now points to Cloudflare URL")
            
            return fixed_img_tag
        
        # Find gallery divs and process img tags within them
        def fix_gallery_div(match):
            gallery_content = match.group(1)
            
            # Fix all img tags within this gallery div
            fixed_gallery_content = re.sub(
                r'<img[^>]+>',
                fix_img_tag,
                gallery_content,
                flags=re.DOTALL
            )
            
            return f'<div id="gallery">{fixed_gallery_content}</div>'
        
        # Process all gallery divs
        content = re.sub(
            r'<div id="gallery">(.*?)</div>',
            fix_gallery_div,
            content,
            flags=re.DOTALL
        )
        
        # Write back if changes were made
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Fixed {file_path}: {fixes_made} images updated")
            return fixes_made
        else:
            print(f"ℹ️  No gallery images to fix in {file_path}")
            return 0
            
    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")
        return 0

def find_files_with_gallery_divs():
    """Find all markdown files that contain gallery divs"""
    gallery_files = []
    
    for md_file in glob.glob('content/**/*.md', recursive=True):
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            if '<div id="gallery">' in content:
                gallery_files.append(md_file)
                
        except Exception as e:
            print(f"Error reading {md_file}: {e}")
    
    return gallery_files

def main():
    print("🔍 Finding files with gallery divs...")
    
    gallery_files = find_files_with_gallery_divs()
    
    if not gallery_files:
        print("✅ No files with gallery divs found!")
        return
    
    print(f"📊 Found {len(gallery_files)} files with gallery divs")
    print("\n🔧 Processing files...\n")
    
    total_fixes = 0
    fixed_files = 0
    
    for file_path in gallery_files:
        print(f"📄 Processing {file_path}...")
        fixes = fix_gallery_images_in_file(file_path)
        if fixes > 0:
            fixed_files += 1
            total_fixes += fixes
    
    print(f"\n🎉 Summary:")
    print(f"   Files processed: {len(gallery_files)}")
    print(f"   Files fixed: {fixed_files}")
    print(f"   Total image fixes: {total_fixes}")
    
    if total_fixes > 0:
        print(f"\n✅ Gallery images have been fixed! The src attributes now point to Cloudflare URLs.")
    else:
        print(f"\nℹ️  No gallery images needed fixing.")

if __name__ == "__main__":
    main()
