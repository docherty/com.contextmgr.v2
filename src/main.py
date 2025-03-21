import os
import subprocess
from pathlib import Path

def run_streamlit():
    """Run the Streamlit application"""
    streamlit_path = Path(__file__).parent / "ui" / "app.py"
    subprocess.run(["streamlit", "run", str(streamlit_path)])

if __name__ == "__main__":
    # Ensure we're in the virtual environment
    if "VIRTUAL_ENV" not in os.environ:
        print("Warning: Virtual environment not detected. Some features may not work.")
    
    # Run the Streamlit UI
    run_streamlit()