#!/usr/bin/env python3
"""
Step 4: Run the Streamlit App

This script launches the CCSF Board Meetings Assistant chat interface.

Usage:
    python scripts/04_run_app.py

Or directly:
    streamlit run src/app/streamlit_app.py
"""

import subprocess
import sys
from pathlib import Path


def main():
    # Path to the Streamlit app
    app_path = Path(__file__).parent.parent / "src" / "app" / "streamlit_app.py"

    if not app_path.exists():
        print(f"Error: App not found at {app_path}")
        sys.exit(1)

    print("=" * 60)
    print("CCSF Board Meetings Assistant")
    print("=" * 60)
    print(f"Starting Streamlit app...")
    print(f"App path: {app_path}")
    print()
    print("The app will open in your default browser.")
    print("Press Ctrl+C to stop the server.")
    print("=" * 60)

    # Run Streamlit
    subprocess.run([
        sys.executable, "-m", "streamlit", "run",
        str(app_path),
        "--server.headless", "true"
    ])


if __name__ == "__main__":
    main()
