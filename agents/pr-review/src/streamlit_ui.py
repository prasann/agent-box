"""Entry point for Streamlit UI."""

import sys
import os
from pathlib import Path


def main():
    """Launch the Streamlit UI."""
    # Get the directory where this script is installed
    script_dir = Path(__file__).parent
    streamlit_app = script_dir.parent / "streamlit_app.py"
    
    # Import streamlit and run
    from streamlit.web import cli as stcli
    
    # Pass the streamlit app path and any additional arguments
    sys.argv = ["streamlit", "run", str(streamlit_app)] + sys.argv[1:]
    sys.exit(stcli.main())


if __name__ == "__main__":
    main()
