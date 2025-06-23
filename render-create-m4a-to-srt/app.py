#!/usr/bin/env python3
"""
M4A to SRT Converter - Render Deployment
Flask web service for converting M4A audio files to SRT subtitles
"""

from flask import Flask, request, Response, send_file, jsonify
from flask_cors import CORS
import os
import tempfile
import uuid
from datetime import timedelta
import speech_recognition as sr
from pydub import AudioSegment
from pydub.silence import split_on_silence
import subprocess
import json
import threading
import time
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)

# Configure ffmpeg path for Render
home_dir = os.path.expanduser("~")
ffmpeg_path = os.path.join(home_dir, "bin", "ffmpeg")
ffprobe_path = os.path.join(home_dir, "bin", "ffprobe")

# Add to PATH
current_path = os.environ.get('PATH', '')
bin_path = os.path.join(home_dir, "bin")
if bin_path not in current_path:
    os.environ['PATH'] = f"{bin_path}:{current_path}"

# Configure pydub to use our ffmpeg
if os.path.exists(ffmpeg_path):
    AudioSegment.converter = ffmpeg_path
    AudioSegment.ffmpeg = ffmpeg_path
    AudioSegment.ffprobe = ffprobe_path
    print(f"FFmpeg configured at: {ffmpeg_path}")
else:
    print("Warning: FFmpeg not found, using system default")

# Store processing status
processing_status = {}
completed_files = {}

class M4AToSRTConverter:
    def __init__(self, max_words=8, framerate=25):
        self.max_words = max_words
        self.framerate = framerate
        self.recognizer = sr.Recognizer()
        
    def convert_m4a_to_wav(self, m4a_path):
        """Convert M4A to WAV for speech recognition"""
        print("Converting M4A to WAV...")
        audio = AudioSegment.from_file(m4a_path, format="m4a")
        
        # Create temporary WAV file
        temp_wav = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        audio.export(temp_wav.name, format="wav")
        return temp_wav.name, len(audio) / 1000.0
    
    def transcribe_with_whisper(self, audio_path):
        """Use OpenAI Whisper for transcription with accurate timestamps"""
        print("Transcribing audio with Whisper...")
        
        try:
            # Set up environment for whisper command
            env = os.environ.copy()
            env['PATH'] = f"{os.path.join(os.path.expanduser('~'), 'bin')}:{env.get('PATH', '')}"
            
            # Try to use whisper command line tool with word-level timestamps
            temp_dir = tempfile.mkdtemp()
            
            # Run whisper with proper environment
            result = subprocess.run([
                'whisper', audio_path, 
                '--model', 'base',
                '--output_format', 'json',
                '--word_timestamps', 'True',
                '--output_dir', temp_dir,
                '--language', 'auto'
            ], capture_output=True, text=True, check=True, timeout=1800, env=env)
            
            # Find the output JSON file
            base_name = os.path.splitext(os.path.basename(audio_path))[0]
            json_path = os.path.join(temp_dir, f"{base_name}.json")
            
            if os.path.exists(json_path):
                with open(json_path, 'r', encoding='utf-8') as f:
                    whisper_result = json.load(f)
                
                # Extract word-level timestamps if available
                words_with_timing = []
                for segment in whisper_result.get('segments', []):
                    if 'words' in segment:
                        for word_info in segment['words']:
                            words_with_timing.append({
                                'word': word_info['word'].strip(),
                                'start': word_info['start'],
                                'end': word_info['end']
                            })
                    else:
                        # Fallback to segment-level timing
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
                    os.unlink(json_path)
                    os.rmdir(temp_dir)
                except:
                    pass
                
                return words_with_timing
                
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as e:
            print(f"Whisper failed: {e}")
            print("Falling back to SpeechRecognition...")
            return self.transcribe_audio_fallback(audio_path)
    
    def transcribe_audio_fallback(self, wav_path):
        """Fallback transcription using SpeechRecognition"""
        print("Transcribing audio with SpeechRecognition...")
        
        try:
            # Load audio file
            audio = AudioSegment.from_wav(wav_path)
            
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
                if i > 20:  # Reduced for Render
                    break
                
                chunk_path = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
                chunk.export(chunk_path.name, format="wav")
                
                try:
                    with sr.AudioFile(chunk_path.name) as source:
                        # Adjust for ambient noise
                        self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                        audio_data = self.recognizer.record(source)
                        try:
                            text = self.recognizer.recognize_google(audio_data)
                            if text.strip():
                                chunk_duration = len(chunk) / 1000.0
                                words = text.split()
                                word_duration = chunk_duration / len(words) if words else 0
                                
                                for j, word in enumerate(words):
                                    words_with_timing.append({
                                        'word': word,
                                        'start': current_time + (j * word_duration),
                                        'end': current_time + ((j + 1) * word_duration)
                                    })
                        except sr.UnknownValueError:
                            print(f"Could not understand chunk {i+1}")
                        except sr.RequestError as e:
                            print(f"Error with speech recognition: {e}")
                            # Continue with other chunks
                            pass
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
    
    def group_words_into_subtitles(self, words_with_timing):
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
    
    def seconds_to_srt_time(self, seconds):
        """Convert seconds to SRT time format (HH:MM:SS,mmm)"""
        td = timedelta(seconds=seconds)
        total_seconds = int(td.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        secs = total_seconds % 60
        milliseconds = int((seconds - total_seconds) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"
    
    def create_srt_content(self, subtitles):
        """Create SRT content as string"""
        srt_content = ""
        
        for i, subtitle in enumerate(subtitles, 1):
            start_time = self.seconds_to_srt_time(subtitle['start_time'])
            end_time = self.seconds_to_srt_time(subtitle['end_time'])
            
            srt_content += f"{i}\n"
            srt_content += f"{start_time} --> {end_time}\n"
            srt_content += f"{subtitle['text']}\n\n"
        
        return srt_content

def process_audio(job_id, file_path, max_words, framerate):
    """Process audio file in background thread"""
    global processing_status, completed_files
    
    try:
        processing_status[job_id] = {"status": "processing", "progress": "Starting conversion..."}
        
        converter = M4AToSRTConverter(max_words=max_words, framerate=framerate)
        
        processing_status[job_id]["progress"] = "Converting audio format..."
        temp_wav_path, duration = converter.convert_m4a_to_wav(file_path)
        
        try:
            processing_status[job_id]["progress"] = "Transcribing audio..."
            words_with_timing = converter.transcribe_with_whisper(file_path)
            
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

@app.route('/')
def index():
    return '''
    <h1>🎵 M4A to SRT Converter API</h1>
    <p>Convert M4A audio files to SRT subtitle format</p>
    <div style="margin: 20px 0;">
        <h3>Available Endpoints:</h3>
        <ul style="text-align: left; max-width: 400px; margin: 0 auto;">
            <li><strong>POST /upload</strong> - Upload M4A file for conversion</li>
            <li><strong>GET /status/{job_id}</strong> - Check processing status</li>
            <li><strong>GET /download/{job_id}</strong> - Download converted SRT file</li>
            <li><strong>GET /health</strong> - Service health check</li>
        </ul>
    </div>
    <div style="margin-top: 30px; font-size: 0.9em; color: #666;">
        <p>Max file size: 100MB | Supported format: M4A</p>
        <p>Processing time varies based on audio length</p>
    </div>
    '''

@app.route('/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'service': 'M4A to SRT Converter',
        'timestamp': time.time()
    })

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Check file size (limit to 100MB for free tier)
    file.seek(0, 2)  # Seek to end
    file_size = file.tell()
    file.seek(0)  # Reset to beginning
    
    if file_size > 100 * 1024 * 1024:  # 100MB limit
        return jsonify({'error': 'File size exceeds 100MB limit'}), 400
    
    # Get parameters
    max_words = int(request.form.get('max_words', 8))
    framerate = float(request.form.get('framerate', 25.0))
    
    # Validate parameters
    if max_words < 1 or max_words > 20:
        return jsonify({'error': 'max_words must be between 1 and 20'}), 400
    
    if framerate <= 0 or framerate > 120:
        return jsonify({'error': 'framerate must be between 0 and 120'}), 400
    
    # Check file extension
    if not file.filename.lower().endswith('.m4a'):
        return jsonify({'error': 'Only M4A files are supported'}), 400
    
    # Save uploaded file
    job_id = str(uuid.uuid4())
    filename = secure_filename(file.filename)
    temp_path = os.path.join(tempfile.gettempdir(), f"{job_id}_{filename}")
    
    try:
        file.save(temp_path)
    except Exception as e:
        return jsonify({'error': f'Failed to save file: {str(e)}'}), 500
    
    # Start background processing
    thread = threading.Thread(
        target=process_audio, 
        args=(job_id, temp_path, max_words, framerate)
    )
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'job_id': job_id,
        'status': 'processing',
        'message': 'File uploaded successfully, processing started',
        'file_size_mb': round(file_size / 1024 / 1024, 2)
    })

@app.route('/status/<job_id>')
def get_status(job_id):
    if job_id not in processing_status:
        return jsonify({'error': 'Job not found'}), 404
    
    return jsonify(processing_status[job_id])

@app.route('/download/<job_id>')
def download_file(job_id):
    if job_id not in completed_files:
        return jsonify({'error': 'File not ready or job not found'}), 404
    
    file_data = completed_files[job_id]
    
    # Create response with SRT content
    response = Response(
        file_data['srt_content'],
        mimetype='text/plain',
        headers={
            'Content-Disposition': f'attachment; filename=subtitles_{job_id}.srt'
        }
    )
    
    return response

# Clean up old files periodically
def cleanup_old_files():
    """Remove files older than 1 hour"""
    current_time = time.time()
    to_remove = []
    
    for job_id, file_data in completed_files.items():
        if current_time - file_data.get('timestamp', 0) > 3600:  # 1 hour
            to_remove.append(job_id)
    
    for job_id in to_remove:
        completed_files.pop(job_id, None)
        processing_status.pop(job_id, None)

# Run cleanup every 30 minutes
def periodic_cleanup():
    while True:
        time.sleep(1800)  # 30 minutes
        cleanup_old_files()

cleanup_thread = threading.Thread(target=periodic_cleanup)
cleanup_thread.daemon = True
cleanup_thread.start()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)