#!/bin/bash
# Build script for Render deployment

set -e  # Exit on any error

echo "🚀 Starting build process..."

# Disable colors and interactive prompts
export DEBIAN_FRONTEND=noninteractive
export NO_COLOR=1
export TERM=dumb

# Install system dependencies
echo "📦 Installing system dependencies..."
apt-get update -qq
apt-get install -y -qq \
    python3-dev \
    python3-pip \
    build-essential \
    libasound2-dev \
    portaudio19-dev \
    libportaudio2 \
    libportaudiocpp0 \
    ffmpeg

# Install Python packages
echo "🐍 Installing Python packages..."
python -m pip install --upgrade pip
pip install -r requirements.txt

# Download ffmpeg binary as backup
echo "🎬 Setting up FFmpeg..."
mkdir -p ~/bin
cd ~/bin

# Download ffmpeg
python3 << 'EOF'
import urllib.request
import tarfile
import os
import sys

print("Downloading ffmpeg...")
try:
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
except Exception as e:
    print(f"FFmpeg setup failed: {e}")
    sys.exit(1)
EOF

# Test the setup
echo "🧪 Testing setup..."
python test_deployment.py

echo "✅ Build completed successfully!"