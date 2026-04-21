#!/usr/bin/env python3
"""
Validate Disqus URLs and create a mapping for broken ones.
Reads URLs from CSV, checks if they're valid, and maps old URLs to new ones.
"""

import csv
import sys
import time
import re
from pathlib import Path
from urllib.parse import urlparse
import subprocess

def check_url_status(url):
    """Check if a URL returns 200 OK using curl."""
    try:
        result = subprocess.run(
            ['curl', '-sI', '-w', '%{http_code}', '-o', '/dev/null', url],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.stdout.strip()
    except Exception as e:
        print(f"Error checking {url}: {e}", file=sys.stderr)
        return "000"

def extract_slug_from_url(url):
    """Extract the slug from a URL path."""
    parsed = urlparse(url)
    path = parsed.path.strip('/')
    parts = path.split('/')
    if len(parts) >= 2:
        return parts[-1]  # Last part is typically the slug
    return None

def find_content_file(slug, section='posts'):
    """Find a content file matching the slug."""
    content_dir = Path('content') / section
    if not content_dir.exists():
        return None
    
    # Try exact match first
    for ext in ['.md', '.markdown']:
        exact_file = content_dir / f"{slug}{ext}"
        if exact_file.exists():
            return exact_file
    
    # Try pattern matching (e.g., YYYYMMDD-slug.md)
    for file in content_dir.glob('*.md'):
        # Remove date prefix if present
        name = file.stem
        if re.match(r'^\d{8}-', name):
            name = name[9:]  # Remove YYYYMMDD- prefix
        
        if name == slug or name.lower() == slug.lower():
            return file
        
        # Also check if slug is contained in filename
        if slug in name or slug.lower() in name.lower():
            return file
    
    return None

def extract_url_from_frontmatter(file_path):
    """Extract the URL/slug from markdown frontmatter."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Extract frontmatter (TOML format)
        if content.startswith('+++'):
            end = content.find('+++', 3)
            if end > 0:
                frontmatter = content[3:end]
                
                # Look for slug or url
                slug_match = re.search(r'slug\s*=\s*["\']([^"\']+)["\']', frontmatter)
                if slug_match:
                    return slug_match.group(1)
        
        # Fallback: use filename
        return file_path.stem
    except Exception as e:
        print(f"Error reading {file_path}: {e}", file=sys.stderr)
        return None

def main():
    input_csv = Path.home() / 'Downloads' / 'tobyblog-com-2026-04-03T20_56_03.210746-links.csv'
    output_csv = Path.home() / 'Downloads' / 'tobyblog-disqus-url-mapping.csv'
    
    if not input_csv.exists():
        print(f"Error: {input_csv} not found", file=sys.stderr)
        sys.exit(1)
    
    # Read input URLs
    with open(input_csv, 'r') as f:
        urls = [line.strip() for line in f if line.strip()]
    
    print(f"Processing {len(urls)} URLs...")
    
    mappings = []
    valid_count = 0
    invalid_count = 0
    remapped_count = 0
    
    for i, old_url in enumerate(urls, 1):
        if i % 50 == 0:
            print(f"Progress: {i}/{len(urls)}", file=sys.stderr)
            time.sleep(1)  # Be nice to the server
        
        # Check if URL is valid
        status = check_url_status(old_url)
        
        if status == '200':
            # URL is valid, map to itself with /index.html
            new_url = old_url.rstrip('/') + '/index.html'
            mappings.append((old_url, new_url))
            valid_count += 1
            continue
        
        # URL is broken, try to find the correct one
        print(f"Broken URL: {old_url} (status: {status})", file=sys.stderr)
        invalid_count += 1
        
        # Extract slug and section
        parsed = urlparse(old_url)
        path_parts = parsed.path.strip('/').split('/')
        
        if len(path_parts) < 2:
            print(f"  Cannot parse URL structure", file=sys.stderr)
            continue
        
        section = path_parts[0]  # posts, photos, etc.
        slug = path_parts[-1]
        
        # Try to find content file
        content_file = find_content_file(slug, section)
        
        if not content_file:
            print(f"  No matching content file found for slug: {slug}", file=sys.stderr)
            continue
        
        print(f"  Found content file: {content_file}", file=sys.stderr)
        
        # Extract actual slug from frontmatter
        actual_slug = extract_url_from_frontmatter(content_file)
        if not actual_slug:
            actual_slug = content_file.stem
        
        # Construct new URL
        new_url = f"https://tobyblog.com/{section}/{actual_slug}/index.html"
        
        # Validate new URL
        test_url = new_url.replace('/index.html', '/')
        status = check_url_status(test_url)
        
        if status == '200':
            print(f"  Remapped to: {new_url}", file=sys.stderr)
            mappings.append((old_url, new_url))
            remapped_count += 1
        else:
            print(f"  New URL also broken (status: {status}): {test_url}", file=sys.stderr)
    
    # Write output CSV
    with open(output_csv, 'w', newline='') as f:
        writer = csv.writer(f)
        for old, new in mappings:
            writer.writerow([old, new])
    
    print(f"\nSummary:")
    print(f"  Total URLs: {len(urls)}")
    print(f"  Valid URLs: {valid_count}")
    print(f"  Invalid URLs: {invalid_count}")
    print(f"  Successfully remapped: {remapped_count}")
    print(f"  Output written to: {output_csv}")

if __name__ == '__main__':
    main()
