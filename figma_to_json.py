import requests
import json
import config

FIGMA_TOKEN = config.FIGMA_TOKEN
FILE_KEY = config.FILE_KEY
OUTPUT_FILE = "output.json"

HEADERS = {
    "X-Figma-Token": FIGMA_TOKEN
}

def find_frames(node, frames=None):
    if frames is None:
        frames = []
    if node.get("type") == "FRAME":
        frames.append(node)
    for child in node.get("children", []):
        find_frames(child, frames)
    return frames

def fetch_figma_file(file_key):
    url = f"https://api.figma.com/v1/files/{file_key}"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json()

def main():
    data = fetch_figma_file(FILE_KEY)
    document = data.get("document", {})
    frames = find_frames(document)
    print(f"Found {len(frames)} frames.")
    
    # Save frames as JSON to output file
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(frames, f, indent=2)
    print(f"Frames JSON saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
