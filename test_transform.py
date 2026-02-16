import re

urls = [
    "https://res.cloudinary.com/drxgymnwa/video/upload/v1739343729/oh9kzscvfpvgraukklhx.mp4", # Apple
    "https://res.cloudinary.com/drxgymnwa/video/upload/v1739343753/u2is0yit8aumshmshnve.mp4", # NASA
    "https://res.cloudinary.com/drxgymnwa/video/upload/q_auto,vc_h264:main:3.1/oh9kzscvfpvgraukklhx.mp4", # Broken Main 3.1
    "https://res.cloudinary.com/drxgymnwa/video/upload/f_auto,q_auto/v1/test.mp4" # Generic
]

def harden(url):
    if 'res.cloudinary.com' not in url or '/video/upload/' not in url:
        return url
    
    safe_profile = 'q_auto,vc_h264:baseline:3.0,br_1m'
    
    # Split by /video/upload/
    base, rest = url.split('/video/upload/', 1)
    
    # The 'rest' part looks like: [transformations/] [v1234/] public_id.mp4
    parts = [p for p in rest.split('/') if p]
    
    new_parts = [safe_profile]
    
    # Check if any part (except the last one) is a version number
    version = None
    for p in parts[:-1]:
        if p.startswith('v') and p[1:].isdigit():
            version = p
            break
            
    if version:
        new_parts.append(version)
    
    # Always append the actual filename/public_id (last part)
    new_parts.append(parts[-1])
        
    return f"{base}/video/upload/{'/'.join(new_parts)}"

for u in urls:
    print(f"Original: {u}")
    print(f"Hardened: {harden(u)}")
    print("-" * 20)
