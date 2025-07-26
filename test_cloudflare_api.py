#!/usr/bin/env python3
"""
Test script to verify Cloudflare API connectivity and account ID
"""

import requests
import os

def test_api():
    """Test Cloudflare API connectivity"""
    
    # Cloudflare API details
    account_id = "44aaa2fa622a6206bffc812de90c4b52"
    api_token = os.environ.get('CLOUDFLARE_API_TOKEN')
    
    if not api_token:
        print("❌ CLOUDFLARE_API_TOKEN environment variable not set")
        return False
    
    # Test 1: List images endpoint
    print("🔍 Testing Cloudflare Images API...")
    
    headers = {
        'Authorization': f'Bearer {api_token}',
        'Content-Type': 'application/json'
    }
    
    # Test the list images endpoint
    list_url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/images/v1"
    
    try:
        response = requests.get(list_url, headers=headers)
        print(f"List images response: {response.status_code}")
        print(f"Response: {response.text[:500]}")
        
        if response.status_code == 200:
            print("✅ API connection successful!")
            result = response.json()
            if 'result' in result and 'images' in result['result']:
                print(f"Found {len(result['result']['images'])} existing images")
            return True
        else:
            print(f"❌ API test failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing API: {e}")
        return False

if __name__ == "__main__":
    test_api()
