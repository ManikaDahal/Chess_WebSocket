import os
import requests

def download_file(url, filename):
    print(f"Downloading {filename} from {url}...")
    response = requests.get(url, stream=True)
    response.raise_for_status()
    with open(filename, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    print(f"Finished downloading {filename}")

def main():
    models_dir = os.path.join('media', 'models')
    os.makedirs(models_dir, exist_ok=True)

    files = [
        {
            "url": "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files/kokoro-v0_19.onnx",
            "filename": os.path.join(models_dir, "kokoro-v0_19.onnx")
        },
        {
            "url": "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files/voices.bin",
            "filename": os.path.join(models_dir, "voices.bin")
        }
    ]

    for f in files:
        if not os.path.exists(f["filename"]):
            download_file(f["url"], f["filename"])
        else:
            print(f"{f['filename']} already exists, skipping.")

if __name__ == "__main__":
    main()
