#!/usr/bin/env python3
"""
Live HLS Stream Monitor - Setup Script

This script helps you set up the Live HLS Stream Monitor with all dependencies
and verifies that everything is working correctly.
"""

import os
import sys
import subprocess
import platform
import urllib.request
from pathlib import Path

def print_header(text):
    """Print a formatted header"""
    print(f"\n{'='*60}")
    print(f" {text}")
    print(f"{'='*60}")

def print_step(step_num, text):
    """Print a step with number"""
    print(f"\n[{step_num}] {text}")

def run_command(command, check=True):
    """Run a command and return the result"""
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True,
            check=check
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return False, e.stdout, e.stderr

def check_python_version():
    """Check if Python version is compatible"""
    print_step(1, "Checking Python version...")
    
    version = sys.version_info
    if version.major == 3 and version.minor >= 7:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} is compatible")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} is not compatible")
        print("   Minimum required: Python 3.7+")
        return False

def check_pip():
    """Check if pip is available"""
    print_step(2, "Checking pip availability...")
    
    success, stdout, stderr = run_command("pip --version")
    if success:
        print(f"✅ pip is available: {stdout.strip()}")
        return True
    else:
        print(f"❌ pip is not available: {stderr}")
        return False

def install_requirements():
    """Install Python requirements"""
    print_step(3, "Installing Python requirements...")
    
    requirements_file = Path("requirements.txt")
    if not requirements_file.exists():
        print("❌ requirements.txt not found")
        return False
    
    print("Installing core dependencies...")
    success, stdout, stderr = run_command("pip install -r requirements.txt")
    if success:
        print("✅ Core dependencies installed successfully")
    else:
        print(f"❌ Failed to install dependencies: {stderr}")
        return False
    
    # Optional: Install psutil for system metrics
    print("\nInstalling optional system metrics support (psutil)...")
    success, stdout, stderr = run_command("pip install psutil", check=False)
    if success:
        print("✅ psutil installed successfully - system metrics will be available")
    else:
        print("⚠️  psutil installation failed - system metrics will use simulated data")
        print("   This is optional and won't prevent the application from working")
    
    return True

def check_ffmpeg():
    """Check if FFmpeg/FFprobe is available"""
    print_step(4, "Checking FFmpeg/FFprobe availability...")
    
    # Check ffprobe
    success, stdout, stderr = run_command("ffprobe -version", check=False)
    if success:
        version_line = stdout.split('\n')[0] if stdout else "Unknown version"
        print(f"✅ FFprobe is available: {version_line}")
        return True
    else:
        print("❌ FFprobe is not available")
        print("\nFFprobe is required for advanced video analysis.")
        print("Installation instructions:")
        
        system = platform.system().lower()
        if system == "windows":
            print("  Windows: choco install ffmpeg")
            print("  Or download from: https://ffmpeg.org/download.html")
        elif system == "darwin":  # macOS
            print("  macOS: brew install ffmpeg")
        elif system == "linux":
            print("  Ubuntu/Debian: sudo apt update && sudo apt install ffmpeg")
            print("  CentOS/RHEL: sudo yum install ffmpeg")
        
        print("\nThe application will work without FFprobe but with limited analysis capabilities.")
        return False

def test_application():
    """Test if the application can start"""
    print_step(5, "Testing application startup...")
    
    app_file = Path("app.py")
    if not app_file.exists():
        print("❌ app.py not found")
        return False
    
    print("Starting application test (this may take a few seconds)...")
    
    # Try to import the app to check for basic errors
    try:
        import app
        print("✅ Application imports successfully")
        
        # Test that we can create a test client
        with app.app.test_client() as client:
            response = client.get('/')
            if response.status_code == 200:
                print("✅ Application responds to requests")
                return True
            else:
                print(f"❌ Application returned status code: {response.status_code}")
                return False
    except Exception as e:
        print(f"❌ Application test failed: {e}")
        return False

def show_next_steps():
    """Show next steps to the user"""
    print_header("Setup Complete! 🎉")
    
    print("Your Live HLS Stream Monitor is ready to use!")
    print("\nNext steps:")
    print("1. Start the application:")
    print("   python app.py")
    print("\n2. Open your browser to:")
    print("   http://localhost:8181")
    print("\n3. Enter an HLS stream URL (.m3u8) to start monitoring")
    
    print("\nExample HLS streams to test:")
    print("• https://devstreaming-cdn.apple.com/videos/streaming/examples/img_bipbop_adv_example_fmp4/master.m3u8")
    print("• https://demo.unified-streaming.com/k8s/features/stable/video/tears-of-steel/tears-of-steel.ism/.m3u8")
    
    print("\nFor help and documentation:")
    print("• README.md - Full documentation")
    print("• CONTRIBUTING.md - Development guidelines")
    print("• GitHub Issues - Report problems or request features")

def main():
    """Main setup function"""
    print_header("Live HLS Stream Monitor - Setup")
    print("This script will help you set up the application with all dependencies.")
    
    # Change to script directory
    script_dir = Path(__file__).parent.absolute()
    os.chdir(script_dir)
    print(f"Working directory: {script_dir}")
    
    success_count = 0
    total_steps = 5
    
    # Step 1: Check Python version
    if check_python_version():
        success_count += 1
    
    # Step 2: Check pip
    if check_pip():
        success_count += 1
    else:
        print("\n❌ Cannot continue without pip. Please install pip and try again.")
        sys.exit(1)
    
    # Step 3: Install requirements
    if install_requirements():
        success_count += 1
    else:
        print("\n❌ Cannot continue without core dependencies.")
        sys.exit(1)
    
    # Step 4: Check FFmpeg (optional)
    if check_ffmpeg():
        success_count += 1
    
    # Step 5: Test application
    if test_application():
        success_count += 1
    else:
        print("\n❌ Application test failed. Please check the error messages above.")
        sys.exit(1)
    
    # Show results
    print_header("Setup Results")
    print(f"✅ {success_count}/{total_steps} checks passed")
    
    if success_count == total_steps:
        show_next_steps()
    else:
        print("\n⚠️  Some optional components are not available:")
        if success_count < total_steps:
            print("• FFprobe - Advanced video analysis will be limited")
        print("\nThe application should still work with basic functionality.")
        show_next_steps()

if __name__ == "__main__":
    main()
