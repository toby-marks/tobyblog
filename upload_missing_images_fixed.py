#!/usr/bin/env python3
"""
Script to upload missing road trip images to Cloudflare Images with improved error handling
"""

import requests
import os
import json
import time

# List of missing images
missing_images = [
    "static/images/20250531-2025-road-trip-day-2/54660766882_63fc56859e_o.jpg",
    "static/images/20250531-2025-road-trip-day-2/54661839689_bbe362a4cb_o.jpg", 
    "static/images/20250531-2025-road-trip-day-2/54661933605_4406cd05cd_o.jpg",
    "static/images/20250531-2025-road-trip-day-2/54661827968_f8e0157059_o.jpg",
    "static/images/20250531-2025-road-trip-day-2/54661839684_836d6627f5_o.jpg",
    "static/images/20250531-2025-road-trip-day-2/54661607286_17ae73bb62_o.jpg"
]

def upload_to_cloudflare(image_path, max_retries=3):
    """Upload an image to Cloudflare Images with retry logic"""
    
    # Cloudflare API details
    account_id = "44aaa2fa622a6206bffc812de90c4b52"
    api_token = os.environ.get('CLOUDFLARE_API_TOKEN')
    
    if not api_token:
        print("❌ CLOUDFLARE_API_TOKEN environment variable not set")
        return None
    
    # Generate Cloudflare ID from the local path
    relative_path = image_path.replace('static/', '')
    cloudflare_id = f"tobyblog_{relative_path.replace('/', '_').replace('-', '_')}"
    
    # Clean up the cloudflare_id (remove any invalid characters)
    cloudflare_id = ''.join(c for c in cloudflare_id if c.isalnum() or c in ['_', '-'])
    
    url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/images/v1"
    
    headers = {
        'Authorization': f'Bearer {api_token}',
    }
    
    for attempt in range(max_retries):
        try:
            print(f"🔄 Uploading {image_path} (attempt {attempt + 1}/{max_retries})")
            print(f"   Cloudflare ID: {cloudflare_id}")
            
            with open(image_path, 'rb') as f:
                files = {
                    'file': f,
                    'id': (None, cloudflare_id)
                }
                response = requests.post(url, headers=headers, files=files, timeout=60)
            
            print(f"   Response: {response.status_code}")
            print(f"   Response text: {response.text[:200]}...")
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    cloudflare_url = f"https://imagedelivery.net/{account_id}/{cloudflare_id}/public"
                    print(f"✅ Uploaded: {image_path}")
                    print(f"   URL: {cloudflare_url}")
                    return cloudflare_id, cloudflare_url
                else:
                    print(f"❌ Upload failed (success=false): {result}")
            elif response.status_code == 409:
                # Image already exists
                print(f"ℹ️  Image already exists: {image_path}")
                cloudflare_url = f"https://imagedelivery.net/{account_id}/{cloudflare_id}/public"
                return cloudflare_id, cloudflare_url
            else:
                print(f"❌ Upload failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"❌ Error uploading {image_path} (attempt {attempt + 1}): {e}")
        
        if attempt < max_retries - 1:
            print(f"   Retrying in 2 seconds...")
            time.sleep(2)
    
    return None

def test_api_first():
    """Test API connectivity before uploading"""
    account_id = "44aaa2fa622a6206bffc812de90c4b52"
    api_token = os.environ.get('CLOUDFLARE_API_TOKEN')
    
    if not api_token:
        print("❌ CLOUDFLARE_API_TOKEN environment variable not set")
        return False
    
    headers = {
        'Authorization': f'Bearer {api_token}',
        'Content-Type': 'application/json'
    }
    
    # Test with a simple GET request first
    list_url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/images/v1"
    
    try:
        print("🔍 Testing API connectivity...")
        response = requests.get(list_url, headers=headers, timeout=30)
        print(f"API test response: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ API connection successful!")
            return True
        else:
            print(f"❌ API test failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing API: {e}")
        return False

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
    
    # Test API connectivity first
    if not test_api_first():
        print("❌ API test failed. Please check your API token and account ID.")
        return
    
    new_uploads = []
    
    for image_path in missing_images:
        if os.path.exists(image_path):
            file_size = os.path.getsize(image_path)
            print(f"\n📁 Processing: {image_path} ({file_size:,} bytes)")
            
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
