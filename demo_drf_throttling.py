import requests
import time
import sys

# REPLACE with your actual throttled endpoint URL (e.g., your Vercel or localhost API)
API_URL = "https://chess-backend-ochre.vercel.app/api/captcha/" 

print(f"===========================================================")
print(f"🎬 STARTING DRF THROTTLING DEMO: {API_URL}")
print(f"===========================================================\n")

# We will send 15 rapid requests to trigger the throttle limit
for i in range(1, 16):
    try:
        response = requests.get(API_URL)
        status_code = response.status_code
        response_text = response.text[:60] # Just the first 60 chars
        
        if status_code == 200:
            print(f"✅ Request {i:02d} | Status: 200 | SUCCESS")
        elif status_code == 429:
            print(f"\n🚨 THROTTLING KICKED IN! (Status 429 Too Many Requests) 🚨")
            print(f"DRF message: {response_text}")
            print(f"DRF is successfully limiting the rate of requests per IP.")
            print(f"Demo successful! Throttling is active on this endpoint.")
            sys.exit(0)
        else:
            print(f"⚠️ Request {i:02d} | Status: {status_code} | {response_text}")
            
        time.sleep(0.1) 
        
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Connection error: {e}")
        sys.exit(1)

print("\nFinished sending 15 requests. Rate limit was NOT reached.")
print("Note: The server might have higher limits or a different throttle policy.")
