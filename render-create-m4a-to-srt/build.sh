#!/bin/bash
# Build script for Render deployment
# This script sets up the environment for the M4A to SRT converter

set -e  # Exit on any error

echo "🚀 Starting build process for M4A to SRT Converter..."

# Check if we're in a containerized environment
if [ -f /.dockerenv ] || [ -f /run/.containerenv ]; then
    echo "📦 Containerized environment detected"
    echo "ℹ️ System packages should be pre-installed by the container"
else
    echo "📦 Non-containerized environment"
    echo "ℹ️ System packages may need to be installed separately"
fi

# Check for FFmpeg (may be pre-installed)
echo "🎬 Checking FFmpeg availability..."
if command -v ffmpeg &> /dev/null; then
    echo "✅ FFmpeg found:"
    ffmpeg -version | head -n 1
else
    echo "⚠️ FFmpeg not found in PATH"
    echo "   This may be installed by the container or available via other means"
fi

if command -v ffprobe &> /dev/null; then
    echo "✅ FFprobe found:"
    ffprobe -version | head -n 1
else
    echo "⚠️ FFprobe not found in PATH"
fi

# Upgrade pip
echo "🐍 Upgrading pip..."
python -m pip install --upgrade pip

# Install Python packages
echo "📚 Installing Python packages..."
pip install -r requirements.txt

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p /tmp/audio_uploads
mkdir -p /tmp/audio_processing

# Set proper permissions
echo "🔐 Setting permissions..."
chmod 755 /tmp/audio_uploads
chmod 755 /tmp/audio_processing

# Test the application
echo "🧪 Testing application startup..."
python -c "import app; print('✅ Application imports successfully')"

# Test Whisper installation
echo "🎤 Testing Whisper installation..."
if command -v whisper &> /dev/null; then
    echo "✅ Whisper CLI found"
    whisper --help | head -n 3
else
    echo "⚠️ Whisper CLI not found, but Python package should be available"
fi

echo "✅ Build completed successfully!"
echo "🎉 Your M4A to SRT converter is ready for deployment!"