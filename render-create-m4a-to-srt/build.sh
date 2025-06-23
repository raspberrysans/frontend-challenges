#!/bin/bash
# Minimal build script for Render

# Disable colors and interactive prompts
export DEBIAN_FRONTEND=noninteractive
export NO_COLOR=1
export TERM=dumb

# Install Python packages
python -m pip install --upgrade pip
pip install -r requirements.txt

# Download ffmpeg binary
mkdir -p ~/bin
cd ~/bin

# Download ffmpeg
python3 << 'EOF'
import urllib.request
import tarfile
import os

print("Downloading ffmpeg...")
url = "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz"
urllib.request.urlretrieve(url, "ffmpeg.tar.xz")

print("Extracting ffmpeg...")
with tarfile.open("ffmpeg.tar.xz", "r:xz") as tar:
    # Extract only ffmpeg and ffprobe
    for member in tar.getmembers():
        if member.name.endswith('/ffmpeg') or member.name.endswith('/ffprobe'):
            member.name = os.path.basename(member.name)
            tar.extract(member, ".")

# Make executable
os.chmod("ffmpeg", 0o755)
os.chmod("ffprobe", 0o755)

# Clean up
os.remove("ffmpeg.tar.xz")
print("FFmpeg setup complete!")
EOF