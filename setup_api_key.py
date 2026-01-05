#!/usr/bin/env python3
"""
CIP API Key Setup
=================
Run once to configure Anthropic API key for AI-powered metadata extraction.

Usage:
    python setup_api_key.py
"""

import os
import sys
from pathlib import Path

# CIP root directory
CIP_ROOT = Path(__file__).parent
ENV_FILE = CIP_ROOT / ".env"
CONFIG_FILE = CIP_ROOT / "backend" / "config.py"


def get_existing_key():
    """Check if key already exists."""
    # Check environment
    if os.environ.get('ANTHROPIC_API_KEY'):
        return os.environ['ANTHROPIC_API_KEY'], 'environment'
    
    # Check .env file
    if ENV_FILE.exists():
        with open(ENV_FILE, 'r') as f:
            for line in f:
                if line.startswith('ANTHROPIC_API_KEY='):
                    key = line.strip().split('=', 1)[1].strip('"\'')
                    if key:
                        return key, '.env file'
    
    return None, None


def save_to_env(key: str):
    """Save key to .env file."""
    lines = []
    key_found = False
    
    # Read existing .env
    if ENV_FILE.exists():
        with open(ENV_FILE, 'r') as f:
            lines = f.readlines()
    
    # Update or add key
    new_lines = []
    for line in lines:
        if line.startswith('ANTHROPIC_API_KEY='):
            new_lines.append(f'ANTHROPIC_API_KEY={key}\n')
            key_found = True
        else:
            new_lines.append(line)
    
    if not key_found:
        new_lines.append(f'ANTHROPIC_API_KEY={key}\n')
    
    # Write back
    with open(ENV_FILE, 'w') as f:
        f.writelines(new_lines)
    
    print(f"Saved to {ENV_FILE}")


def create_config_loader():
    """Create/update config.py to auto-load .env."""
    config_content = '''"""
CIP Configuration - Auto-loads environment variables from .env file.
"""

import os
from pathlib import Path

def load_env():
    """Load environment variables from .env file."""
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    value = value.strip('"\\\'')
                    os.environ.setdefault(key, value)

# Auto-load on import
load_env()

# Export configuration
ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')
CLAUDE_MODEL = "claude-sonnet-4-20250514"
EXTRACTION_TIMEOUT = 30

if not ANTHROPIC_API_KEY:
    print("WARNING: ANTHROPIC_API_KEY not set. Run setup_api_key.py to configure.")
'''
    
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, 'w') as f:
        f.write(config_content)
    
    print(f"Created {CONFIG_FILE}")


def test_key(key: str) -> bool:
    """Test if key works."""
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=key)
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=10,
            messages=[{"role": "user", "content": "Say OK"}]
        )
        return True
    except Exception as e:
        print(f"Key test failed: {e}")
        return False


def main():
    print("=" * 60)
    print("CIP API KEY SETUP")
    print("=" * 60)
    print()
    
    # Check existing
    existing_key, source = get_existing_key()
    if existing_key:
        masked = existing_key[:10] + "..." + existing_key[-4:]
        print(f"Found existing key in {source}: {masked}")
        
        response = input("\nTest existing key? [Y/n]: ").strip().lower()
        if response != 'n':
            print("Testing key...")
            if test_key(existing_key):
                print("Key is valid!")
                
                response = input("\nKeep this key? [Y/n]: ").strip().lower()
                if response != 'n':
                    save_to_env(existing_key)
                    create_config_loader()
                    print("\nSetup complete!")
                    return
    
    # Get new key
    print("\n" + "-" * 60)
    print("Enter your Anthropic API key")
    print("(Get one at: https://console.anthropic.com/settings/keys)")
    print("-" * 60)
    
    key = input("\nAPI Key: ").strip()
    
    if not key:
        print("No key entered. Exiting.")
        sys.exit(1)
    
    if not key.startswith('sk-ant-'):
        print("Warning: Key doesn't start with 'sk-ant-'. Proceeding anyway...")
    
    # Test
    print("\nTesting key...")
    if test_key(key):
        print("Key is valid!")
    else:
        response = input("\nKey test failed. Save anyway? [y/N]: ").strip().lower()
        if response != 'y':
            print("Aborted.")
            sys.exit(1)
    
    # Save
    save_to_env(key)
    create_config_loader()
    
    print("\n" + "=" * 60)
    print("SETUP COMPLETE")
    print("=" * 60)
    print()
    print("Your API key is now stored in .env")
    print("It will be automatically loaded when CIP starts.")
    print()


if __name__ == "__main__":
    main()
