#!/usr/bin/env bash
# build.sh - Render build script with proper ffmpeg setup

set -o errexit  # exit on error

echo "Starting build process..."

# Upgrade pip first
pip install --upgrade pip

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Create bin directory for ffmpeg
echo "Setting up ffmpeg..."
mkdir -p $HOME/bin

# Download and install static ffmpeg binary
cd $HOME/bin
wget -q https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz
tar -xf ffmpeg-release-amd64-static.tar.xz --strip-components=1
rm ffmpeg-release-amd64-static.tar.xz

# Make binaries executable
chmod +x ffmpeg ffprobe

# Add to PATH for current session
export PATH="$HOME/bin:$PATH"

# Verify ffmpeg installation
echo "FFmpeg version:"
./ffmpeg -version | head -1

echo "Build completed successfully!"
echo "FFmpeg installed at: $HOME/bin/ffmpeg"