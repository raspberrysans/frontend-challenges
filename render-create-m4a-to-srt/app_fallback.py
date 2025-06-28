#!/usr/bin/env python3
"""
M4A to SRT Converter - Fallback Version
FastAPI web service for converting M4A audio files to SRT subtitles
This version works without Whisper if installation fails
"""

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import os
import tempfile
import uuid
from datetime import timedelta
from pydub import AudioSegment
from pydub.silence import split_on_silence
import subprocess
import json
import time
import asyncio
from pathlib import Path

# Check for required system dependencies
def check_dependencies():
    """Check if required system dependencies are available"""
    missing_deps = []
    
    # Check FFmpeg
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        missing_deps.append('ffmpeg')
    
    # Check Whisper CLI (optional)
    whisper_available = False
    try:
        subprocess.run(['whisper', '--help'], capture_output=True, check=True)
        whisper_available = True
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    
    if missing_deps:
        print(f"⚠️ Warning: Missing system dependencies: {', '.join(missing_deps)}")
        print("   The application may not work correctly without these dependencies.")
        return False, whisper_available
    
    return True, whisper_available

# Check dependencies at startup
dependencies_ok, whisper_available = check_dependencies()

app = FastAPI(
    title="M4A to SRT Converter (Fallback)",
    description="Convert M4A audio files to SRT subtitles using available transcription methods",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store processing status and completed files
processing_status: Dict[str, Dict[str, Any]] = {}
completed_files: Dict[str, Dict[str, Any]] = {}

class ConversionRequest(BaseModel):
    max_words: int = 8

class StatusResponse(BaseModel):
    status: str
    progress: Optional[str] = None
    message: Optional[str] = None
    subtitle_count: Optional[int] = None
    duration: Optional[float] = None

class UploadResponse(BaseModel):
    job_id: str
    status: str
    message: str
    file_size_mb: float

class SimpleM4AToSRTConverter:
    def __init__(self, max_words: int = 8):
        self.max_words = max_words
        
    def convert_m4a_to_wav(self, m4a_path: str) -> tuple[str, float]:
        """Convert M4A to WAV for processing"""
        print("Converting M4A to WAV...")
        try:
            audio = AudioSegment.from_file(m4a_path, format="m4a")
            
            # Create temporary WAV file
            temp_wav = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            audio.export(temp_wav.name, format="wav")
            return temp_wav.name, len(audio) / 1000.0
        except Exception as e:
            print(f"Error converting M4A to WAV: {e}")
            raise
    
    def transcribe_audio(self, audio_path: str) -> list[Dict[str, Any]]:
        """Transcribe audio using available methods"""
        print("Transcribing audio...")
        
        # Try Whisper first if available
        if whisper_available:
            try:
                return self.transcribe_with_whisper(audio_path)
            except Exception as e:
                print(f"Whisper transcription failed: {e}")
        
        # Fallback to audio segmentation
        return self.transcribe_audio_fallback(audio_path)
    
    def transcribe_with_whisper(self, audio_path: str) -> list[Dict[str, Any]]:
        """Use OpenAI Whisper for transcription"""
        print("Using Whisper for transcription...")
        
        try:
            temp_dir = tempfile.mkdtemp()
            result = subprocess.run([
                'whisper', audio_path, 
                '--model', 'base',
                '--output_format', 'json',
                '--output_dir', temp_dir
            ], capture_output=True, text=True, check=True)
            
            base_name = Path(audio_path).stem
            json_path = Path(temp_dir) / f"{base_name}.json"
            
            if json_path.exists():
                with open(json_path, 'r', encoding='utf-8') as f:
                    whisper_result = json.load(f)
                
                words_with_timing = []
                for segment in whisper_result.get('segments', []):
                    segment_words = segment['text'].strip().split()
                    if segment_words:
                        word_duration = (segment['end'] - segment['start']) / len(segment_words)
                        for i, word in enumerate(segment_words):
                            words_with_timing.append({
                                'word': word,
                                'start': segment['start'] + (i * word_duration),
                                'end': segment['start'] + ((i + 1) * word_duration)
                            })
                
                # Clean up
                try:
                    json_path.unlink()
                    Path(temp_dir).rmdir()
                except:
                    pass
                
                return words_with_timing
            else:
                raise FileNotFoundError("Whisper output file not found")
                
        except Exception as e:
            print(f"Whisper transcription failed: {e}")
            raise
    
    def transcribe_audio_fallback(self, audio_path: str) -> list[Dict[str, Any]]:
        """Fallback transcription using audio segmentation"""
        print("Using fallback transcription method...")
        
        try:
            # Load audio file
            audio = AudioSegment.from_file(audio_path)
            
            # Split audio on silence to get chunks
            chunks = split_on_silence(
                audio,
                min_silence_len=800,
                silence_thresh=audio.dBFS - 16,
                keep_silence=500
            )
            
            if not chunks:
                chunks = [audio]
            
            words_with_timing = []
            current_time = 0
            
            for i, chunk in enumerate(chunks):
                print(f"Processing chunk {i+1}/{len(chunks)}")
                
                # Limit number of chunks to prevent excessive processing time
                if i > 10:  # Reduced limit for fallback
                    break
                
                chunk_path = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
                chunk.export(chunk_path.name, format="wav")
                
                try:
                    # Use whisper on individual chunks if available
                    if whisper_available:
                        chunk_words = self.transcribe_chunk_with_whisper(chunk_path.name, current_time)
                        words_with_timing.extend(chunk_words)
                    else:
                        # Simple timing based on chunk duration
                        chunk_duration = len(chunk) / 1000.0
                        words_with_timing.append({
                            'word': f"[Audio chunk {i+1}]",
                            'start': current_time,
                            'end': current_time + chunk_duration
                        })
                except Exception as e:
                    print(f"Error processing chunk {i+1}: {e}")
                finally:
                    try:
                        os.unlink(chunk_path.name)
                    except:
                        pass
                    current_time += len(chunk) / 1000.0
            
            return words_with_timing
            
        except Exception as e:
            print(f"Fallback transcription failed: {e}")
            return []
    
    def transcribe_chunk_with_whisper(self, chunk_path: str, offset_time: float) -> list[Dict[str, Any]]:
        """Transcribe a single chunk with Whisper"""
        try:
            temp_dir = tempfile.mkdtemp()
            result = subprocess.run([
                'whisper', chunk_path, 
                '--model', 'tiny',
                '--output_format', 'json',
                '--output_dir', temp_dir
            ], capture_output=True, text=True, check=True)
            
            base_name = Path(chunk_path).stem
            json_path = Path(temp_dir) / f"{base_name}.json"
            
            if json_path.exists():
                with open(json_path, 'r', encoding='utf-8') as f:
                    whisper_result = json.load(f)
                
                words_with_timing = []
                for segment in whisper_result.get('segments', []):
                    segment_words = segment['text'].strip().split()
                    if segment_words:
                        word_duration = (segment['end'] - segment['start']) / len(segment_words)
                        for i, word in enumerate(segment_words):
                            words_with_timing.append({
                                'word': word,
                                'start': offset_time + segment['start'] + (i * word_duration),
                                'end': offset_time + segment['start'] + ((i + 1) * word_duration)
                            })
                
                # Clean up
                try:
                    json_path.unlink()
                    Path(temp_dir).rmdir()
                except:
                    pass
                
                return words_with_timing
            else:
                return []
                
        except Exception as e:
            print(f"Chunk transcription failed: {e}")
            return []
    
    def group_words_into_subtitles(self, words_with_timing: list[Dict[str, Any]]) -> list[Dict[str, Any]]:
        """Group words into subtitles based on max_words parameter"""
        if not words_with_timing:
            return []
        
        subtitles = []
        current_group = []
        
        for word_info in words_with_timing:
            current_group.append(word_info)
            
            # Check if we should create a new subtitle
            if len(current_group) >= self.max_words:
                if current_group:
                    subtitle_text = ' '.join([w['word'] for w in current_group])
                    start_time = current_group[0]['start']
                    end_time = current_group[-1]['end']
                    
                    subtitles.append({
                        'text': subtitle_text.strip(),
                        'start_time': start_time,
                        'end_time': end_time
                    })
                
                current_group = []
        
        # Handle remaining words
        if current_group:
            subtitle_text = ' '.join([w['word'] for w in current_group])
            start_time = current_group[0]['start']
            end_time = current_group[-1]['end']
            
            subtitles.append({
                'text': subtitle_text.strip(),
                'start_time': start_time,
                'end_time': end_time
            })
        
        return subtitles
    
    def seconds_to_srt_time(self, seconds: float) -> str:
        """Convert seconds to SRT time format (HH:MM:SS,mmm)"""
        td = timedelta(seconds=seconds)
        total_seconds = int(td.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        secs = total_seconds % 60
        milliseconds = int((seconds - total_seconds) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"
    
    def create_srt_content(self, subtitles: list[Dict[str, Any]]) -> str:
        """Create SRT content as string"""
        srt_content = ""
        
        for i, subtitle in enumerate(subtitles, 1):
            start_time = self.seconds_to_srt_time(subtitle['start_time'])
            end_time = self.seconds_to_srt_time(subtitle['end_time'])
            
            srt_content += f"{i}\n"
            srt_content += f"{start_time} --> {end_time}\n"
            srt_content += f"{subtitle['text']}\n\n"
        
        return srt_content

async def process_audio(job_id: str, file_path: str, max_words: int):
    """Process audio file in background"""
    global processing_status, completed_files
    
    try:
        processing_status[job_id] = {"status": "processing", "progress": "Starting conversion..."}
        
        converter = SimpleM4AToSRTConverter(max_words=max_words)
        
        processing_status[job_id]["progress"] = "Converting audio format..."
        temp_wav_path, duration = converter.convert_m4a_to_wav(file_path)
        
        try:
            processing_status[job_id]["progress"] = "Transcribing audio..."
            words_with_timing = converter.transcribe_audio(file_path)
            
            if not words_with_timing:
                processing_status[job_id] = {"status": "error", "message": "No speech detected in audio file"}
                return
            
            processing_status[job_id]["progress"] = "Generating subtitles..."
            subtitles = converter.group_words_into_subtitles(words_with_timing)
            srt_content = converter.create_srt_content(subtitles)
            
            # Store completed file
            completed_files[job_id] = {
                "srt_content": srt_content,
                "subtitle_count": len(subtitles),
                "duration": duration,
                "max_words": max_words,
                "timestamp": time.time()
            }
            
            processing_status[job_id] = {
                "status": "completed", 
                "subtitle_count": len(subtitles),
                "duration": duration
            }
            
        finally:
            # Clean up temporary WAV file
            try:
                os.unlink(temp_wav_path)
            except:
                pass
    
    except Exception as e:
        processing_status[job_id] = {"status": "error", "message": str(e)}
    
    finally:
        # Clean up original file
        try:
            os.unlink(file_path)
        except:
            pass

@app.get("/")
async def index():
    whisper_status = "✅ Available" if whisper_available else "❌ Not available"
    dependency_status = "✅ All dependencies available" if dependencies_ok else "⚠️ Some dependencies missing"
    
    return f"""
    <h1>🎵 M4A to SRT Converter API (Fallback Version)</h1>
    <p>Convert M4A audio files to SRT subtitle format using available transcription methods</p>
    <p><strong>System Status:</strong> {dependency_status}</p>
    <p><strong>Whisper Status:</strong> {whisper_status}</p>
    <div style="margin: 20px 0;">
        <h3>Available Endpoints:</h3>
        <ul style="text-align: left; max-width: 400px; margin: 0 auto;">
            <li><strong>POST /upload</strong> - Upload M4A file for conversion</li>
            <li><strong>GET /status/{{job_id}}</strong> - Check processing status</li>
            <li><strong>GET /download/{{job_id}}</strong> - Download converted SRT file</li>
            <li><strong>GET /health</strong> - Service health check</li>
            <li><strong>GET /docs</strong> - Interactive API documentation</li>
        </ul>
    </div>
    <div style="margin-top: 30px; font-size: 0.9em; color: #666;">
        <p>Max file size: 50MB | Supported format: M4A</p>
        <p>Uses available transcription methods (Whisper if available, fallback otherwise)</p>
    </div>
    """

@app.get("/health")
async def health_check():
    return {
        'status': 'healthy' if dependencies_ok else 'degraded',
        'service': 'M4A to SRT Converter (Fallback)',
        'dependencies_ok': dependencies_ok,
        'whisper_available': whisper_available,
        'timestamp': time.time()
    }

@app.post("/upload", response_model=UploadResponse)
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    max_words: int = Form(8)
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file selected")
    
    # Check file size (limit to 50MB)
    file_size = 0
    content = await file.read()
    file_size = len(content)
    
    if file_size > 50 * 1024 * 1024:  # 50MB limit
        raise HTTPException(status_code=400, detail="File size exceeds 50MB limit")
    
    # Validate parameters
    if max_words < 1 or max_words > 20:
        raise HTTPException(status_code=400, detail="max_words must be between 1 and 20")
    
    # Check file extension
    if not file.filename.lower().endswith('.m4a'):
        raise HTTPException(status_code=400, detail="Only M4A files are supported")
    
    # Save uploaded file
    job_id = str(uuid.uuid4())
    temp_path = os.path.join(tempfile.gettempdir(), f"{job_id}_{file.filename}")
    
    try:
        with open(temp_path, "wb") as f:
            f.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
    
    # Start background processing
    background_tasks.add_task(process_audio, job_id, temp_path, max_words)
    
    return UploadResponse(
        job_id=job_id,
        status="processing",
        message="File uploaded successfully, processing started",
        file_size_mb=round(file_size / 1024 / 1024, 2)
    )

@app.get("/status/{job_id}", response_model=StatusResponse)
async def get_status(job_id: str):
    if job_id not in processing_status:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return processing_status[job_id]

@app.get("/download/{job_id}")
async def download_file(job_id: str):
    if job_id not in completed_files:
        raise HTTPException(status_code=404, detail="File not ready or job not found")
    
    file_data = completed_files[job_id]
    
    # Create response with SRT content
    return Response(
        content=file_data['srt_content'],
        media_type='text/plain',
        headers={
            'Content-Disposition': f'attachment; filename=subtitles_{job_id}.srt'
        }
    )

# Clean up old files periodically
async def cleanup_old_files():
    """Remove files older than 1 hour"""
    current_time = time.time()
    to_remove = []
    
    for job_id, file_data in completed_files.items():
        if current_time - file_data.get('timestamp', 0) > 3600:  # 1 hour
            to_remove.append(job_id)
    
    for job_id in to_remove:
        completed_files.pop(job_id, None)
        processing_status.pop(job_id, None)

@app.on_event("startup")
async def startup_event():
    """Start background cleanup task"""
    async def periodic_cleanup():
        while True:
            await asyncio.sleep(1800)  # 30 minutes
            await cleanup_old_files()
    
    asyncio.create_task(periodic_cleanup())

if __name__ == '__main__':
    import uvicorn
    port = int(os.environ.get('PORT', 10000))
    uvicorn.run(app, host='0.0.0.0', port=port) 