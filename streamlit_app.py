"""AMD AI Command Center — cloud UI for a laptop ROCm node and future EAI cluster."""

from __future__ import annotations

import time
from datetime import datetime, timezone

import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st


st.set_page_config(page_title="AMD AI Command Center", page_icon="🟧", layout="wide")


def get_secret(name: str) -> str:
    try:
        return str(st.secrets.get(name, "")).strip()
    except Exception:
        return ""


API_URL = get_secret("AMD_API_URL").rstrip("/")
API_TOKEN = get_secret("AMD_API_TOKEN")
CF_CLIENT_ID = get_secret("CF_ACCESS_CLIENT_ID")
CF_CLIENT_SECRET = get_secret("CF_ACCESS_CLIENT_SECRET")


def request_headers() -> dict[str, str]:
    output = {"Accept": "application/json"}
    if API_TOKEN:
        output["Authorization"] = f"Bearer {API_TOKEN}"
    if CF_CLIENT_ID and CF_CLIENT_SECRET:
        output["CF-Access-Client-Id"] = CF_CLIENT_ID
        output["CF-Access-Client-Secret"] = CF_CLIENT_SECRET
    return output


def call_api(method: str, path: str, timeout: int = 12, **kwargs):
    if not API_URL:
        raise RuntimeError("Laptop tunnel is not configured")
    response = requests.request(
        method,
        f"{API_URL}{path}",
        headers=request_headers(),
        timeout=timeout,
        **kwargs,
    )
    response.raise_for_status()
    return response.json()


@st.cache_data(ttl=10, show_spinner=False)
def fetch_status():
    started = time.perf_counter()
    payload = call_api("GET", "/api/status")
    payload["dashboard_roundtrip_ms"] = (time.perf_counter() - started) * 1000
    return payload


def gauge(value: float, title: str, color: str = "#ff5c00"):
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=value,
            number={"suffix": "%"},
            title={"text": title},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": color},
                "steps": [
                    {"range": [0, 70], "color": "rgba(255,255,255,.06)"},
                    {"range": [70, 90], "color": "rgba(255,170,0,.16)"},
                    {"range": [90, 100], "color": "rgba(255,50,50,.20)"},
                ],
            },
        )
    )
    fig.update_layout(height=225, margin=dict(l=20, r=20, t=55, b=10), paper_bgcolor="rgba(0,0,0,0)")
    return fig


st.markdown(
    """
    <style>
      :root {--amd:#ff5c00; --panel:rgba(255,255,255,.045);}
      .block-container {max-width:1500px; padding-top:1.25rem;}
      [data-testid="stSidebar"] {border-right:1px solid rgba(255,92,0,.24);}
      .hero {border:1px solid rgba(255,92,0,.42); border-radius:20px; padding:1.35rem 1.6rem;
        background:linear-gradient(125deg,rgba(255,92,0,.20),rgba(45,15,5,.14),rgba(8,10,17,.92));}
      .hero h1 {margin:0;font-size:2.05rem;letter-spacing:-.025em}.hero p{margin:.35rem 0 0;opacity:.72}
      .badge {display:inline-block;padding:.22rem .58rem;border-radius:999px;margin-right:.35rem;
        border:1px solid rgba(255,92,0,.45);font-size:.78rem;color:#ffb088}
      .card {border:1px solid rgba(255,255,255,.10);border-radius:16px;padding:1rem 1.1rem;
        background:var(--panel);min-height:145px}.card h3{margin:.1rem 0 .45rem}.muted{opacity:.66}
      .planned {color:#ffb35c}.live {color:#55d98b}.offline {color:#ff6c6c}
    </style>
    <div class="hero">
      <span class="badge">ROCm 7.14</span><span class="badge">PyTorch 2.12</span><span class="badge">gfx1153</span>
      <h1>🟧 AMD AI Command Center</h1>
      <p>Radeon edge observability today · AIM and AI Workbench control plane tomorrow</p>
    </div>
    """,
    unsafe_allow_html=True,
)

menu = st.sidebar.radio(
    "Command Center",
    [
        "◉ Executive Overview",
        "◈ ROCm Observability",
        "▦ AIM Catalog",
        "▣ AI Workbench",
        "⬡ Architecture",
        "✓ Deployment Roadmap",
    ],
)
st.sidebar.caption("AMD Ryzen AI 5 PRO 435\n\nRadeon 840M · 32 GB shared memory")

status = None
connection_error = ""
if API_URL:
    try:
        status = fetch_status()
    except Exception as exc:
        connection_error = str(exc)


if menu == "◉ Executive Overview":
    st.subheader("Enterprise AI estate")
    if status:
        st.success("Radeon laptop connected through the secured telemetry service")
    elif API_URL:
        st.error("Radeon laptop is currently offline")
        st.caption(connection_error)
    else:
        st.warning("Radeon laptop tunnel is not configured yet")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Edge accelerator", (status or {}).get("gpu_name", "Radeon 840M"))
    c2.metric("ROCm / HIP", (status or {}).get("hip_version", "7.14 installed"))
    c3.metric("PyTorch", (status or {}).get("pytorch_version", "2.12 installed"))
    c4.metric("Laptop state", "ONLINE" if status else "OFFLINE")

    st.write("")
    left, middle, right = st.columns(3)
    left.markdown(
        '<div class="card"><h3>🟢 Edge ROCm node</h3><p class="live">Installed</p>'
        '<p class="muted">Windows 11 · Ryzen AI 5 PRO 435 · Radeon 840M · isolated Python environment</p></div>',
        unsafe_allow_html=True,
    )
    middle.markdown(
        '<div class="card"><h3>🟠 Secure remote control</h3><p class="planned">Next milestone</p>'
        '<p class="muted">Authenticated laptop API behind an outbound-only Cloudflare Tunnel.</p></div>',
        unsafe_allow_html=True,
    )
    right.markdown(
        '<div class="card"><h3>🔵 Enterprise cluster</h3><p class="planned">Planned</p>'
        '<p class="muted">AIM Engine, AI Workbench and Resource Manager require supported server hardware.</p></div>',
        unsafe_allow_html=True,
    )

    st.subheader("Capability matrix")
    st.dataframe(
        pd.DataFrame(
            [
                ["ROCm PyTorch", "Installed", "Laptop", "Live GPU computation"],
                ["ROCm observability", "In progress", "Laptop + portal", "Metrics and benchmark history"],
                ["Secure remote inference", "Planned next", "Cloudflare Tunnel", "Authenticated API"],
                ["AIM Catalog", "UI preview", "Supported cluster required", "Model discovery and profiles"],
                ["AMD AI Workbench", "UI preview", "Supported cluster required", "Workspaces and deployments"],
                ["AMD Resource Manager", "Roadmap", "Supported cluster required", "Projects, quotas and governance"],
            ],
            columns=["Capability", "State", "Execution plane", "Purpose"],
        ),
        hide_index=True,
        use_container_width=True,
    )

elif menu == "◈ ROCm Observability":
    st.subheader("Radeon 840M · live ROCm operations")
    if status:
        g1, g2, g3 = st.columns(3)
        g1.plotly_chart(gauge(float(status.get("cpu_percent", 0)), "CPU"), use_container_width=True)
        g2.plotly_chart(gauge(float(status.get("memory_percent", 0)), "System memory", "#ff9e2a"), use_container_width=True)
        g3.plotly_chart(gauge(float(status.get("gpu_percent", 0)), "Radeon compute", "#e63b2e"), use_container_width=True)

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Architecture", status.get("architecture", "gfx1153"))
        m2.metric("GPU available", "Yes" if status.get("gpu_available") else "No")
        m3.metric("Temperature", f"{status.get('gpu_temperature_c', 0):.0f} °C" if status.get("gpu_temperature_c") else "Driver unavailable")
        m4.metric("Round trip", f"{status.get('dashboard_roundtrip_ms', 0):.0f} ms")
    else:
        st.info("Connect the laptop API to replace this installed-state view with live telemetry.")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Architecture", "gfx1153")
        m2.metric("GPU", "Radeon 840M")
        m3.metric("ROCm", "7.14.0")
        m4.metric("PyTorch", "2.12.0")

    st.subheader("Remote compute validation")
    matrix_size = st.select_slider("Matrix size", [512, 1024, 2048, 4096], value=2048)
    if st.button("Run Radeon matrix benchmark", type="primary", disabled=not bool(status)):
        try:
            result = call_api("POST", "/api/benchmark", timeout=60, json={"matrix_size": matrix_size})
            st.success("ROCm calculation completed on the laptop")
            a, b, c = st.columns(3)
            a.metric("GPU time", f"{result['gpu_seconds']:.3f} s")
            b.metric("Device", result["device"])
            c.metric("Shape", result["shape"])
        except Exception as exc:
            st.error(str(exc))

    with st.expander("Installed ROCm library inventory", expanded=True):
        libraries = (status or {}).get(
            "libraries",
            {
                "torch": "2.12.0+rocm7.14.0",
                "rocm": "7.14.0",
                "rocm-sdk-core": "7.14.0",
                "rocm-sdk-libraries": "7.14.0",
                "amd-torch-device-gfx1153": "2.12.0+rocm7.14.0",
            },
        )
        st.json(libraries)

elif menu == "▦ AIM Catalog":
    st.subheader("AMD Inference Microservices")
    st.warning("Catalog preview only — no AIM runtime is installed on the Radeon 840M laptop.")
    st.caption("AIM deployments will become active after connecting a supported Instinct or Radeon Pro Kubernetes cluster.")

    models = pd.DataFrame(
        [
            ["Llama family", "Chat / generation", "AIM profile required", "Not deployed"],
            ["Mistral family", "Chat / generation", "AIM profile required", "Not deployed"],
            ["Embedding models", "Retrieval", "AIM profile required", "Not deployed"],
            ["Rerankers", "Search relevance", "AIM profile required", "Not deployed"],
        ],
        columns=["Model family", "Task", "Hardware selection", "State"],
    )
    st.dataframe(models, hide_index=True, use_container_width=True)
    selected = st.selectbox("Inspect model family", models["Model family"])
    c1, c2, c3 = st.columns(3)
    c1.metric("Selected", selected)
    c2.metric("Optimization target", "Latency / throughput")
    c3.metric("API standard", "OpenAI compatible")
    st.button("Deploy AIM", disabled=True, help="Requires a compatible AIM Engine cluster")

elif menu == "▣ AI Workbench":
    st.subheader("AI Workbench control plane")
    st.warning("Workbench UI preview — official AMD AI Workbench is not installed on this laptop.")
    tabs = st.tabs(["Workspaces", "Models", "Fine-tuning", "Chat & compare", "Projects"])
    with tabs[0]:
        st.markdown("### Developer workspaces")
        st.dataframe(pd.DataFrame([["JupyterLab", "Planned"], ["VS Code", "Planned"], ["MLflow", "Planned"]], columns=["Workspace", "State"]), hide_index=True)
    with tabs[1]:
        st.markdown("### Model deployments")
        st.info("AIM deployments and OpenAI-compatible endpoints will appear here.")
    with tabs[2]:
        st.markdown("### Training and fine-tuning")
        st.info("Requires supported cluster compute, datasets and project-scoped secrets.")
    with tabs[3]:
        left, right = st.columns(2)
        left.text_area("Model A", "No deployed AIM selected", disabled=True)
        right.text_area("Model B", "No deployed AIM selected", disabled=True)
    with tabs[4]:
        st.dataframe(pd.DataFrame([["edge-lab", "Radeon laptop", "Development"], ["enterprise-cluster", "Not connected", "Planned"]], columns=["Project", "Compute", "State"]), hide_index=True)

elif menu == "⬡ Architecture":
    st.subheader("Platform architecture")
    st.code(
        """amdai.streamlit.app
    |
    +-- Executive overview
    +-- ROCm observability
    +-- AIM and Workbench views
    |
    +-- HTTPS + Cloudflare Access service token
            |
            +-- Cloudflare Tunnel (outbound only)
                    |
                    +-- Windows laptop API (localhost)
                            +-- PyTorch ROCm / HIP
                            +-- Radeon 840M (gfx1153)
                            +-- benchmarks and inference

Future supported Kubernetes cluster
    +-- AMD GPU Operator
    +-- AIM Engine / KServe
    +-- AIM model catalog
    +-- AMD AI Workbench
    +-- AMD Resource Manager
    +-- OpenTelemetry / metrics / logs""",
        language="text",
    )
    st.markdown(
        """
        **Security boundaries**

        - The laptop API binds only to localhost.
        - Cloudflare Tunnel creates the outbound connection; no router port forwarding.
        - Cloudflare Access authenticates the Streamlit service with a revocable service token.
        - Inference actions require a second application bearer token.
        - No Hugging Face, Cloudflare, GitHub or model credentials belong in source control.
        """
    )

else:
    st.subheader("Deployment roadmap")
    roadmap = pd.DataFrame(
        [
            [1, "ROCm 7.14 + PyTorch 2.12 on Radeon 840M", "Complete"],
            [2, "Local visual validation dashboard", "Complete"],
            [3, "AMD cloud command-center repository", "In progress"],
            [4, "Authenticated laptop telemetry/inference API", "Next"],
            [5, "Cloudflare Tunnel and Access policy", "Next"],
            [6, "Live Streamlit observability and remote benchmark", "Planned"],
            [7, "Supported AMD Enterprise AI Kubernetes infrastructure", "Future"],
            [8, "AIM Engine, catalog and AI Workbench integration", "Future"],
        ],
        columns=["Phase", "Deliverable", "State"],
    )
    st.dataframe(roadmap, hide_index=True, use_container_width=True)
    st.caption(f"Roadmap rendered {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")

st.divider()
st.caption("AMD AI Command Center · truthful capability states · secrets never stored in Git")
