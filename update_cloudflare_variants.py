#!/usr/bin/env python3
"""
Script to update Cloudflare image URLs from /public variant to custom variant
"""

import os
import re
import glob

def update_cloudflare_variants():
    """Update all Cloudflare image URLs to use custom variant instead of /public"""
    
    # Define the replacement
    old_variant = "/public"
    new_variant = "/fit=scale-down,w=780,sharpen=1,f=auto,q=0.9,slow-connection-quality=0.3"
    
    # Pattern to match Cloudflare imagedelivery URLs with /public
    cloudflare_pattern = r'(https://imagedelivery\.net/[^/]+/[^/]+)/public'
    
    files_updated = 0
    total_replacements = 0
    
    # Find all markdown files in content directory
    content_files = glob.glob('content/**/*.md', recursive=True)
    
    print(f"Found {len(content_files)} markdown files to process...")
    
    for file_path in content_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Replace Cloudflare URLs with /public variant
            content, replacements = re.subn(
                cloudflare_pattern,
                r'\1' + new_variant,
                content
            )
            
            if replacements > 0:
                # Write back the updated content
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                files_updated += 1
                total_replacements += replacements
                print(f"Updated {file_path}: {replacements} URLs replaced")
        
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
    
    print(f"\nSummary:")
    print(f"Files updated: {files_updated}")
    print(f"Total URL replacements: {total_replacements}")
    print(f"Old variant: {old_variant}")
    print(f"New variant: {new_variant}")

if __name__ == "__main__":
    # Change to the script's directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    update_cloudflare_variants()
