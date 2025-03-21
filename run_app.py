#!/usr/bin/env python3
import subprocess
import os
from pathlib import Path

def main():
    """Run the Streamlit application with file watching disabled"""
    # Path to the Streamlit app
    app_path = Path(__file__).parent / "src" / "ui" / "app.py"
    
    # Set the PYTHONPATH to include the project root
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(__file__).parent) + ":" + env.get("PYTHONPATH", "")
    
    # Run Streamlit with file watcher disabled
    subprocess.run([
        "streamlit", 
        "run", 
        str(app_path), 
        "--server.fileWatcherType=none"
    ], env=env)

if __name__ == "__main__":
    main()