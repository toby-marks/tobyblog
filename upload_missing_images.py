#!/usr/bin/env python3
"""
Script to upload missing road trip images to Cloudflare Images
"""

import requests
import os
import json

# List of missing images
missing_images = [
    "static/images/20250531-2025-road-trip-day-2/54660766882_63fc56859e_o.jpg",
    "static/images/20250531-2025-road-trip-day-2/54661839689_bbe362a4cb_o.jpg", 
    "static/images/20250531-2025-road-trip-day-2/54661933605_4406cd05cd_o.jpg",
    "static/images/20250531-2025-road-trip-day-2/54661827968_f8e0157059_o.jpg",
    "static/images/20250531-2025-road-trip-day-2/54661839684_836d6627f5_o.jpg",
    "static/images/20250531-2025-road-trip-day-2/54661607286_17ae73bb62_o.jpg"
]

def upload_to_cloudflare(image_path):
    """Upload an image to Cloudflare Images"""
    
    # Cloudflare API details
    account_id = "44aaa2fa622a6206bffc812de90c4b52"
    api_token = os.environ.get('CLOUDFLARE_API_TOKEN')
    
    if not api_token:
        print("❌ CLOUDFLARE_API_TOKEN environment variable not set")
        return None
    
    # Generate Cloudflare ID from the local path
    relative_path = image_path.replace('static/', '')
    cloudflare_id = f"tobyblog_{relative_path.replace('/', '_').replace('-', '_')}"
    
    url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/images/v1"
    
    headers = {
        'Authorization': f'Bearer {api_token}',
    }
    
    try:
        with open(image_path, 'rb') as f:
            files = {
                'file': f,
                'id': (None, cloudflare_id)
            }
            response = requests.post(url, headers=headers, files=files)
        
        if response.status_code == 200:
            result = response.json()
            cloudflare_url = f"https://imagedelivery.net/{account_id}/{cloudflare_id}/public"
            print(f"✅ Uploaded: {image_path}")
            print(f"   Cloudflare ID: {cloudflare_id}")
            print(f"   URL: {cloudflare_url}")
            return cloudflare_id, cloudflare_url
        else:
            print(f"❌ Failed to upload {image_path}: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error uploading {image_path}: {e}")
        return None

def update_mapping_file(new_uploads):
    """Update the mapping file with new uploads"""
    
    try:
        # Load existing mapping
        with open('cloudflare_image_mapping.json', 'r') as f:
            mapping = json.load(f)
        
        # Add new uploads
        for local_path, cloudflare_id, cloudflare_url in new_uploads:
            # Convert to the format used in mapping
            mapping_key = local_path.replace('static/', '')
            mapping[mapping_key] = {
                "cloudflare_id": cloudflare_id,
                "cloudflare_url": cloudflare_url,
                "local_path": mapping_key
            }
        
        # Save updated mapping
        with open('cloudflare_image_mapping.json', 'w') as f:
            json.dump(mapping, f, indent=2)
        
        print(f"✅ Updated mapping file with {len(new_uploads)} new entries")
        
    except Exception as e:
        print(f"❌ Error updating mapping file: {e}")

def main():
    print("🚀 Uploading missing road trip images to Cloudflare...")
    
    new_uploads = []
    
    for image_path in missing_images:
        if os.path.exists(image_path):
            result = upload_to_cloudflare(image_path)
            if result:
                cloudflare_id, cloudflare_url = result
                new_uploads.append((image_path, cloudflare_id, cloudflare_url))
        else:
            print(f"❌ File not found: {image_path}")
    
    if new_uploads:
        update_mapping_file(new_uploads)
        print(f"\n✅ Successfully uploaded {len(new_uploads)} images!")
    else:
        print("\n❌ No images were uploaded successfully")

if __name__ == "__main__":
    main()
