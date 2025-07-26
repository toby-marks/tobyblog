#!/usr/bin/env python3

import os
import boto3
import json
import glob
import time
from pathlib import Path
from botocore.config import Config

# Cloudflare R2 configuration
# You'll need to set these environment variables:
# export CLOUDFLARE_R2_ACCESS_KEY_ID="your_access_key"
# export CLOUDFLARE_R2_SECRET_ACCESS_KEY="your_secret_key"
# export CLOUDFLARE_R2_BUCKET_NAME="your_bucket_name"
# export CLOUDFLARE_R2_ACCOUNT_ID="your_account_id"
# export CLOUDFLARE_R2_CUSTOM_DOMAIN="your_custom_domain"  # Optional

R2_ACCESS_KEY_ID = os.getenv('CLOUDFLARE_R2_ACCESS_KEY_ID')
R2_SECRET_ACCESS_KEY = os.getenv('CLOUDFLARE_R2_SECRET_ACCESS_KEY')
R2_BUCKET_NAME = os.getenv('CLOUDFLARE_R2_BUCKET_NAME')
R2_ACCOUNT_ID = os.getenv('CLOUDFLARE_R2_ACCOUNT_ID')
R2_CUSTOM_DOMAIN = os.getenv('CLOUDFLARE_R2_CUSTOM_DOMAIN')

if not all([R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_BUCKET_NAME, R2_ACCOUNT_ID]):
    print("Error: Please set the required Cloudflare R2 environment variables")
    print("Required:")
    print("export CLOUDFLARE_R2_ACCESS_KEY_ID='your_access_key'")
    print("export CLOUDFLARE_R2_SECRET_ACCESS_KEY='your_secret_key'")
    print("export CLOUDFLARE_R2_BUCKET_NAME='your_bucket_name'")
    print("export CLOUDFLARE_R2_ACCOUNT_ID='your_account_id'")
    print("Optional:")
    print("export CLOUDFLARE_R2_CUSTOM_DOMAIN='your_custom_domain'")
    exit(1)

# Cloudflare R2 endpoint
R2_ENDPOINT = f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com"

def get_s3_client():
    """Get S3 client configured for Cloudflare R2"""
    return boto3.client(
        's3',
        endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_ACCESS_KEY_ID,
        aws_secret_access_key=R2_SECRET_ACCESS_KEY,
        config=Config(signature_version='v4'),
        region_name='auto'
    )

def get_content_type(file_path):
    """Get content type based on file extension"""
    ext = os.path.splitext(file_path)[1].lower()
    content_types = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.webp': 'image/webp',
        '.svg': 'image/svg+xml',
        '.ico': 'image/x-icon'
    }
    return content_types.get(ext, 'application/octet-stream')

def upload_image_to_r2(s3_client, file_path, s3_key):
    """Upload an image to Cloudflare R2"""
    try:
        content_type = get_content_type(file_path)
        
        # Upload with public-read ACL for direct access
        s3_client.upload_file(
            file_path,
            R2_BUCKET_NAME,
            s3_key,
            ExtraArgs={
                'ContentType': content_type,
                'CacheControl': 'public, max-age=31536000'  # 1 year cache
            }
        )
        
        # Generate the public URL
        if R2_CUSTOM_DOMAIN:
            public_url = f"https://{R2_CUSTOM_DOMAIN}/{s3_key}"
        else:
            public_url = f"https://{R2_BUCKET_NAME}.{R2_ACCOUNT_ID}.r2.cloudflarestorage.com/{s3_key}"
        
        return public_url
    except Exception as e:
        print(f"Error uploading {file_path}: {e}")
        return None

def create_upload_mapping():
    """Create a mapping of local files to R2 URLs"""
    mapping_file = "cloudflare_r2_mapping.json"
    
    if os.path.exists(mapping_file):
        with open(mapping_file, 'r') as f:
            return json.load(f)
    
    return {}

def save_upload_mapping(mapping):
    """Save the mapping to file"""
    with open("cloudflare_r2_mapping.json", 'w') as f:
        json.dump(mapping, f, indent=2)

def upload_all_images():
    """Upload all images in static/images to Cloudflare R2"""
    s3_client = get_s3_client()
    mapping = create_upload_mapping()
    
    # Find all image files
    image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.gif', '*.webp', '*.svg', '*.ico']
    image_files = []
    
    for ext in image_extensions:
        image_files.extend(glob.glob(f"static/images/**/{ext}", recursive=True))
        image_files.extend(glob.glob(f"static/images/**/{ext.upper()}", recursive=True))
    
    print(f"Found {len(image_files)} images to upload")
    
    uploaded = 0
    skipped = 0
    failed = 0
    
    for file_path in image_files:
        # Create relative path for the key
        rel_path = os.path.relpath(file_path, "static")
        s3_key = rel_path  # Use the same path structure in R2
        
        # Check if already uploaded
        if rel_path in mapping:
            print(f"Skipping {rel_path} (already uploaded)")
            skipped += 1
            continue
        
        print(f"Uploading {rel_path}...")
        
        # Upload to Cloudflare R2
        public_url = upload_image_to_r2(s3_client, file_path, s3_key)
        
        if public_url:
            # Store the mapping
            mapping[rel_path] = {
                's3_key': s3_key,
                'public_url': public_url,
                'local_path': rel_path
            }
            
            uploaded += 1
            print(f"  ✓ Uploaded: {public_url}")
            
            # Save mapping periodically
            if uploaded % 50 == 0:  # R2 can handle more uploads per second
                save_upload_mapping(mapping)
                print(f"Progress: {uploaded} uploaded, {skipped} skipped, {failed} failed")
        else:
            failed += 1
            print(f"  ✗ Failed to upload {rel_path}")
        
        # Rate limiting (R2 is more generous than Images API)
        time.sleep(0.01)
    
    # Final save
    save_upload_mapping(mapping)
    
    print(f"\nUpload Summary:")
    print(f"Uploaded: {uploaded}")
    print(f"Skipped: {skipped}")
    print(f"Failed: {failed}")
    print(f"Total: {len(image_files)}")

def update_content_links():
    """Update content files to use Cloudflare R2 URLs"""
    # Load the mapping
    if not os.path.exists("cloudflare_r2_mapping.json"):
        print("No mapping file found. Run upload first.")
        return
    
    with open("cloudflare_r2_mapping.json", 'r') as f:
        mapping = json.load(f)
    
    # Find all markdown files
    content_files = glob.glob("content/**/*.md", recursive=True)
    
    total_updates = 0
    files_updated = 0
    
    for filepath in content_files:
        print(f"Processing: {filepath}")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        updates_made = 0
        
        # Replace local image paths with R2 URLs
        for local_path, r2_info in mapping.items():
            local_url = f"/{local_path}"
            r2_url = r2_info['public_url']
            
            if local_url in content:
                content = content.replace(local_url, r2_url)
                updates_made += 1
                print(f"  Updated: {local_path} -> {r2_url}")
        
        # Write back if changes were made
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  ✓ {updates_made} updates saved to {filepath}")
            files_updated += 1
            total_updates += updates_made
        else:
            print(f"  No changes needed for {filepath}")
    
    print(f"\nUpdate Summary:")
    print(f"Files processed: {len(content_files)}")
    print(f"Files updated: {files_updated}")
    print(f"Total link updates: {total_updates}")

def setup_bucket():
    """Set up the R2 bucket for public access"""
    s3_client = get_s3_client()
    
    try:
        # Check if bucket exists
        s3_client.head_bucket(Bucket=R2_BUCKET_NAME)
        print(f"Bucket {R2_BUCKET_NAME} already exists")
    except:
        try:
            # Create bucket
            s3_client.create_bucket(Bucket=R2_BUCKET_NAME)
            print(f"Created bucket {R2_BUCKET_NAME}")
        except Exception as e:
            print(f"Error creating bucket: {e}")
            return False
    
    # Set public read policy for images
    bucket_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "PublicReadGetObject",
                "Effect": "Allow",
                "Principal": "*",
                "Action": "s3:GetObject",
                "Resource": f"arn:aws:s3:::{R2_BUCKET_NAME}/images/*"
            }
        ]
    }
    
    try:
        s3_client.put_bucket_policy(
            Bucket=R2_BUCKET_NAME,
            Policy=json.dumps(bucket_policy)
        )
        print("Set bucket policy for public read access")
    except Exception as e:
        print(f"Warning: Could not set bucket policy: {e}")
    
    return True

def main():
    import sys
    
    if len(sys.argv) != 2:
        print("Usage:")
        print("  python upload_to_cloudflare_r2.py setup     # Setup R2 bucket")
        print("  python upload_to_cloudflare_r2.py upload    # Upload images")
        print("  python upload_to_cloudflare_r2.py update    # Update content links")
        print("  python upload_to_cloudflare_r2.py both      # Upload and update")
        return
    
    command = sys.argv[1]
    
    if command == "setup":
        setup_bucket()
    elif command == "upload":
        upload_all_images()
    elif command == "update":
        update_content_links()
    elif command == "both":
        upload_all_images()
        update_content_links()
    else:
        print("Invalid command. Use 'setup', 'upload', 'update', or 'both'")

if __name__ == "__main__":
    main()
