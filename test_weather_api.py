#!/usr/bin/env python3
"""
Quick test script to verify OpenWeatherMap API key
"""
import sys
import requests

def test_api_key(api_key):
    """Test the API key with a simple weather request"""
    print(f"Testing API key: {api_key[:10]}...{api_key[-4:]}")
    print("-" * 50)
    
    # Test 1: Current weather (simplest endpoint)
    print("\n1. Testing Current Weather API...")
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": "London",
        "appid": api_key,
        "units": "metric"
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ SUCCESS! Weather in {data.get('name')}: {data['weather'][0]['description']}")
            print(f"   Temperature: {data['main']['temp']}°C")
            return True
        else:
            data = response.json()
            print(f"   ❌ ERROR: {data.get('message', 'Unknown error')}")
            if response.status_code == 401:
                print("   This means your API key is invalid or not activated yet.")
            return False
    except Exception as e:
        print(f"   ❌ ERROR: {str(e)}")
        return False
    
    # Test 2: Geocoding API
    print("\n2. Testing Geocoding API...")
    geocode_url = "https://api.openweathermap.org/geo/1.0/direct"
    geocode_params = {
        "q": "London",
        "limit": 1,
        "appid": api_key
    }
    
    try:
        response = requests.get(geocode_url, params=geocode_params, timeout=10)
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                print(f"   ✅ SUCCESS! Found location: {data[0]['name']}, {data[0].get('country', '')}")
                return True
            else:
                print("   ❌ ERROR: No location found")
                return False
        else:
            data = response.json()
            print(f"   ❌ ERROR: {data.get('message', 'Unknown error')}")
            return False
    except Exception as e:
        print(f"   ❌ ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 test_weather_api.py YOUR_API_KEY")
        print("\nExample:")
        print("  python3 test_weather_api.py abc123def456ghi789")
        sys.exit(1)
    
    api_key = sys.argv[1].strip()
    if not api_key:
        print("❌ Error: API key cannot be empty")
        sys.exit(1)
    
    success = test_api_key(api_key)
    
    if not success:
        print("\n" + "=" * 50)
        print("TROUBLESHOOTING:")
        print("1. Make sure your API key is correct (no extra spaces)")
        print("2. Check if your API key is activated at:")
        print("   https://openweathermap.org/api_keys")
        print("3. New API keys may take 10-60 minutes to activate")
        print("4. Make sure you're using the correct API key from your account")
        sys.exit(1)
    else:
        print("\n" + "=" * 50)
        print("✅ Your API key is working! You can now use it in the weather integration.")
        sys.exit(0)

