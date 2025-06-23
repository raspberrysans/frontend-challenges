<!-- @format -->

# M4A to SRT Converter - Render Deployment Guide

This guide will help you deploy the M4A to SRT converter on Render.

## Prerequisites

- A Render account
- Your code pushed to a Git repository (GitHub, GitLab, etc.)

## Deployment Steps

### Option 1: Using render.yaml (Recommended)

1. **Connect your repository to Render:**

   - Go to [Render Dashboard](https://dashboard.render.com)
   - Click "New +" and select "Web Service"
   - Connect your Git repository
   - Render will automatically detect the `render.yaml` file

2. **Automatic deployment:**
   - Render will use the configuration from `render.yaml`
   - The build script will run automatically
   - Your service will be deployed with the name "m4a-to-srt-converter"

### Option 2: Manual Configuration

1. **Create a new Web Service:**

   - Go to [Render Dashboard](https://dashboard.render.com)
   - Click "New +" and select "Web Service"
   - Connect your Git repository

2. **Configure the service:**

   - **Name:** `m4a-to-srt-converter` (or your preferred name)
   - **Environment:** `Python 3`
   - **Build Command:** `chmod +x build.sh && ./build.sh`
   - **Start Command:** `gunicorn --bind 0.0.0.0:$PORT --timeout 3600 --workers 1 --worker-class sync --max-requests 10 app:app`
   - **Health Check Path:** `/health`

3. **Environment Variables:**
   - `PYTHON_VERSION`: `3.9.16`
   - `PORT`: `10000` (Render will override this automatically)

## Build Script Details

The `build.sh` script performs the following:

1. **System Dependencies:**

   - Installs Python development tools
   - Installs audio processing libraries (portaudio, libasound2)
   - Installs FFmpeg and related codecs
   - Installs build tools

2. **Python Dependencies:**

   - Upgrades pip
   - Installs packages from `requirements.txt`

3. **Verification:**
   - Verifies FFmpeg installation
   - Tests application imports
   - Creates necessary directories

## API Endpoints

Once deployed, your service will have these endpoints:

- `GET /` - Main page
- `GET /health` - Health check
- `POST /upload` - Upload M4A file for conversion
- `GET /status/<job_id>` - Check conversion status
- `GET /download/<job_id>` - Download converted SRT file

## Usage Example

```bash
# Upload a file
curl -X POST -F "file=@audio.m4a" https://your-app-name.onrender.com/upload

# Check status
curl https://your-app-name.onrender.com/status/job_id_here

# Download result
curl https://your-app-name.onrender.com/download/job_id_here
```

## Troubleshooting

### Common Issues

1. **Build fails with FFmpeg errors:**

   - The build script includes comprehensive FFmpeg dependencies
   - Check the build logs for specific error messages

2. **Audio processing fails:**

   - Ensure your M4A files are valid
   - Check that the file size is reasonable (under 50MB recommended)

3. **Service times out:**
   - The gunicorn configuration includes a 3600-second timeout
   - For very long audio files, consider splitting them

### Logs

- Check the Render dashboard for build and runtime logs
- The application logs processing progress to stdout

## Performance Considerations

- **Memory:** Audio processing can be memory-intensive
- **CPU:** Speech recognition is CPU-intensive
- **Timeout:** Long audio files may hit timeout limits
- **Concurrent requests:** Limited to 1 worker for stability

## Security Notes

- Files are stored temporarily and cleaned up automatically
- No persistent storage is used
- CORS is enabled for web access
- File uploads are validated for M4A format

## Support

If you encounter issues:

1. Check the Render build logs
2. Verify your M4A files are valid
3. Ensure your repository contains all necessary files
4. Check that the build script has execute permissions
