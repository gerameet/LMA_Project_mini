#!/usr/bin/env python3
"""
Hugging Face Authentication Helper
Guides you through the process of setting up authentication for Wikipedia datasets.
"""

import subprocess
import sys
import os

def check_huggingface_cli():
    """Check if huggingface-cli is available."""
    try:
        result = subprocess.run(['huggingface-cli', '--help'], 
                              capture_output=True, text=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def install_huggingface_hub():
    """Install huggingface-hub if not available."""
    print("📦 Installing huggingface-hub...")
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'huggingface-hub'], check=True)
        print("✅ huggingface-hub installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install huggingface-hub: {e}")
        return False

def login_interactive():
    """Interactive login process."""
    print("🔐 Starting Hugging Face authentication...")
    
    if not check_huggingface_cli():
        print("⚠️  huggingface-cli not found. Installing...")
        if not install_huggingface_hub():
            return False
    
    print("\n" + "="*60)
    print("HUGGING FACE TOKEN SETUP")
    print("="*60)
    print("You need a token to access Wikipedia datasets.")
    print("\n📋 Steps:")
    print("1. Go to: https://huggingface.co/settings/tokens")
    print("2. Click 'New token'")
    print("3. Name: 'corpus_download'")
    print("4. Type: 'Read' (sufficient for downloading)")
    print("5. Click 'Generate'")
    print("6. Copy the token (starts with 'hf_...')")
    
    input("\nPress Enter when you have your token ready...")
    
    print("\n🎯 Now logging in...")
    try:
        # Run huggingface-cli login interactively
        subprocess.run(['huggingface-cli', 'login'], check=True)
        print("✅ Authentication successful!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Authentication failed: {e}")
        return False
    except KeyboardInterrupt:
        print("\n❌ Authentication cancelled by user")
        return False

def verify_authentication():
    """Verify that authentication works."""
    print("🧪 Testing authentication...")
    try:
        from huggingface_hub import whoami
        user_info = whoami()
        print(f"✅ Successfully authenticated as: {user_info['name']}")
        return True
    except Exception as e:
        print(f"❌ Authentication test failed: {e}")
        return False

def main():
    print("🔐 HUGGING FACE AUTHENTICATION HELPER")
    print("="*50)
    
    # Check if already authenticated
    if verify_authentication():
        print("🎉 You're already authenticated!")
        print("\nReady to run:")
        print("  python example.py")
        print("  python download_data.py")
        return
    
    print("❌ No valid authentication found.")
    
    choice = input("\nWould you like to set up authentication now? (y/n): ").strip().lower()
    
    if choice in ['y', 'yes']:
        if login_interactive():
            if verify_authentication():
                print("\n🎉 Setup complete!")
                print("\nYou can now run:")
                print("  python example.py  # Test with Wikipedia datasets")
                print("  python download_data.py  # Full download")
            else:
                print("\n❌ Authentication setup failed")
        else:
            print("\n❌ Authentication setup failed")
    else:
        print("\n⚠️  Without authentication, some datasets may not be available.")
        print("You can still run:")
        print("  python download_data.py --skip-auth-check")

if __name__ == "__main__":
    main()
