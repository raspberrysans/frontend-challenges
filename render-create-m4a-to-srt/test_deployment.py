#!/usr/bin/env python3
"""
Test script to verify deployment setup
Run this to check if all dependencies and configurations are working
"""

import sys
import os
import subprocess

def test_imports():
    """Test if all required modules can be imported"""
    print("🔍 Testing imports...")
    
    modules = [
        'flask',
        'flask_cors', 
        'werkzeug',
        'speech_recognition',
        'pydub',
        'torch',
        'whisper',
        'numpy',
        'transformers'
    ]
    
    failed_imports = []
    
    for module in modules:
        try:
            __import__(module)
            print(f"✅ {module}")
        except ImportError as e:
            print(f"❌ {module}: {e}")
            failed_imports.append(module)
    
    return failed_imports

def test_ffmpeg():
    """Test FFmpeg availability"""
    print("\n🔍 Testing FFmpeg...")
    
    # Check system ffmpeg
    try:
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ System FFmpeg available")
            return True
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    # Check custom ffmpeg
    home_dir = os.path.expanduser("~")
    ffmpeg_path = os.path.join(home_dir, "bin", "ffmpeg")
    
    if os.path.exists(ffmpeg_path):
        try:
            result = subprocess.run([ffmpeg_path, '-version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print(f"✅ Custom FFmpeg available at {ffmpeg_path}")
                return True
        except subprocess.TimeoutExpired:
            pass
    
    print("❌ No FFmpeg found")
    return False

def test_whisper():
    """Test Whisper availability"""
    print("\n🔍 Testing Whisper...")
    
    try:
        result = subprocess.run(['whisper', '--help'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ Whisper CLI available")
            return True
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    print("❌ Whisper CLI not found")
    return False

def test_environment():
    """Test environment variables and paths"""
    print("\n🔍 Testing environment...")
    
    # Check PATH
    path = os.environ.get('PATH', '')
    home_dir = os.path.expanduser("~")
    bin_path = os.path.join(home_dir, "bin")
    
    if bin_path in path:
        print(f"✅ Custom bin path in PATH: {bin_path}")
    else:
        print(f"⚠️ Custom bin path not in PATH: {bin_path}")
    
    # Check PORT
    port = os.environ.get('PORT', 'Not set')
    print(f"PORT: {port}")
    
    # Check Python version
    print(f"Python version: {sys.version}")

def main():
    print("🚀 Deployment Test Script")
    print("=" * 50)
    
    # Test environment
    test_environment()
    
    # Test imports
    failed_imports = test_imports()
    
    # Test external tools
    ffmpeg_ok = test_ffmpeg()
    whisper_ok = test_whisper()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 SUMMARY")
    print("=" * 50)
    
    if failed_imports:
        print(f"❌ Failed imports: {', '.join(failed_imports)}")
    else:
        print("✅ All imports successful")
    
    if ffmpeg_ok:
        print("✅ FFmpeg available")
    else:
        print("❌ FFmpeg not available")
    
    if whisper_ok:
        print("✅ Whisper available")
    else:
        print("❌ Whisper not available")
    
    if not failed_imports and ffmpeg_ok and whisper_ok:
        print("\n🎉 All tests passed! Deployment should work.")
    else:
        print("\n⚠️ Some tests failed. Check the issues above.")

if __name__ == "__main__":
    main() 