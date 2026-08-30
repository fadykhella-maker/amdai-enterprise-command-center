"""Stable Streamlit Community Cloud entry point.

Execute the dashboard file on every Streamlit rerun. A normal module import is
cached by Python and can leave later browser sessions with a blank page.
"""

from pathlib import Path
import runpy


runpy.run_path(str(Path(__file__).with_name("amd_dashboard_v2.py")), run_name="__main__")
