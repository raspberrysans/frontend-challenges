#!/usr/bin/env python3
"""
M4A to SRT Subtitle Converter
Converts M4A audio files to SRT subtitle format with customizable settings
"""

import os
import sys
import argparse
from datetime import timedelta
import speech_recognition as sr
from pydub import AudioSegment
from pydub.silence import split_on_silence
import tempfile
import subprocess
import json
import re

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
        return temp_wav.name, len(audio) / 1000.0  # Return path and duration in seconds
    
    def transcribe_with_whisper(self, audio_path):
        """Use OpenAI Whisper for transcription with accurate timestamps"""
        print("Transcribing audio with Whisper...")
        
        try:
            # Try to use whisper command line tool with word-level timestamps
            temp_dir = tempfile.mkdtemp()
            result = subprocess.run([
                'whisper', audio_path, 
                '--model', 'base',
                '--output_format', 'json',
                '--word_timestamps', 'True',
                '--output_dir', temp_dir
            ], capture_output=True, text=True, check=True)
            
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
                
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("Whisper not found or failed, falling back to SpeechRecognition...")
            return self.transcribe_audio_fallback(audio_path)
    
    def transcribe_audio_fallback(self, wav_path):
        """Fallback transcription using SpeechRecognition"""
        print("Transcribing audio with SpeechRecognition...")
        
        # Load audio file
        audio = AudioSegment.from_wav(wav_path)
        
        # Split audio on silence to get chunks
        chunks = split_on_silence(
            audio,
            min_silence_len=800,  # 800ms of silence
            silence_thresh=audio.dBFS - 16,
            keep_silence=500
        )
        
        if not chunks:
            chunks = [audio]
        
        words_with_timing = []
        current_time = 0
        
        for i, chunk in enumerate(chunks):
            print(f"Processing chunk {i+1}/{len(chunks)}")
            
            chunk_path = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            chunk.export(chunk_path.name, format="wav")
            
            try:
                with sr.AudioFile(chunk_path.name) as source:
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
            finally:
                try:
                    os.unlink(chunk_path.name)
                except:
                    pass
                current_time += len(chunk) / 1000.0
        
        return words_with_timing
    
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
    
    def create_srt_file(self, subtitles, output_path):
        """Create SRT subtitle file"""
        print("Creating SRT file...")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            for i, subtitle in enumerate(subtitles, 1):
                start_time = self.seconds_to_srt_time(subtitle['start_time'])
                end_time = self.seconds_to_srt_time(subtitle['end_time'])
                
                f.write(f"{i}\n")
                f.write(f"{start_time} --> {end_time}\n")
                f.write(f"{subtitle['text']}\n\n")
        
        print(f"SRT file saved to: {output_path}")
    
    def convert(self, m4a_path, output_path=None):
        """Main conversion function"""
        if not os.path.exists(m4a_path):
            raise FileNotFoundError(f"M4A file not found: {m4a_path}")
        
        if output_path is None:
            base_name = os.path.splitext(m4a_path)[0]
            output_path = f"{base_name}.srt"
        
        temp_wav_path = None
        try:
            # Convert M4A to WAV
            temp_wav_path, duration = self.convert_m4a_to_wav(m4a_path)
            
            # Transcribe audio (try Whisper first, fallback to SpeechRecognition)
            words_with_timing = self.transcribe_with_whisper(m4a_path)
            
            if not words_with_timing:
                print("No speech detected in audio file")
                return
            
            # Group words into subtitles
            subtitles = self.group_words_into_subtitles(words_with_timing)
            
            # Create SRT file
            self.create_srt_file(subtitles, output_path)
            
            print(f"\nConversion complete!")
            print(f"Generated {len(subtitles)} subtitles")
            print(f"Max words per subtitle: {self.max_words}")
            print(f"Total duration: {duration:.2f} seconds")
            print(f"Output: {output_path}")
            
        finally:
            # Clean up temporary WAV file
            if temp_wav_path:
                try:
                    os.unlink(temp_wav_path)
                except:
                    pass

def main():
    parser = argparse.ArgumentParser(
        description="Convert M4A audio to SRT subtitles",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python m4a_to_srt.py audio.m4a
  python m4a_to_srt.py audio.m4a -w 10 -f 29.97
  python m4a_to_srt.py audio.m4a -o custom_output.srt
        """
    )
    
    parser.add_argument("input", help="Input M4A file path")
    parser.add_argument("-o", "--output", help="Output SRT file path")
    parser.add_argument("-w", "--words", type=int, default=8,
                       help="Maximum words per subtitle (default: 8)")
    parser.add_argument("-f", "--framerate", type=float, default=25.0,
                       help="Video framerate for timing reference (default: 25.0)")
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.words < 1:
        print("Error: Words per subtitle must be at least 1")
        sys.exit(1)
    
    if args.framerate <= 0:
        print("Error: Framerate must be positive")
        sys.exit(1)
    
    try:
        converter = M4AToSRTConverter(
            max_words=args.words,
            framerate=args.framerate
        )
        converter.convert(args.input, args.output)
        
    except KeyboardInterrupt:
        print("\nConversion cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()