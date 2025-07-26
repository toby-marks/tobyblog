#!/usr/bin/env python3
"""
Script to update ALL remaining local image references to Cloudflare URLs
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

def process_file(file_path, mapping):
    """Process a single markdown file and update local image references"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        replacements = 0
        
        # Find all local image references
        # Pattern matches /images/... paths in markdown and HTML
        def replace_image(match):
            nonlocal replacements
            full_match = match.group(0)
            prefix = match.group(1)  # src=" or " or (
            image_path = match.group(2)  # the actual path
            suffix = match.group(3)  # " or ) or >
            mapping_key = f"images/{image_path}"
            
            if mapping_key in mapping:
                cloudflare_url = mapping[mapping_key]["cloudflare_url"]
                # Replace the /public variant with your custom variant
                cloudflare_url = cloudflare_url.replace('/public', '/fit=scale-down,w=780,sharpen=1,f=auto,q=0.9,slow-connection-quality=0.3')
                
                replacements += 1
                print(f"  Replacing: /images/{image_path}")
                print(f"  With: {cloudflare_url}")
                
                # Replace the path while preserving prefix and suffix
                return f"{prefix}{cloudflare_url}{suffix}"
            else:
                print(f"  ⚠️  No mapping found for: /images/{image_path}")
                return full_match
        
        # Pattern to match /images/... in various contexts
        # This handles: src="/images/...", ("/images/..."), and similar patterns
        content = re.sub(r'(src="|["\(])/images/([^"\)\s>]+)(["\)>])', replace_image, content)
        
        # If we made changes, write the file back
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Updated {file_path}: {replacements} images replaced")
            return replacements
        else:
            print(f"ℹ️  No changes needed for {file_path}")
            return 0
            
    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")
        return 0

def main():
    print("🚀 Updating ALL remaining local image references to Cloudflare URLs...")
    
    # Load Cloudflare mapping
    mapping = load_mapping()
    if not mapping:
        print("❌ Could not load Cloudflare mapping file")
        return
    
    print(f"📊 Loaded {len(mapping)} images from Cloudflare mapping")
    
    # Find all markdown files with local image references
    files_to_process = []
    total_references = 0
    
    for md_file in glob.glob('content/**/*.md', recursive=True):
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Count local image references
            matches = re.findall(r'(src="|["\(])/images/([^"\)\s>]+)(["\)>])', content)
            if matches:
                files_to_process.append(md_file)
                total_references += len(matches)
                
        except Exception as e:
            print(f"Error reading {md_file}: {e}")
    
    print(f"📊 Found {len(files_to_process)} files with {total_references} local image references")
    
    if not files_to_process:
        print("✅ No files need updating!")
        return
    
    # Process each file
    total_replacements = 0
    updated_files = 0
    
    for file_path in files_to_process:
        print(f"\n📄 Processing {file_path}...")
        replacements = process_file(file_path, mapping)
        if replacements > 0:
            updated_files += 1
            total_replacements += replacements
    
    print(f"\n🎉 Summary:")
    print(f"   📁 {updated_files} files updated")
    print(f"   🔗 {total_replacements} image references converted to Cloudflare URLs")
    print(f"   ✅ Migration complete!")

if __name__ == "__main__":
    main()
