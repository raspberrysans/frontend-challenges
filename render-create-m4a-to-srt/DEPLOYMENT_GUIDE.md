<!-- @format -->

# Deployment Guide: M4A to SRT Converter

## Overview

You have three versions of the M4A to SRT converter:

1. **`app_working.py`** - Works locally, command-line version
2. **`app.py`** - Full-featured web service with Whisper + SpeechRecognition
3. **`app_simple.py`** - Simplified web service with SpeechRecognition only

## Why `app_working.py` Works Locally But `app.py` Doesn't Deploy

### Key Differences:

1. **Dependencies**: `app_working.py` has fewer dependencies and simpler setup
2. **FFmpeg**: Local machine has FFmpeg installed, production needs explicit setup
3. **Whisper**: Heavy ML library that requires significant resources
4. **Environment**: Local vs production environment differences

### Main Issues with `app.py`:

1. **Complex FFmpeg setup** - Production environments need explicit FFmpeg installation
2. **Whisper dependencies** - Large ML models and dependencies
3. **Resource requirements** - Whisper needs significant CPU/memory
4. **Timeout issues** - Long processing times can cause deployment failures

## Deployment Options

### Option 1: Use `app_simple.py` (Recommended for Production)

**Pros:**

- Fewer dependencies
- Faster deployment
- More reliable
- Lower resource requirements
- Uses only SpeechRecognition (no Whisper)

**Cons:**

- Less accurate transcription than Whisper
- Limited to 50MB files
- Fewer features

**Deployment Steps:**

1. Rename `app_simple.py` to `app.py`
2. Use `requirements_simple.txt` instead of `requirements.txt`
3. Update `Procfile` to use the simplified version

### Option 2: Fix `app.py` (Advanced)

**Pros:**

- Full Whisper functionality
- Better transcription accuracy
- More features

**Cons:**

- Complex setup
- Higher resource requirements
- More potential failure points

**Required Changes:**

1. Use a larger Render instance (paid tier)
2. Ensure all dependencies are properly installed
3. Handle FFmpeg setup correctly
4. Manage timeouts and resource limits

## Step-by-Step Deployment

### For Simplified Version (`app_simple.py`):

1. **Prepare files:**

   ```bash
   # Rename the simplified version
   mv app_simple.py app.py
   mv requirements_simple.txt requirements.txt
   ```

2. **Update Procfile:**

   ```
   web: gunicorn --bind 0.0.0.0:$PORT --timeout 1800 --workers 1 app:app
   ```

3. **Deploy to Render:**
   - Create new Web Service
   - Connect your repository
   - Build command: `./build.sh`
   - Start command: `gunicorn app:app`

### For Full Version (`app.py`):

1. **Use paid Render tier** (at least $7/month)
2. **Update build script** to handle dependencies better
3. **Increase timeouts** in Procfile
4. **Monitor resource usage**

## Testing Deployment

### Before Deploying:

1. **Test locally:**

   ```bash
   python test_deployment.py
   ```

2. **Check dependencies:**

   ```bash
   pip install -r requirements.txt
   python -c "import flask, pydub, speech_recognition; print('All imports successful')"
   ```

3. **Test FFmpeg:**
   ```bash
   ffmpeg -version
   ```

### After Deploying:

1. **Check health endpoint:**

   ```
   GET https://your-app.onrender.com/health
   ```

2. **Test file upload:**
   - Use a small M4A file (< 10MB)
   - Check processing status
   - Download result

## Troubleshooting

### Common Issues:

1. **Import Errors:**

   - Check `requirements.txt` compatibility
   - Ensure all dependencies are listed
   - Use `test_deployment.py` to verify

2. **FFmpeg Issues:**

   - Verify FFmpeg is installed in build script
   - Check PATH configuration
   - Test with `which ffmpeg`

3. **Timeout Issues:**

   - Increase Gunicorn timeout
   - Reduce file size limits
   - Use background processing

4. **Memory Issues:**
   - Upgrade to larger Render instance
   - Reduce chunk processing limits
   - Use simplified version

### Debug Commands:

```bash
# Check what's installed
pip list

# Test FFmpeg
ffmpeg -version

# Test Whisper
whisper --help

# Check environment
echo $PATH
which ffmpeg
which whisper
```

## Recommendations

### For Quick Deployment:

Use `app_simple.py` - it's more reliable and easier to deploy.

### For Best Quality:

Use `app.py` with a paid Render tier and proper resource allocation.

### For Development:

Start with `app_simple.py`, then upgrade to `app.py` once you have a stable deployment.

## File Structure for Deployment

```
render-create-m4a-to-srt/
├── app.py                    # Main application (rename from app_simple.py)
├── requirements.txt          # Dependencies (rename from requirements_simple.txt)
├── build.sh                  # Build script
├── Procfile                  # Process definition
├── test_deployment.py        # Testing script
└── README.md                 # Documentation
```

## Environment Variables

- `PORT`: Set by Render automatically
- `PYTHONPATH`: May need to be set for imports
- `PATH`: Should include FFmpeg location

## Monitoring

- Check Render logs for errors
- Monitor resource usage
- Test endpoints regularly
- Keep track of processing times
