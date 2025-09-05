#!/usr/bin/env python3
"""
Quick fix script to install missing dependencies and set up authentication.
"""

import subprocess
import sys
import os

def run_command(command, description):
    """Run a command and handle errors."""
    print(f"📦 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def main():
    print("🔧 QUICK FIX - Installing missing dependencies")
    print("=" * 50)
    
    # Install protobuf
    success = run_command("pip install protobuf>=3.20.0", "Installing protobuf")
    if not success:
        print("⚠️  Manual installation needed: pip install protobuf")
    
    # Install any other missing packages
    run_command("pip install -r requirements.txt", "Installing all requirements")
    
    print("\n🔐 HUGGING FACE AUTHENTICATION")
    print("=" * 50)
    print("For some datasets, you'll need a Hugging Face token:")
    print("1. Go to: https://huggingface.co/settings/tokens")
    print("2. Create a new token (read permission)")
    print("3. Run: huggingface-cli login")
    print("\nOr run the main script with --skip-auth-check to continue without authentication")
    
    print("\n🧪 TEST YOUR SETUP")
    print("=" * 50)
    print("Run: python test_setup.py")
    print("Then: python example.py")

if __name__ == "__main__":
    main()
