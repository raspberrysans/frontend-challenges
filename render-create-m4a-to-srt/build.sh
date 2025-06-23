#!/usr/bin/env bash
# build.sh

set -o errexit  # exit on error

# Install system dependencies
apt-get update
apt-get install -y ffmpeg

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt