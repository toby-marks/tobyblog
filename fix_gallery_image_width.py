#!/usr/bin/env python3
"""
Script to update gallery images to use w=365 instead of w=780 in Cloudflare URLs
"""

import re
import glob
import os

def fix_gallery_image_width_in_file(file_path):
    """Fix gallery image widths in a single file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        fixes_made = 0
        
        # Function to fix width in a single img tag within gallery
        def fix_img_width(match):
            nonlocal fixes_made
            full_img_tag = match.group(0)
            
            # Check if this img tag has a Cloudflare URL in src attribute
            src_match = re.search(r'src="([^"]*imagedelivery\.net[^"]*)"', full_img_tag)
            if not src_match:
                return full_img_tag  # No Cloudflare URL in src, skip
            
            src_url = src_match.group(1)
            
            # Replace w=780 with w=365 in the src URL
            if 'w=780' in src_url:
                new_src_url = src_url.replace('w=780', 'w=365')
                fixed_img_tag = full_img_tag.replace(src_url, new_src_url)
                
                if fixed_img_tag != full_img_tag:
                    fixes_made += 1
                    print(f"   Fixed img width: w=780 → w=365")
                
                return fixed_img_tag
            
            return full_img_tag
        
        # Find gallery divs and process img tags within them
        def fix_gallery_div(match):
            gallery_content = match.group(1)
            
            # Fix all img tags within this gallery div
            fixed_gallery_content = re.sub(
                r'<img[^>]+>',
                fix_img_width,
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
            print(f"✅ Fixed {file_path}: {fixes_made} image widths updated")
            return fixes_made
        else:
            print(f"ℹ️  No gallery image widths to fix in {file_path}")
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
    print("🔍 Finding files with gallery divs to update image widths...")
    
    gallery_files = find_files_with_gallery_divs()
    
    if not gallery_files:
        print("✅ No files with gallery divs found!")
        return
    
    print(f"📊 Found {len(gallery_files)} files with gallery divs")
    print("\n🔧 Processing files to change w=780 to w=365...\n")
    
    total_fixes = 0
    fixed_files = 0
    
    for file_path in gallery_files:
        print(f"📄 Processing {file_path}...")
        fixes = fix_gallery_image_width_in_file(file_path)
        if fixes > 0:
            fixed_files += 1
            total_fixes += fixes
    
    print(f"\n🎉 Summary:")
    print(f"   Files processed: {len(gallery_files)}")
    print(f"   Files with width changes: {fixed_files}")
    print(f"   Total width fixes: {total_fixes}")
    
    if total_fixes > 0:
        print(f"\n✅ Gallery image widths updated! All gallery images now use w=365.")
    else:
        print(f"\nℹ️  No gallery image widths needed updating.")

if __name__ == "__main__":
    main()
