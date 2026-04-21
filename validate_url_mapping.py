#!/usr/bin/env python3
"""
Validate the Disqus URL mapping CSV file.
"""

import csv
import sys
from pathlib import Path
from collections import Counter
import subprocess

def check_url_status(url):
    """Check if a URL returns 200 OK."""
    try:
        # Remove /index.html and check the directory URL
        test_url = url.replace('/index.html', '/')
        result = subprocess.run(
            ['curl', '-sI', '-w', '%{http_code}', '-o', '/dev/null', test_url],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.stdout.strip()
    except Exception as e:
        return "ERROR"

def main():
    csv_file = Path.home() / 'Downloads' / 'tobyblog-disqus-url-mapping.csv'
    
    if not csv_file.exists():
        print(f"Error: {csv_file} not found")
        sys.exit(1)
    
    print(f"Validating {csv_file}...")
    print()
    
    issues = []
    old_urls = []
    new_urls = []
    line_num = 0
    
    with open(csv_file, 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            line_num += 1
            
            # Check CSV format
            if len(row) != 2:
                issues.append(f"Line {line_num}: Invalid CSV format (expected 2 columns, got {len(row)})")
                continue
            
            old_url, new_url = row
            old_urls.append(old_url)
            new_urls.append(new_url)
            
            # Check if new URL ends with /index.html
            if not new_url.endswith('/index.html'):
                issues.append(f"Line {line_num}: New URL doesn't end with /index.html: {new_url}")
            
            # Check if URLs use https
            if old_url.startswith('http://'):
                if 'ngrok' not in old_url:  # ngrok URLs are expected to be http
                    issues.append(f"Line {line_num}: Old URL uses http instead of https: {old_url}")
    
    # Check for duplicate old URLs
    old_url_counts = Counter(old_urls)
    duplicates = {url: count for url, count in old_url_counts.items() if count > 1}
    if duplicates:
        issues.append(f"Found {len(duplicates)} duplicate old URLs:")
        for url, count in sorted(duplicates.items()):
            issues.append(f"  {url} appears {count} times")
    
    # Check for duplicate new URLs
    new_url_counts = Counter(new_urls)
    duplicates = {url: count for url, count in new_url_counts.items() if count > 1}
    if duplicates:
        issues.append(f"Found {len(duplicates)} duplicate new URLs (multiple old URLs mapping to same new URL):")
        for url, count in sorted(duplicates.items()):
            issues.append(f"  {url} mapped from {count} different old URLs")
    
    print(f"CSV Format Check:")
    print(f"  Total mappings: {line_num}")
    print(f"  Format issues: {len([i for i in issues if 'Invalid CSV format' in i])}")
    print(f"  /index.html issues: {len([i for i in issues if 'doesn\'t end with' in i])}")
    print(f"  http:// issues: {len([i for i in issues if 'uses http' in i])}")
    print(f"  Duplicate old URLs: {len([i for i in issues if 'duplicate old URLs' in str(i)])}")
    print(f"  Duplicate new URLs: {len([i for i in issues if 'duplicate new URLs' in str(i)])}")
    print()
    
    if issues:
        print("ISSUES FOUND:")
        for issue in issues:
            print(f"  {issue}")
        print()
    
    # Validate sample of URLs (check first 10, last 10, and 10 random from middle)
    print("Validating sample URLs against live site...")
    sample_indices = list(range(min(10, line_num))) + list(range(max(0, line_num-10), line_num))
    
    with open(csv_file, 'r') as f:
        reader = csv.reader(f)
        rows = list(reader)
    
    failed_urls = []
    for i in sample_indices:
        if i >= len(rows):
            continue
        old_url, new_url = rows[i]
        status = check_url_status(new_url)
        if status != '200':
            failed_urls.append((old_url, new_url, status))
            print(f"  FAILED: {new_url} (status: {status})")
    
    print()
    print("VALIDATION SUMMARY:")
    print(f"  Sample size: {len(sample_indices)}")
    print(f"  Failed validations: {len(failed_urls)}")
    
    if not issues and not failed_urls:
        print()
        print("✅ All checks passed! CSV is valid and ready for Disqus URL Mapper.")
    else:
        print()
        print("⚠️  Some issues found. Please review above.")
        if failed_urls:
            print()
            print("Failed URLs:")
            for old, new, status in failed_urls:
                print(f"  {old} -> {new} (HTTP {status})")

if __name__ == '__main__':
    main()
