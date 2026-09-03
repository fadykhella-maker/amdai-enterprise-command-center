"""Stable Streamlit Community Cloud entry point.

Execute the dashboard file on every Streamlit rerun. A normal module import is
cached by Python and can leave later browser sessions with a blank page.
"""

from pathlib import Path
import runpy

import streamlit as st

from auth.viewer_portal import require_viewer

require_viewer()

# The very first script execution of a brand-new browser session (most
# commonly a returning visitor whose "remembered device" cookie skips the
# login form's own post-auth st.rerun()) can render before the page is fully
# warmed up, leaving elements such as the header logo missing until a manual
# refresh. Force exactly one silent rerun per session so every viewer always
# gets a fully warmed second pass before anything is shown.
if not st.session_state.get("_warmed_up"):
    st.session_state["_warmed_up"] = True
    st.rerun()

runpy.run_path(str(Path(__file__).with_name("amd_dashboard_v2.py")), run_name="__main__")
