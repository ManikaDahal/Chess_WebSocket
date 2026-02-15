import requests

ids = {
    "Apple": "oh9kzscvfpvgraukklhx",
    "Meat": "uknucyobjbri7yhtsmaa"
}

def check_id(name, public_id):
    url = f"https://res.cloudinary.com/drxgymnwa/video/upload/q_auto,vc_h264:baseline:3.0/{public_id}.mp4"
    print(f"\nChecking {name}: {url}")
    try:
        r = requests.head(url, timeout=10)
        print(f"Status: {r.status_code}")
        print(f"Content-Type: {r.headers.get('Content-Type')}")
        print(f"Content-Length: {r.headers.get('Content-Length')}")
    except Exception as e:
        print(f"Error: {e}")

for name, public_id in ids.items():
    check_id(name, public_id)
