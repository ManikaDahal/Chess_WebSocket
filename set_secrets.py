import os
import subprocess
import json

def parse_env(file_path):
    secrets = {}
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    current_key = None
    current_val = []
    
    for line in lines:
        line_stripped = line.strip()
        if not current_key and (not line_stripped or line_stripped.startswith('#')):
            continue
            
        if current_key:
            current_val.append(line.strip('\n'))
            if line_stripped == '}':
                secrets[current_key] = '\n'.join(current_val)
                current_key = None
                current_val = []
        elif '=' in line:
            key, val = line.split('=', 1)
            key = key.strip()
            if val.strip() == '{' or val.startswith('{'):
                current_key = key
                current_val = [val.strip('\n')]
            else:
                secrets[key] = val.strip()
    return secrets

secrets = parse_env('.env')
cmd = [r"C:\Users\User\.fly\bin\flyctl.exe", "secrets", "set"]
for k, v in secrets.items():
    cmd.append(f"{k}={v}")

print("Setting secrets...")
subprocess.run(cmd)
print("Done")
