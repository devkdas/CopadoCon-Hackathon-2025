#!/usr/bin/env python3
"""
CopadoCon 2025 Hackathon - Smart Startup Script
This script makes it easy to get the hackathon project running by checking dependencies
and setting up configuration files automatically. Think of it as your helpful assistant!
"""

import os
import sys
import subprocess
from pathlib import Path

def check_requirements():
    """
    Make sure we have the essential packages installed before trying to start the server.
    If something's missing, we'll give you helpful suggestions on how to fix it.
    """
    try:
        import fastapi
        import uvicorn
        print("Great! Core dependencies are ready to go")
        return True
    except ImportError as e:
        print(f"Oops! We're missing some packages: {e}")
        print("Here's how to fix it:")
        print("   For everything: pip install -r requirements.txt")
        print("   Just the basics: pip install fastapi uvicorn pydantic requests python-dotenv")
        return False

def check_env_file():
    """
    Make sure we have a .env file with all our configuration settings.
    If it doesn't exist, we'll create one from the example template.
    """
    env_file = Path(".env")
    if not env_file.exists():
        print("No .env file found - let's create one for you")
        print("Copying from .env.example template...")
        
        example_file = Path(".env.example")
        if example_file.exists():
            import shutil
            shutil.copy(".env.example", ".env")
            print("Perfect! Created your .env file")
            print("Remember to add your actual API keys and settings to the .env file")
        else:
            print("Hmm, can't find .env.example file either")
            return False
    else:
        print("Found your .env configuration file")
    return True

def main():
    """
    This is where the magic happens! We'll check everything is set up properly
    and then launch your hackathon project with style.
    """
    print("CopadoCon 2025 Hackathon")
    print("=" * 60)
    print("Transforming Salesforce issue resolution from days to minutes")
    print("=" * 60)
    
    # First, let's make sure we have everything we need
    if not check_requirements():
        sys.exit(1)
    
    # Next, check that configuration is ready
    if not check_env_file():
        sys.exit(1)
    
    print("\nYour application will be available at:")
    print("   Dashboard: http://127.0.0.1:8080")
    print("   API Docs: http://127.0.0.1:8080/docs")
    print("   Health Check: http://127.0.0.1:8080/api/health")
    
    print("\nWhat you'll see in action:")
    print("   Real-time monitoring of Salesforce environments")
    print("   AI-powered root cause analysis with 85-92% confidence")
    print("   Automated workflows connecting Jira, GitHub, and Slack")
    print("   Beautiful interactive dashboard with live updates")
    print("   Lightning-fast incident resolution (days to minutes)")
    
    print("\nHackathon Demo Ready!")
    print("   Team: AI Signal Squad")
    print("   Innovation: AI correlation engine for DevOps observability")
    
    print("\nStarting your server now...")
    print("   Press Ctrl+C to stop when you're done")
    print("=" * 60)
    
    # Time to launch! We'll use the simple demo for better compatibility
    try:
        if os.path.exists("simple_demo.py"):
            print("Launching with Windows-friendly demo version...")
            subprocess.run([sys.executable, "simple_demo.py"], check=True)
        else:
            subprocess.run([sys.executable, "main.py"], check=True)
    except KeyboardInterrupt:
        print("\nThanks for trying our hackathon project!")
    except subprocess.CalledProcessError as e:
        print(f"\nOops! Something went wrong starting the server: {e}")
        print("Try running: python simple_demo.py")
        sys.exit(1)

if __name__ == "__main__":
    main()
