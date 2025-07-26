#!/usr/bin/env python3

import os
import re
from pathlib import Path

def fix_gallery_src_width(content_dir):
    """
    Change only src attributes in gallery images from w=780 to w=365
    Leave data-image attributes unchanged
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
            
        # Find gallery sections and process them
        gallery_sections = []
        start = 0
        
        while True:
            gallery_start = content.find('<div id="gallery">', start)
            if gallery_start == -1:
                break
                
            gallery_end = content.find('</div>', gallery_start)
            if gallery_end == -1:
                break
                
            gallery_section = content[gallery_start:gallery_end + 6]
            
            # In this gallery section, replace src attributes with w=780 to w=365
            # Only change src, not data-image
            modified_section = re.sub(
                r'src="([^"]*?)w=780([^"]*?)"',
                r'src="\1w=365\2"',
                gallery_section
            )
            
            gallery_sections.append((gallery_start, gallery_end + 6, modified_section))
            start = gallery_end + 6
        
        # Apply all modifications
        if gallery_sections:
            # Process in reverse order to maintain indices
            for gallery_start, gallery_end, modified_section in reversed(gallery_sections):
                content = content[:gallery_start] + modified_section + content[gallery_end:]
        
        if content != original_content:
            # Count how many src attributes were changed
            changes = content.count('src="') - original_content.count('src="') + \
                     original_content.count('w=780') - content.count('w=780')
            
            # More accurate count: count src attributes with w=365 in gallery sections
            src_365_count = 0
            for _, _, section in gallery_sections:
                src_365_count += section.count('src="') and section.count('w=365')
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            files_processed += 1
            replacements = len(re.findall(r'src="[^"]*w=365[^"]*"', content))
            total_replacements += replacements
            print(f"Fixed {file_path.name}: Changed src width to w=365 for {replacements} images")
    
    print(f"\nSummary:")
    print(f"Files processed: {files_processed}")
    print(f"Total src attributes changed to w=365: {total_replacements}")

if __name__ == "__main__":
    content_dir = "content"
    fix_gallery_src_width(content_dir)
