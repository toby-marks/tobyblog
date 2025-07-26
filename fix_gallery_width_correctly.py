#!/usr/bin/env python3
"""
Script to correctly set gallery image widths:
- src attribute should have w=365 (thumbnails)
- data-image attribute should have w=780 (full-size display)
"""

import re
import glob
import os

def fix_gallery_widths_correctly_in_file(file_path):
    """Fix gallery image widths correctly in a single file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        fixes_made = 0
        
        # Function to fix widths in a single img tag within gallery
        def fix_img_widths(match):
            nonlocal fixes_made
            full_img_tag = match.group(0)
            
            # Extract both src and data-image URLs
            src_match = re.search(r'src="([^"]*imagedelivery\.net[^"]*)"', full_img_tag)
            data_image_match = re.search(r'data-image="([^"]*imagedelivery\.net[^"]*)"', full_img_tag)
            
            if not src_match or not data_image_match:
                return full_img_tag  # Skip if either URL is missing
            
            src_url = src_match.group(1)
            data_image_url = data_image_match.group(1)
            
            changed = False
            
            # Fix src URL: should have w=365
            if 'w=780' in src_url:
                new_src_url = src_url.replace('w=780', 'w=365')
                full_img_tag = full_img_tag.replace(src_url, new_src_url)
                changed = True
            
            # Fix data-image URL: should have w=780
            if 'w=365' in data_image_url:
                new_data_image_url = data_image_url.replace('w=365', 'w=780')
                full_img_tag = full_img_tag.replace(data_image_url, new_data_image_url)
                changed = True
            
            if changed:
                fixes_made += 1
                print(f"   Fixed img: src→w=365, data-image→w=780")
            
            return full_img_tag
        
        # Find gallery divs and process img tags within them
        def fix_gallery_div(match):
            gallery_content = match.group(1)
            
            # Fix all img tags within this gallery div
            fixed_gallery_content = re.sub(
                r'<img[^>]+>',
                fix_img_widths,
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
            print(f"✅ Fixed {file_path}: {fixes_made} images corrected")
            return fixes_made
        else:
            print(f"ℹ️  No gallery image widths to correct in {file_path}")
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
    print("🔍 Finding files with gallery divs to correct image widths...")
    print("   Setting: src → w=365 (thumbnails), data-image → w=780 (full-size)")
    
    gallery_files = find_files_with_gallery_divs()
    
    if not gallery_files:
        print("✅ No files with gallery divs found!")
        return
    
    print(f"📊 Found {len(gallery_files)} files with gallery divs")
    print(f"\n🔧 Processing files...\n")
    
    total_fixes = 0
    fixed_files = 0
    
    for file_path in gallery_files:
        print(f"📄 Processing {file_path}...")
        fixes = fix_gallery_widths_correctly_in_file(file_path)
        if fixes > 0:
            fixed_files += 1
            total_fixes += fixes
    
    print(f"\n🎉 Summary:")
    print(f"   Files processed: {len(gallery_files)}")
    print(f"   Files corrected: {fixed_files}")
    print(f"   Total image corrections: {total_fixes}")
    
    if total_fixes > 0:
        print(f"\n✅ Gallery image widths corrected!")
        print(f"   src attributes now use w=365 (thumbnails)")
        print(f"   data-image attributes now use w=780 (full-size)")
    else:
        print(f"\nℹ️  No gallery image widths needed correction.")

if __name__ == "__main__":
    main()
