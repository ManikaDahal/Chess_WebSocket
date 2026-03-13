import requests
import sys

# REPLACE with your actual Login API endpoint URL
LOGIN_URL = "https://chess-backend-ochre.vercel.app/api/token/"

# The username you want to demo lockout on
TARGET_USERNAME = "Sabina"
INCORRECT_PASSWORD = "wrong_password123"

print(f"===========================================================")
print(f"STARTING DJANGO AXES DEMO: {LOGIN_URL}")
print(f"===========================================================\n")

# Attempt 10 failed consecutive logins to trigger Axes lockout
# Check your settings.AXES_FAILURE_LIMIT (usually 3)
for i in range(1, 11):
    print(f"Attempt {i:02d}: Logging in as '{TARGET_USERNAME}' with INCORRECT password...")
    
    payload = {
        "username": TARGET_USERNAME,
        "password": INCORRECT_PASSWORD
    }
    
    try:
        response = requests.post(LOGIN_URL, json=payload)
        
        status_code = response.status_code
        response_text = response.text
        
        if status_code == 403 or "locked out" in response_text.lower():
            print(f"\n[SUCCESS] DJANGO AXES LOCKOUT TRIGGERED!")
            print(f"Status: {status_code}")
            print(f"User '{TARGET_USERNAME}' or IP is now locked out due to too many failed attempts.")
            print(f"Axes response: {response_text}")
            sys.exit(0)
            
        elif status_code == 429:
            print(f"   [INFO] DRF Global IP Throttle kicked in (Status 429).")
            print(f"     Axes is still counting these failures, but DRF intercepted the response.")
            print(f"     Continuing to see if Axes lockout triggers next...\n")
            
        else:
            print(f"   Still allowing attempts. Status: {status_code} | Response: {response_text[:30]}...\n")
             
    except requests.exceptions.RequestException as e:
        print(f"\n[ERROR] Connection error: {e}")
        sys.exit(1)

print("\nDemo script finished. Looked like Axes lockout did not trigger after 10 attempts.")
print("Check your settings.AXES_FAILURE_LIMIT or if Axes is enabled.")
