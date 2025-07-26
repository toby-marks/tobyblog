#!/usr/bin/env python3
"""
Script to identify files with broken image references for manual fixing
"""

import json
import os
import re
import glob
from collections import defaultdict

def load_mapping():
    """Load the Cloudflare image mapping"""
    try:
        with open('cloudflare_image_mapping.json', 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading mapping: {e}")
        return {}

def find_broken_references():
    """Find all files with broken local image references"""
    mapping = load_mapping()
    mapped_images = set(mapping.keys())
    
    broken_files = []
    
    # Search all markdown files in content directory
    for md_file in glob.glob('content/**/*.md', recursive=True):
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find all local image references
            matches = re.findall(r'(src="|["\(])/images/([^"\)\s>]+)(["\)>])', content)
            
            broken_refs_in_file = []
            for match in matches:
                image_path = match[1]  # The actual path part
                full_path = f"images/{image_path}"
                
                # Check if this image is in the mapping
                if full_path not in mapped_images:
                    broken_refs_in_file.append(image_path)
            
            if broken_refs_in_file:
                broken_files.append({
                    'file': md_file,
                    'broken_refs': broken_refs_in_file,
                    'count': len(broken_refs_in_file)
                })
                
        except Exception as e:
            print(f"Error reading {md_file}: {e}")
    
    return broken_files

def group_by_directory(broken_files):
    """Group broken files by their content directory"""
    groups = defaultdict(list)
    
    for file_info in broken_files:
        # Extract the content subdirectory (posts, photos, microposts, etc.)
        file_path = file_info['file']
        if file_path.startswith('content/'):
            subdir = file_path.split('/')[1]  # Get the subdirectory
            groups[subdir].append(file_info)
        else:
            groups['other'].append(file_info)
    
    return groups

def main():
    print("🔍 Identifying files with broken image references...\n")
    
    broken_files = find_broken_references()
    
    if not broken_files:
        print("✅ No broken image references found!")
        return
    
    # Group by directory
    groups = group_by_directory(broken_files)
    
    # Sort files by number of broken references (most broken first)
    broken_files.sort(key=lambda x: x['count'], reverse=True)
    
    total_broken_refs = sum(f['count'] for f in broken_files)
    
    print(f"📊 Summary:")
    print(f"   Files with broken references: {len(broken_files)}")
    print(f"   Total broken image references: {total_broken_refs}")
    
    print(f"\n📂 Breakdown by content directory:")
    for subdir, files in sorted(groups.items()):
        total_refs = sum(f['count'] for f in files)
        print(f"   {subdir}/: {len(files)} files, {total_refs} broken refs")
    
    print(f"\n📋 Files to fix (ordered by number of broken references):")
    print("=" * 80)
    
    for file_info in broken_files:
        file_path = file_info['file']
        count = file_info['count']
        
        print(f"\n📄 {file_path}")
        print(f"   🔗 {count} broken image reference{'s' if count != 1 else ''}")
        
        # Show first few broken references as examples
        examples = file_info['broken_refs'][:3]
        for ref in examples:
            print(f"   📸 /images/{ref}")
        
        if len(file_info['broken_refs']) > 3:
            remaining = len(file_info['broken_refs']) - 3
            print(f"   ... and {remaining} more")
    
    print(f"\n" + "=" * 80)
    print(f"💡 Tip: These references point to image size variants that were never")
    print(f"   uploaded to Cloudflare. You can either:")
    print(f"   1. Remove the broken image references")
    print(f"   2. Replace them with similar images from the Cloudflare mapping")
    print(f"   3. Find and upload the missing image variants")

if __name__ == "__main__":
    main()
