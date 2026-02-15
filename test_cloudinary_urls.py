import requests

videos = {
    "Apple": "oh9kzscvfpvgraukklhx",
    "Museum": "jnkib8glyyallraylzmz"
}
profile = "q_auto,vc_h264:main:3.1"

def check_video(name, public_id):
    url = f"https://res.cloudinary.com/drxgymnwa/video/upload/{profile}/{public_id}.mp4"
    print(f"\nChecking {name}: {url}")
    try:
        r = requests.get(url, timeout=10, stream=True)
        print(f"Status: {r.status_code}")
        if r.status_code == 200:
            print(f"Content-Type: {r.headers.get('Content-Type')}")
            print(f"Content-Length: {r.headers.get('Content-Length')}")
            # Try to read a bit of content to ensure it's not a 200 Error Page
            chunk = next(r.iter_content(chunk_size=1024))
            print(f"Sample data received: {len(chunk)} bytes")
        else:
            print(f"Reason: {r.reason}")
    except Exception as e:
        print(f"Error: {e}")

for name, public_id in videos.items():
    check_video(name, public_id)
