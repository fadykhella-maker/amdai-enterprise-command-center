"""Viewer-only authentication gate for the hosted Streamlit dashboard."""

from __future__ import annotations

import html
from typing import Any

import streamlit as st
import streamlit_authenticator as stauth


def _secret(name: str, default: Any = None) -> Any:
    """Read an auth value without ever displaying the secret."""
    try:
        auth = st.secrets.get("auth", {})
        return auth.get(name, default)
    except FileNotFoundError:
        return default


def _render_global_scene() -> None:
    routes = """
      <path d="M115 225 Q360 45 610 210"/><path d="M175 265 Q460 480 790 245"/>
      <path d="M380 170 Q650 5 900 205"/><path d="M440 300 Q710 110 1035 275"/>
      <path d="M95 330 Q510 120 980 345"/><path d="M250 90 Q550 380 870 105"/>
    """
    st.markdown(
        f"""
<div class="amd-login-world" aria-hidden="true">
  <div class="world-heading"><b>AMD is Global</b><span>HQ · Engineering &amp; R&amp;D · Regional Sales · Foundry Partners</span></div>
  <svg viewBox="0 0 1120 500" preserveAspectRatio="xMidYMid slice">
    <defs><filter id="glow"><feGaussianBlur stdDeviation="3" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>
    <g class="grid"><path d="M0 100H1120M0 200H1120M0 300H1120M0 400H1120M140 0V500M280 0V500M420 0V500M560 0V500M700 0V500M840 0V500M980 0V500"/></g>
    <g class="continents">
      <path d="M75 146l28-30 49-11 42 9 20 21 44 4 31 31-12 23-36 9-19 35-25 10-8 42-29 38-22-33-28-12-13-46-32-25 15-30z"/>
      <path d="M281 114l13-18 25 3 7 15-20 14z"/>
      <path d="M323 230l37 4 31 28 15 47-17 54-28 53-24-31 3-42-23-36-12-48z"/>
      <path d="M505 145l28-31 48-12 34 14 38-7 40 13 55-6 36 18 57 2 43 24 67 16 34 31-21 25-55-4-28 22-50-7-33 20-51-10-28-38-33 9-22-28-43 5-31-26-37 9-34-21z"/>
      <path d="M566 225l48 10 31 38-8 55-30 73-39-22-18-51-20-43z"/>
      <path d="M874 342l40-22 56 12 31 34-15 43-67 10-49-30z"/>
      <path d="M1008 389l18-9 16 15-13 17z"/>
    </g>
    <g class="routes">{routes}</g>
    <g class="nodes"><circle cx="145" cy="210" r="5"/><circle cx="255" cy="245" r="5"/><circle cx="420" cy="178" r="4"/><circle cx="655" cy="180" r="5"/><circle cx="810" cy="250" r="5"/><circle cx="925" cy="218" r="5"/><circle cx="960" cy="385" r="5"/></g>
  </svg>
</div>
""",
        unsafe_allow_html=True,
    )


def _render_styles() -> None:
    st.markdown(
        """
<style>
  [data-testid="stHeader"], [data-testid="stSidebar"], footer {display:none!important}
  div.st-key-viewer_logout {position:fixed;right:18px;top:14px;z-index:999999;width:auto}
  div.st-key-viewer_logout button {background:#0a0e12!important;color:#d7af63!important;border:1px solid #3c3426!important;padding:.3rem .8rem!important}
  .stApp {background:#020405;color:#f4f4f4}
  .main .block-container {max-width:560px;margin-top:12vh;padding:34px 38px 32px;position:relative;z-index:4;background:rgba(9,13,17,.96);border:1px solid #29313a;border-radius:25px;box-shadow:0 24px 90px #000}
  .main .block-container:before {content:"AMD";display:block;width:80px;height:80px;margin:0 auto 18px;border-radius:20px;background:linear-gradient(145deg,#e3bd70,#ac7924);color:#17130b;text-align:center;line-height:80px;font:800 22px Inter,sans-serif;box-shadow:0 0 35px rgba(207,158,67,.25)}
  .amd-login-world {position:fixed;inset:0;z-index:0;overflow:hidden;background:radial-gradient(circle at 50% 32%,#0d1726 0,#04080d 43%,#010202 78%)}
  .amd-login-world:after {content:"";position:absolute;inset:0;background:linear-gradient(90deg,rgba(0,0,0,.25),transparent 30%,transparent 70%,rgba(0,0,0,.32));pointer-events:none}
  .amd-login-world svg {position:absolute;inset:11% 0 0;width:100%;height:82%;opacity:.78}
  .world-heading {position:absolute;top:26px;left:28px;display:flex;flex-direction:column;gap:3px;color:#8f6d2d;font:14px ui-monospace,monospace;letter-spacing:1px}
  .world-heading b {font:700 22px Inter,sans-serif;color:#c8993f}.world-heading span{color:#58606c}
  .grid path {stroke:#132235;stroke-width:1;fill:none;opacity:.72}.continents path{fill:#07101a;stroke:#182638;stroke-width:1.5}
  .routes path {fill:none;stroke:#245da6;stroke-width:1.4;stroke-dasharray:8 9;animation:route 7s linear infinite;filter:url(#glow)}
  .routes path:nth-child(even){stroke:#c99a43;animation-duration:10s}.nodes circle{fill:#d5a84c;stroke:#f3d48b;stroke-width:2;filter:url(#glow);animation:pulse 2.2s ease-in-out infinite alternate}
  @keyframes route {to{stroke-dashoffset:-136}} @keyframes pulse{to{r:8;opacity:.45}}
  [data-testid="stForm"] {background:transparent;border:0;padding:0;box-shadow:none}
  [data-testid="stForm"] h1,[data-testid="stForm"] h2,[data-testid="stForm"] h3{text-align:center;color:#d3a247}
  .stTextInput input {background:#020304!important;border-color:#28303a!important;color:#fff!important}
  .stButton button,[data-testid="stFormSubmitButton"] button {background:linear-gradient(90deg,#e2bd78,#bb842b)!important;color:#17130b!important;border:0!important;font-weight:800!important}
  .portal-note{text-align:center;color:#8f98a5;font:12px ui-monospace,monospace;letter-spacing:1.5px;margin:-10px 0 16px}
  @media(max-width:700px){.main .block-container{margin-top:8vh;padding:26px 22px}.world-heading{left:18px}.world-heading span{display:none}.amd-login-world svg{width:180%;left:-40%}}
</style>
""",
        unsafe_allow_html=True,
    )


def require_viewer() -> dict[str, str]:
    """Authenticate a viewer before any dashboard code or telemetry is loaded."""
    username = str(_secret("viewer_username", "")).strip()
    password_hash = str(_secret("viewer_password_hash", "")).strip()
    cookie_key = str(_secret("cookie_key", "")).strip()
    if not username or not password_hash or not cookie_key:
        st.error("Viewer access is not configured. Add the [auth] values in Streamlit Secrets.")
        st.stop()

    _render_styles()
    _render_global_scene()
    st.markdown("<div class='portal-note'>AMD ENTERPRISE AI · SECURE TEAM VIEW</div>", unsafe_allow_html=True)

    remember = st.checkbox("Remember this trusted device for 30 days", value=False)
    credentials = {
        "usernames": {
            username: {
                "name": str(_secret("viewer_name", "Team Viewer")),
                "password": password_hash,
                "roles": ["viewer"],
            }
        }
    }
    authenticator = stauth.Authenticate(
        credentials,
        str(_secret("cookie_name", "amd_eai_viewer")),
        cookie_key,
        30 if remember else 0,
        auto_hash=False,
    )
    authenticator.login(
        location="main",
        max_login_attempts=5,
        fields={"Form name": "Team View", "Username": "Username", "Password": "Password", "Login": "Sign in"},
    )

    status = st.session_state.get("authentication_status")
    if status is False:
        st.error("Username or password is incorrect.")
    if status is not True:
        st.stop()
    if "viewer" not in (st.session_state.get("roles") or []):
        st.error("This account does not have viewer access.")
        st.stop()
    st.markdown(
        """
        <style>
        .amd-login-world,.portal-note,[data-testid="stCheckbox"]{display:none!important}
        .main .block-container{max-width:100%!important;margin:0!important;padding:0!important;background:transparent!important;border:0!important;border-radius:0!important;box-shadow:none!important}
        .main .block-container:before{display:none!important}
        </style>
        """,
        unsafe_allow_html=True,
    )
    with st.container(key="viewer_logout"):
        authenticator.logout("Sign out", location="main", key="amd_viewer_logout")
    return {"username": username, "role": "viewer"}
