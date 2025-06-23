<!-- @format -->

# M4A to SRT Converter - Render Deployment

A Flask web service for converting M4A audio files to SRT subtitle format using OpenAI Whisper and SpeechRecognition.

## Features

- Convert M4A audio files to SRT subtitles
- Uses OpenAI Whisper for accurate transcription with timestamps
- Fallback to Google Speech Recognition if Whisper fails
- Customizable subtitle length (max words per subtitle)
- RESTful API with status tracking
- Background processing with job management

## API Endpoints

- `POST /upload` - Upload M4A file for conversion
- `GET /status/{job_id}` - Check processing status
- `GET /download/{job_id}` - Download converted SRT file
- `GET /health` - Service health check

## Deployment on Render

### Prerequisites

- Render account
- Git repository with this code

### Deployment Steps

1. **Create a new Web Service on Render**

   - Connect your Git repository
   - Choose Python as the runtime
   - Set build command: `./build.sh`
   - Set start command: `gunicorn app:app`

2. **Environment Variables** (optional)

   - `PORT`: Port number (Render sets this automatically)

3. **Deploy**
   - Render will automatically build and deploy your service
   - The build script will install all dependencies and set up FFmpeg

### Build Process

The `build.sh` script performs the following:

1. Installs system dependencies (FFmpeg, audio libraries)
2. Installs Python packages from `requirements.txt`
3. Downloads and configures FFmpeg binary
4. Runs deployment tests

## Troubleshooting

### Common Issues

1. **Import Errors**

   - Run `python test_deployment.py` to check all dependencies
   - Ensure all packages in `requirements.txt` are compatible

2. **FFmpeg Not Found**

   - The build script installs FFmpeg both via apt and downloads a binary
   - Check if FFmpeg is in PATH: `which ffmpeg`

3. **Whisper Not Working**

   - Whisper requires significant memory and CPU
   - Consider using a larger instance on Render
   - The app falls back to SpeechRecognition if Whisper fails

4. **Audio Processing Fails**
   - Check if PyAudio and audio libraries are installed
   - Verify FFmpeg can process M4A files

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

- Maximum file size: 100MB (Render free tier limit)
- Supported format: M4A only
- Processing time varies with audio length

## Architecture

- **Flask**: Web framework
- **Gunicorn**: WSGI server for production
- **OpenAI Whisper**: Primary transcription engine
- **SpeechRecognition**: Fallback transcription
- **pydub**: Audio processing
- **FFmpeg**: Audio format conversion

## Performance Considerations

- Whisper processing is CPU and memory intensive
- Consider using Render's paid tiers for better performance
- Audio files are processed in background threads
- Temporary files are automatically cleaned up

## Security

- File uploads are validated for type and size
- Temporary files are cleaned up after processing
- No persistent storage of uploaded files
- CORS enabled for web client access
