#!/usr/bin/env python3
"""
Simple test script to verify backend is working
"""

import requests
import json

def test_backend():
    backend_url = "http://192.168.20.192:8080/api/status"
    
    print("Testing backend connection...")
    print(f"URL: {backend_url}")
    
    try:
        response = requests.get(backend_url, timeout=5)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Backend is working!")
            print("Response data:")
            print(json.dumps(data, indent=2))
        else:
            print(f"❌ Backend returned error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed - backend is not running or not accessible")
    except requests.exceptions.Timeout:
        print("❌ Connection timeout - backend is not responding")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_backend()
