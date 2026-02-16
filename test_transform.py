import re

urls = [
    "https://res.cloudinary.com/drxgymnwa/video/upload/v1739343729/oh9kzscvfpvgraukklhx.mp4", # Apple
    "video/upload/v1739343753/u2is0yit8aumshmshnve.mp4", # Relative
    "https://chess-websocket-dor6.onrender.com/media/video/upload/v1/test.mp4" # Proxied
]

def harden(url):
    if not url or '/video/upload/' not in url:
        return url
    
    safe_profile = 'w_854,h_480,c_limit,q_auto,vc_h264:baseline:3.0,br_1m' # Using 3.0 for test
    cloud_name = "drxgymnwa"
    base_cloud = f"https://res.cloudinary.com/{cloud_name}"
    
    try:
        path_part = url.split('/video/upload/')[-1]
        parts = [p for p in path_part.split('/') if p]
        new_parts = [safe_profile]
        
        version = None
        for p in parts[:-1]:
            if p.startswith('v') and p[1:].isdigit():
                version = p
                break
        
        if version:
            new_parts.append(version)
        
        new_parts.append(parts[-1])
        return f"{base_cloud}/video/upload/{'/'.join(new_parts)}"
    except Exception as e:
        return f"ERROR: {e}"

for u in urls:
    print(f"Original: {u}")
    print(f"Hardened: {harden(u)}")
    print("-" * 20)
