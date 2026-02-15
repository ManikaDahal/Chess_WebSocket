import requests

urls = [
    # Original Egypt (High)
    "https://res.cloudinary.com/drxgymnwa/video/upload/v1770887786/sqs0cwlno65kmxg4nxpy.mp4",
    # Transformed to Baseline 3.0
    "https://res.cloudinary.com/drxgymnwa/video/upload/q_auto,vc_h264:baseline:3.0/v1770887786/sqs0cwlno65kmxg4nxpy.mp4",
    # Transformed to Main 3.1
    "https://res.cloudinary.com/drxgymnwa/video/upload/q_auto,vc_h264:main:3.1/v1770887786/sqs0cwlno65kmxg4nxpy.mp4"
]

def check_url(url):
    print(f"\nChecking: {url}")
    try:
        r = requests.head(url, timeout=10)
        print(f"Status: {r.status_code}")
        print(f"Content-Type: {r.headers.get('Content-Type')}")
        print(f"Content-Length: {r.headers.get('Content-Length')}")
    except Exception as e:
        print(f"Error: {e}")

for url in urls:
    check_url(url)
