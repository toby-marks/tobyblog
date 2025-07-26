#!/usr/bin/env python3
"""
Script to compress large images and upload them to Cloudflare Images
"""

import requests
import os
import json
import time
from PIL import Image, ImageOps
import io

# List of missing images
missing_images = [
    "static/images/20250531-2025-road-trip-day-2/54660766882_63fc56859e_o.jpg",
    "static/images/20250531-2025-road-trip-day-2/54661839689_bbe362a4cb_o.jpg", 
    "static/images/20250531-2025-road-trip-day-2/54661933605_4406cd05cd_o.jpg",
    "static/images/20250531-2025-road-trip-day-2/54661827968_f8e0157059_o.jpg",
    "static/images/20250531-2025-road-trip-day-2/54661839684_836d6627f5_o.jpg",
    "static/images/20250531-2025-road-trip-day-2/54661607286_17ae73bb62_o.jpg"
]

def compress_image(image_path, max_size_mb=19):
    """Compress an image to be under the specified size limit"""
    max_size_bytes = max_size_mb * 1024 * 1024
    
    print(f"📸 Compressing {image_path}...")
    
    try:
        # Open and auto-orient the image
        with Image.open(image_path) as img:
            # Apply EXIF orientation
            img = ImageOps.exif_transpose(img)
            
            # Convert to RGB if necessary (for JPEG)
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')
            
            # Start with original dimensions
            original_size = os.path.getsize(image_path)
            print(f"   Original size: {original_size:,} bytes")
            
            # If original is already under limit, return as-is
            if original_size <= max_size_bytes:
                print(f"   ✅ Already under {max_size_mb}MB limit")
                return image_path
            
            # Try different compression levels
            for quality in [95, 90, 85, 80, 75, 70, 65, 60]:
                # Create compressed image in memory
                output = io.BytesIO()
                img.save(output, format='JPEG', quality=quality, optimize=True)
                compressed_size = output.tell()
                
                print(f"   Quality {quality}: {compressed_size:,} bytes")
                
                if compressed_size <= max_size_bytes:
                    # Save compressed version
                    compressed_path = image_path.replace('.jpg', '_compressed.jpg')
                    with open(compressed_path, 'wb') as f:
                        f.write(output.getvalue())
                    
                    print(f"   ✅ Compressed to {compressed_size:,} bytes (quality {quality})")
                    return compressed_path
            
            # If still too large, try resizing
            print(f"   🔄 Still too large, trying to resize...")
            
            for scale in [0.9, 0.8, 0.7, 0.6, 0.5]:
                new_width = int(img.width * scale)
                new_height = int(img.height * scale)
                resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # Try with 85% quality after resizing
                output = io.BytesIO()
                resized_img.save(output, format='JPEG', quality=85, optimize=True)
                compressed_size = output.tell()
                
                print(f"   Scale {scale} ({new_width}x{new_height}): {compressed_size:,} bytes")
                
                if compressed_size <= max_size_bytes:
                    # Save resized and compressed version
                    compressed_path = image_path.replace('.jpg', '_compressed.jpg')
                    with open(compressed_path, 'wb') as f:
                        f.write(output.getvalue())
                    
                    print(f"   ✅ Resized and compressed to {compressed_size:,} bytes")
                    return compressed_path
            
            print(f"   ❌ Could not compress {image_path} to under {max_size_mb}MB")
            return None
            
    except Exception as e:
        print(f"   ❌ Error compressing {image_path}: {e}")
        return None

def upload_to_cloudflare(image_path, max_retries=3):
    """Upload an image to Cloudflare Images with retry logic"""
    
    # Cloudflare API details
    account_id = "44aaa2fa622a6206bffc812de90c4b52"
    api_token = os.environ.get('CLOUDFLARE_API_TOKEN')
    
    if not api_token:
        print("❌ CLOUDFLARE_API_TOKEN environment variable not set")
        return None
    
    # Generate Cloudflare ID from the original local path (not compressed version)
    original_path = image_path.replace('_compressed.jpg', '.jpg')
    relative_path = original_path.replace('static/', '')
    cloudflare_id = f"tobyblog_{relative_path.replace('/', '_').replace('-', '_')}"
    
    # Clean up the cloudflare_id (remove any invalid characters)
    cloudflare_id = ''.join(c for c in cloudflare_id if c.isalnum() or c in ['_', '-'])
    
    url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/images/v1"
    
    headers = {
        'Authorization': f'Bearer {api_token}',
    }
    
    for attempt in range(max_retries):
        try:
            file_size = os.path.getsize(image_path)
            print(f"🔄 Uploading {image_path} ({file_size:,} bytes) (attempt {attempt + 1}/{max_retries})")
            print(f"   Cloudflare ID: {cloudflare_id}")
            
            with open(image_path, 'rb') as f:
                files = {
                    'file': f,
                    'id': (None, cloudflare_id)
                }
                response = requests.post(url, headers=headers, files=files, timeout=120)
            
            print(f"   Response: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    cloudflare_url = f"https://imagedelivery.net/{account_id}/{cloudflare_id}/public"
                    print(f"✅ Uploaded: {image_path}")
                    print(f"   URL: {cloudflare_url}")
                    return cloudflare_id, cloudflare_url, original_path
                else:
                    print(f"❌ Upload failed (success=false): {result}")
            elif response.status_code == 409:
                # Image already exists
                print(f"ℹ️  Image already exists: {image_path}")
                cloudflare_url = f"https://imagedelivery.net/{account_id}/{cloudflare_id}/public"
                return cloudflare_id, cloudflare_url, original_path
            else:
                print(f"❌ Upload failed: {response.status_code} - {response.text[:200]}...")
                
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

def cleanup_compressed_files():
    """Clean up temporary compressed files"""
    for image_path in missing_images:
        compressed_path = image_path.replace('.jpg', '_compressed.jpg')
        if os.path.exists(compressed_path):
            try:
                os.remove(compressed_path)
                print(f"🗑️  Removed temporary file: {compressed_path}")
            except Exception as e:
                print(f"❌ Error removing {compressed_path}: {e}")

def main():
    print("🚀 Compressing and uploading missing road trip images to Cloudflare...")
    
    # Check if PIL is available
    try:
        from PIL import Image
    except ImportError:
        print("❌ PIL (Pillow) is required for image compression. Install with: pip install Pillow")
        return
    
    # Test API connectivity first
    if not test_api_first():
        print("❌ API test failed. Please check your API token and account ID.")
        return
    
    new_uploads = []
    compressed_files = []
    
    for image_path in missing_images:
        if os.path.exists(image_path):
            file_size = os.path.getsize(image_path)
            print(f"\n📁 Processing: {image_path} ({file_size:,} bytes)")
            
            # Compress the image if needed
            compressed_path = compress_image(image_path)
            if compressed_path:
                if compressed_path != image_path:
                    compressed_files.append(compressed_path)
                
                # Upload the compressed image
                result = upload_to_cloudflare(compressed_path)
                if result:
                    cloudflare_id, cloudflare_url, original_path = result
                    new_uploads.append((original_path, cloudflare_id, cloudflare_url))
            else:
                print(f"❌ Could not compress {image_path} to acceptable size")
        else:
            print(f"❌ File not found: {image_path}")
    
    if new_uploads:
        update_mapping_file(new_uploads)
        print(f"\n✅ Successfully uploaded {len(new_uploads)} images!")
    else:
        print("\n❌ No images were uploaded successfully")
    
    # Clean up temporary compressed files
    if compressed_files:
        print(f"\n🧹 Cleaning up {len(compressed_files)} temporary compressed files...")
        cleanup_compressed_files()

if __name__ == "__main__":
    main()
