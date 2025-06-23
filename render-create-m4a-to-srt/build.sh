#!/bin/bash
# Build script for Render deployment
# This script sets up the environment for the M4A to SRT converter

set -e  # Exit on any error

echo "🚀 Starting build process for M4A to SRT Converter..."

# Update package lists
echo "📦 Updating package lists..."
apt-get update -qq

# Install system dependencies
echo "🔧 Installing system dependencies..."
apt-get install -y -qq \
    python3-dev \
    python3-pip \
    build-essential \
    libasound2-dev \
    portaudio19-dev \
    libportaudio2 \
    libportaudiocpp0 \
    ffmpeg \
    libavcodec-extra \
    libavformat-dev \
    libavutil-dev \
    libswresample-dev \
    libswscale-dev \
    pkg-config

# Verify FFmpeg installation
echo "🎬 Verifying FFmpeg installation..."
ffmpeg -version | head -n 1
ffprobe -version | head -n 1

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

echo "✅ Build completed successfully!"
echo "🎉 Your M4A to SRT converter is ready for deployment!"