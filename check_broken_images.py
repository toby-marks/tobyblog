#!/usr/bin/env python3
import os
import re
import glob
from pathlib import Path

def is_line_commented(line):
    """Check if a line is commented out (HTML or markdown comments)"""
    stripped = line.strip()
    # HTML comments
    if stripped.startswith('<!--') or stripped.endswith('-->'):
        return True
    # Check if line is inside HTML comment block
    return False

def is_in_comment_block(lines, line_index):
    """Check if current line is inside a comment block"""
    # Look backwards for comment start
    for i in range(line_index, -1, -1):
        line = lines[i].strip()
        if '<!--' in line and '-->' in line:
            # Single line comment, check if our content is in it
            comment_start = lines[i].find('<!--')
            comment_end = lines[i].find('-->') + 3
            if i == line_index:
                # Same line, check position
                return False  # We'll handle this in the main loop
            return False
        elif '<!--' in line:
            # Found comment start, now look forward for end
            for j in range(i, len(lines)):
                if '-->' in lines[j]:
                    if j >= line_index:
                        return True
                    break
            return False
        elif '-->' in line:
            return False
    return False

def extract_image_paths(content, file_path):
    """Extract image paths from markdown and HTML, excluding commented ones"""
    lines = content.split('\n')
    image_refs = []
    
    for i, line in enumerate(lines):
        # Skip if line is in comment block
        if is_in_comment_block(lines, i):
            continue
            
        # Skip if line itself is a comment
        if is_line_commented(line):
            continue
            
        # Find markdown images ![alt](path)
        md_images = re.findall(r'!\[([^\]]*)\]\(([^)]+)\)', line)
        for alt, path in md_images:
            # Skip if this specific image is in a comment on the same line
            img_text = f'![{alt}]({path})'
            if not is_image_in_line_comment(line, img_text):
                image_refs.append((path, i + 1, 'markdown'))
        
        # Find HTML images
        html_images = re.findall(r'<img[^>]*src=["\']([^"\']+)["\']', line)
        for path in html_images:
            img_match = re.search(r'<img[^>]*src=["\']' + re.escape(path) + r'["\'][^>]*>', line)
            if img_match and not is_image_in_line_comment(line, img_match.group(0)):
                image_refs.append((path, i + 1, 'html'))
    
    return image_refs

def is_image_in_line_comment(line, img_text):
    """Check if a specific image reference is inside a comment on the same line"""
    # Find all comment blocks in the line
    comment_blocks = []
    
    # HTML comments
    for match in re.finditer(r'<!--.*?-->', line):
        comment_blocks.append((match.start(), match.end()))
    
    # Find position of image text
    img_pos = line.find(img_text)
    if img_pos == -1:
        return False
    
    # Check if image is inside any comment block
    for start, end in comment_blocks:
        if start <= img_pos < end:
            return True
    
    return False

def resolve_image_path(image_path, file_path):
    """Resolve relative image paths to absolute paths"""
    if image_path.startswith('http://') or image_path.startswith('https://'):
        return None  # Skip external URLs
    
    file_dir = os.path.dirname(file_path)
    
    if image_path.startswith('/'):
        # Absolute path from root
        return '.' + image_path
    else:
        # Relative path
        return os.path.join(file_dir, image_path)

def main():
    print("Checking for broken image links in content/ directory...")
    print("(Excluding commented image references)")
    print("=" * 60)
    print()
    
    broken_files = []
    total_files_checked = 0
    total_images_found = 0
    total_broken_images = 0
    
    # Find all content files
    content_files = []
    for pattern in ['**/*.md', '**/*.html', '**/*.mdx']:
        content_files.extend(glob.glob(f'content/{pattern}', recursive=True))
    
    for file_path in sorted(content_files):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            try:
                with open(file_path, 'r', encoding='latin-1') as f:
                    content = f.read()
            except:
                print(f"⚠️  Could not read file: {file_path}")
                continue
        except:
            print(f"⚠️  Could not read file: {file_path}")
            continue
        
        total_files_checked += 1
        image_refs = extract_image_paths(content, file_path)
        
        if not image_refs:
            continue
            
        total_images_found += len(image_refs)
        broken_images = []
        
        for image_path, line_num, ref_type in image_refs:
            resolved_path = resolve_image_path(image_path, file_path)
            if resolved_path and not os.path.exists(resolved_path):
                broken_images.append((image_path, resolved_path, line_num, ref_type))
        
        if broken_images:
            broken_files.append(file_path)
            total_broken_images += len(broken_images)
            
            print(f"🔍 BROKEN LINKS IN: {file_path}")
            print("-" * 50)
            
            for img_path, resolved_path, line_num, ref_type in broken_images:
                print(f"  ❌ Line {line_num} ({ref_type}): {img_path}")
                print(f"     Expected at: {resolved_path}")
            print()
    
    # Summary
    print("📊 SUMMARY")
    print("=" * 30)
    print(f"Files checked: {total_files_checked}")
    print(f"Total image references found: {total_images_found}")
    print(f"Files with broken links: {len(broken_files)}")
    print(f"Total broken image links: {total_broken_images}")
    
    if broken_files:
        print(f"\n📝 FILES NEEDING ATTENTION:")
        for file_path in broken_files:
            print(f"  • {file_path}")

if __name__ == "__main__":
    main()
