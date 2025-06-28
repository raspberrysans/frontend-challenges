<!-- @format -->

# M4A to SRT Converter - Render Deployment

A FastAPI web service for converting M4A audio files to SRT subtitle format using OpenAI Whisper.

## Features

- Convert M4A audio files to SRT subtitles
- Uses OpenAI Whisper for high-quality transcription with word-level timestamps
- Fallback transcription method using audio segmentation
- Customizable subtitle length (max words per subtitle)
- RESTful API with status tracking
- Background processing with job management
- Interactive API documentation (Swagger UI)

## API Endpoints

- `POST /upload` - Upload M4A file for conversion
- `GET /status/{job_id}` - Check processing status
- `GET /download/{job_id}` - Download converted SRT file
- `GET /health` - Service health check
- `GET /docs` - Interactive API documentation

## Deployment on Render

### Prerequisites

- Render account
- Git repository with this code

### Deployment Steps

1. **Create a new Web Service on Render**

   - Connect your Git repository
   - Choose Python as the runtime
   - Set build command: `chmod +x build.sh && ./build.sh`
   - Set start command: `uvicorn app:app --host 0.0.0.0 --port $PORT --timeout-keep-alive 3600`

2. **Environment Variables** (optional)

   - `PORT`: Port number (Render sets this automatically)

3. **Deploy**
   - Render will automatically build and deploy your service
   - The build script will install all dependencies and set up FFmpeg

### Alternative Deployment Methods

#### Option 1: Using Docker (Recommended)

If you encounter read-only filesystem issues, use the provided Dockerfile:

1. **Create a new Web Service on Render**

   - Connect your Git repository
   - Choose **Docker** as the runtime
   - Render will automatically detect and use the `Dockerfile`

2. **Benefits of Docker deployment:**
   - Explicit system dependency installation
   - Consistent environment across deployments
   - No read-only filesystem issues
   - Proper Rust toolchain installation

#### Option 2: Manual System Dependencies

If using Python runtime, ensure these system packages are available:

- `ffmpeg`
- `ffprobe`
- `build-essential`

### Build Process

The `build.sh` script performs the following:

1. Checks for containerized environment
2. Verifies FFmpeg availability
3. Installs Python packages from `requirements.txt`
4. Creates necessary directories
5. Tests application startup

## Troubleshooting

### Common Issues

1. **Rust Compilation Error**

   ```
   error: failed to create directory `/usr/local/cargo/registry/cache/index.crates.io-1949cf8c6b5b557f`
   Caused by: Read-only file system (os error 30)
   ```

   **Solutions:**

   - **Use Docker deployment** (recommended) - includes Rust toolchain
   - **Use fallback app** - `app_fallback.py` works without Whisper
   - **Updated build script** - sets proper environment variables for Rust

2. **Read-only Filesystem Error**

   ```
   E: List directory /var/lib/apt/lists/partial is missing. - Acquire (30: Read-only file system)
   ```

   **Solution:** Use Docker deployment instead of Python runtime, or ensure system packages are pre-installed.

3. **Import Errors**

   - Run `python test_deployment.py` to check all dependencies
   - Ensure all packages in `requirements.txt` are compatible

4. **FFmpeg Not Found**

   - The Dockerfile installs FFmpeg explicitly
   - Check if FFmpeg is in PATH: `which ffmpeg`
   - Use the health check endpoint to verify system status

5. **Whisper Not Working**

   - Whisper requires significant memory and CPU
   - Consider using a larger instance on Render
   - The app falls back to chunk-based transcription if Whisper fails

6. **Audio Processing Fails**
   - Check if audio libraries are installed
   - Verify FFmpeg can process M4A files
   - Check the application logs for detailed error messages

### Deployment Options for Rust Issues

#### Option A: Docker Deployment (Best)

```bash
# Use the provided Dockerfile
# Includes Rust toolchain and all dependencies
```

#### Option B: Fallback App

```bash
# Use app_fallback.py instead of app.py
# Works without Whisper if installation fails
```

#### Option C: Simplified Requirements

```bash
# Use requirements-simple.txt
# Pre-compiled packages only
```

### Testing Locally

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Install FFmpeg:

   ```bash
   # macOS
   brew install ffmpeg

   # Ubuntu/Debian
   sudo apt-get install ffmpeg
   ```

3. Run the test script:

   ```bash
   python test_deployment.py
   ```

4. Start the server:
   ```bash
   python app.py
   ```

### File Size Limits

- Maximum file size: 50MB
- Supported format: M4A only
- Processing time varies with audio length

## Architecture

- **FastAPI**: Modern, fast web framework with automatic API documentation
- **Uvicorn**: ASGI server for production
- **OpenAI Whisper**: Primary transcription engine with word-level timestamps
- **pydub**: Audio processing and format conversion
- **FFmpeg**: Audio format conversion
- **Pydantic**: Data validation and serialization

## Performance Considerations

- Whisper processing is CPU and memory intensive
- Consider using Render's paid tiers for better performance
- Audio files are processed in background tasks
- Temporary files are automatically cleaned up
- Uses async/await for better concurrency

## Security

- File uploads are validated for type and size
- Temporary files are cleaned up after processing
- No persistent storage of uploaded files
- CORS enabled for web client access
- Input validation using Pydantic models

## API Documentation

FastAPI automatically generates interactive API documentation:

- **Swagger UI**: Available at `/docs`
- **ReDoc**: Available at `/redoc`
- **OpenAPI Schema**: Available at `/openapi.json`

## Whisper Configuration

The application uses OpenAI Whisper with the following settings:

- **Model**: `base` (good balance of speed and accuracy)
- **Word Timestamps**: Enabled for precise subtitle timing
- **Output Format**: JSON for detailed transcription data
- **Fallback**: Chunk-based transcription if Whisper fails

## Deployment Status Monitoring

The application includes built-in health checks:

- **Health endpoint**: `/health` - Returns system status and dependency availability
- **Root endpoint**: `/` - Shows dependency status on the landing page
- **Automatic dependency checking**: Validates FFmpeg and Whisper availability at startup

## Files Overview

- `app.py` - Main FastAPI application with Whisper integration
- `app_fallback.py` - Fallback version that works without Whisper
- `requirements.txt` - Main requirements with specific versions
- `requirements-simple.txt` - Simplified requirements (pre-compiled only)
- `Dockerfile` - Docker deployment with Rust toolchain
- `build.sh` - Build script with Rust environment setup
- `render.yaml` - Render deployment configuration
