#!/usr/bin/env python3
"""
Test script to verify deployment environment
Checks all dependencies and basic functionality
"""

import sys
import subprocess
import importlib

def test_import(module_name, package_name=None):
    """Test if a module can be imported"""
    try:
        importlib.import_module(module_name)
        print(f"✅ {package_name or module_name} - OK")
        return True
    except ImportError as e:
        print(f"❌ {package_name or module_name} - FAILED: {e}")
        return False

def test_command(command, description):
    """Test if a command is available"""
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"✅ {description} - OK")
            return True
        else:
            print(f"❌ {description} - FAILED: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ {description} - FAILED: {e}")
        return False

def main():
    print("🧪 Testing M4A to SRT Converter Deployment Environment")
    print("=" * 60)
    
    # Test Python version
    print(f"🐍 Python version: {sys.version}")
    
    # Test core dependencies
    print("\n📚 Testing Core Dependencies:")
    core_deps = [
        ("fastapi", "FastAPI"),
        ("uvicorn", "Uvicorn"),
        ("pydantic", "Pydantic"),
        ("pydub", "pydub"),
        ("openai_whisper", "OpenAI Whisper"),
        ("requests", "requests"),
    ]
    
    core_ok = all(test_import(module, name) for module, name in core_deps)
    
    # Test system commands
    print("\n🔧 Testing System Commands:")
    system_ok = all([
        test_command(["ffmpeg", "-version"], "FFmpeg"),
        test_command(["ffprobe", "-version"], "FFprobe"),
    ])
    
    # Test Whisper installation
    print("\n🎤 Testing Whisper Installation:")
    whisper_ok = test_command(["whisper", "--help"], "Whisper CLI")
    
    # Test application import
    print("\n🚀 Testing Application:")
    app_ok = test_import("app", "Application Module")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary:")
    
    if all([core_ok, system_ok, whisper_ok, app_ok]):
        print("🎉 All tests passed! Deployment environment is ready.")
        print("\n🚀 You can now start the application with:")
        print("   python app.py")
        print("   or")
        print("   uvicorn app:app --host 0.0.0.0 --port 10000")
        return 0
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 