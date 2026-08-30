"""Full-screen AMD Enterprise AI command-center shell."""
from __future__ import annotations

from pathlib import Path
import html
import requests
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="AMD Enterprise AI", page_icon="◆", layout="wide")

def sec(name: str) -> str:
    try: return str(st.secrets.get(name, "")).strip()
    except Exception: return ""

root = Path(__file__).resolve().parent
api_url, api_token = sec("AMD_API_URL").rstrip("/"), sec("AMD_API_TOKEN")
token_file = root / "data" / "supervisor-token.txt"
if not api_url and token_file.exists():
    api_url, api_token = "http://127.0.0.1:8765", token_file.read_text(encoding="utf-8").strip()

def telemetry() -> dict:
    if not api_url: return {"state":"offline","reason":"Secure laptop tunnel is not configured"}
    headers = {"Authorization": f"Bearer {api_token}"}
    if sec("CF_ACCESS_CLIENT_ID") and sec("CF_ACCESS_CLIENT_SECRET"):
        headers.update({"CF-Access-Client-Id":sec("CF_ACCESS_CLIENT_ID"),"CF-Access-Client-Secret":sec("CF_ACCESS_CLIENT_SECRET")})
    try:
        reply=requests.get(api_url+"/api/status",headers=headers,timeout=6); reply.raise_for_status(); return reply.json()
    except Exception as exc: return {"state":"offline","reason":str(exc)[:150]}

s=telemetry(); online=s.get("state")=="online"
def val(key, default): return html.escape(str(s.get(key,default)))
gpu=val("gpu_name","AMD Radeon 840M Graphics"); arch=val("architecture","gfx1153")
hip=val("hip_version","7.14"); torch=val("pytorch_version","2.12")
cpu=max(0,min(100,round(float(s.get("cpu_percent",0))))); mem=max(0,min(100,round(float(s.get("memory_percent",0)))))
gpup=max(0,min(100,round(float(s.get("gpu_percent",0))))); state="ONLINE" if online else "OFFLINE"
reason=val("reason","Protected Supervisor connected")

st.markdown("""<style>.block-container{padding:0!important;max-width:100%!important}iframe{border:0!important}
[data-testid=stHeader],[data-testid=stToolbar],[data-testid=stDecoration],[data-testid=stAppDeployButton],#MainMenu,footer{display:none!important}</style>""",unsafe_allow_html=True)

shell=r'''
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap');
:root{--bg:#030504;--panel:#0a0e0b;--panel2:#0d120e;--line:#253027;--gold:#d7b542;--hi:#ffe873;--green:#37dc78;--red:#ff5d68;--blue:#438fff;--ink:#f5f7f2;--muted:#89a092;--faint:#506159;--mono:'IBM Plex Mono',monospace;--body:'DM Sans',sans-serif}
*{box-sizing:border-box}html,body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--body)}button{font:inherit}.app{min-height:1050px;background:radial-gradient(circle at 72% -25%,#201a07 0,transparent 37%),var(--bg)}
.rail{position:fixed;left:0;top:0;bottom:0;width:76px;background:#040706;border-right:1px solid var(--line);display:flex;flex-direction:column;align-items:center;padding:13px 7px;z-index:20}.logo{width:47px;height:47px;color:var(--hi);margin-bottom:18px}.logo svg{width:100%;height:100%}.nav{width:60px;min-height:58px;border:1px solid transparent;border-radius:10px;background:none;color:var(--faint);display:flex;flex-direction:column;align-items:center;justify-content:center;gap:4px;margin:2px 0;cursor:pointer}.nav svg{width:19px;height:19px;fill:none;stroke:currentColor;stroke-width:1.6}.nav span{font:500 7px var(--mono);text-transform:uppercase}.nav:hover{color:var(--hi);background:#11150f}.nav.active{color:var(--hi);border-color:#464128;background:#15170e;box-shadow:inset 3px 0 var(--gold)}.space{flex:1}
.main{margin-left:76px}.top{height:70px;border-bottom:1px solid var(--line);display:flex;align-items:center;justify-content:space-between;padding:0 28px 0 36px;background:rgba(4,8,6,.91);position:sticky;top:0;z-index:10}.brand{display:flex;align-items:center;gap:12px}.brand svg{width:28px;height:28px;color:var(--hi)}.brand h1{font-size:16px;margin:0}.brand h1 b{color:var(--hi)}.crumb{font:9px var(--mono);letter-spacing:.16em;color:var(--faint);text-transform:uppercase;margin-top:2px}.topright{display:flex;align-items:center;gap:8px}.pill{border:1px solid var(--line);border-radius:999px;padding:7px 11px;font:9px var(--mono);color:#9aaba0;background:#09100b}.pill i{display:inline-block;width:6px;height:6px;border-radius:50%;background:var(--faint);margin-right:7px}.pill.live{color:var(--green)}.pill.live i{background:var(--green);box-shadow:0 0 9px #37dc78}.pill.off{color:var(--red)}.pill.off i{background:var(--red);box-shadow:0 0 9px #ff5d68}
.view{display:none;padding:28px 36px 65px}.view.active{display:block}.intro{display:flex;justify-content:space-between;align-items:end;margin-bottom:20px}.intro h2{font-size:24px;margin:0 0 6px}.intro p{font-size:13px;line-height:1.65;color:#a0b2a6;max-width:850px;margin:0}.stamp{font:9px var(--mono);color:var(--faint)}.sect{font:600 10px var(--mono);letter-spacing:.18em;text-transform:uppercase;border-left:3px solid var(--gold);padding-left:9px;margin:20px 0 12px;color:#c6d2ca}
.g5{display:grid;grid-template-columns:repeat(5,1fr);gap:13px}.g4{display:grid;grid-template-columns:repeat(4,1fr);gap:13px}.g3{display:grid;grid-template-columns:repeat(3,1fr);gap:13px}.g2{display:grid;grid-template-columns:repeat(2,1fr);gap:13px}.card{background:linear-gradient(145deg,#0b100d,#080b09);border:1px solid var(--line);border-radius:12px;padding:16px;min-width:0}.kpi{height:87px}.kpi strong{display:block;font:600 25px var(--mono);color:var(--hi);margin:2px 0 8px}.kpi small,.label{font:9px var(--mono);letter-spacing:.09em;color:var(--faint);text-transform:uppercase}.green strong{color:var(--green)}.blue strong{color:var(--blue)}
.statusline{display:flex;gap:9px;align-items:center;margin-bottom:11px}.btn{border:1px solid #35523b;background:#0b1710;color:var(--green);padding:8px 12px;border-radius:7px;font:10px var(--mono)}.btn.gold{color:var(--hi);border-color:#5b5128;background:#171408}.btn:disabled{opacity:.4}.console{background:#07100b;border:1px solid #284231;border-radius:8px;padding:13px;color:#79aa8b;font:10px/1.55 var(--mono);white-space:pre-wrap;min-height:128px}.feature h3{font-size:14px;margin:0 0 5px}.tag{float:right;border:1px solid #31593a;color:var(--green);border-radius:999px;padding:3px 7px;font:8px var(--mono)}.tag.pending{color:var(--hi);border-color:#564c28}.tag.off{color:#ff8088;border-color:#563238}.feature p{color:#83a08e;font:10px/1.55 var(--mono);min-height:48px}.rows{border-top:1px solid #1e2821;padding-top:9px}.row{display:flex;justify-content:space-between;padding:4px 0;color:#87a292;font:10px var(--mono)}.row b{color:#f5f7f2}.bar{height:8px;border-radius:8px;background:#182019;overflow:hidden;margin-top:10px}.bar i{display:block;height:100%;background:linear-gradient(90deg,#8d741e,var(--hi));box-shadow:0 0 12px #d7b54266}
.topology{display:flex;align-items:center;gap:12px}.node{flex:1;text-align:center;border:1px solid #3c3925;border-radius:12px;background:#0a0e0b;padding:20px}.node h3{margin:0 0 6px}.node p{font:9px var(--mono);color:var(--muted)}.link{font:22px var(--mono);color:var(--gold)}.apps{display:grid;grid-template-columns:repeat(3,1fr);gap:13px}.appcard{position:relative;overflow:hidden}.appcard:before{content:'';position:absolute;inset:0 auto 0 0;width:3px;background:var(--gold)}.appcard h3{margin:4px 0}.appcard p{font-size:12px;line-height:1.5;color:var(--muted);min-height:54px}.chart{height:210px;width:100%}.chart line{stroke:#1f2922}.chart polyline{fill:none;stroke:var(--gold);stroke-width:2}
@media(max-width:1100px){.g5,.g4,.apps{grid-template-columns:repeat(2,1fr)}}
</style>
<div class="app"><aside class="rail"><div class="logo"><svg viewBox="0 0 48 48" aria-label="AMD"><path d="M6 7h19v7H13v12H6V7zm22 0h14v14h-7v-7h-7V7zM22 27h13V14h7v20H29v7h-7V27zM6 29h7v12H6V29z" fill="currentColor"/></svg></div>
<button class="nav active" data-v="overview"><svg viewBox="0 0 24 24"><rect x="3" y="3" width="8" height="8"/><rect x="13" y="3" width="8" height="5"/><rect x="13" y="10" width="8" height="11"/><rect x="3" y="13" width="8" height="8"/></svg><span>Overview</span></button>
<button class="nav" data-v="topology"><svg viewBox="0 0 24 24"><circle cx="5" cy="12" r="2"/><circle cx="19" cy="6" r="2"/><circle cx="19" cy="18" r="2"/><path d="m7 12 10-5m-10 5 10 5"/></svg><span>Topology</span></button>
<button class="nav" data-v="gpu"><svg viewBox="0 0 24 24"><rect x="3" y="6" width="18" height="12" rx="2"/><path d="M7 6V3m5 3V3m5 3V3M7 21v-3m5 3v-3m5 3v-3"/></svg><span>ROCm</span></button>
<button class="nav" data-v="aims"><svg viewBox="0 0 24 24"><path d="M4 18V8l8-5 8 5v10l-8 3-8-3zM8 10h8M8 14h8"/></svg><span>AIMs</span></button>
<button class="nav" data-v="workbench"><svg viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 9h18M8 9v11"/></svg><span>Workbench</span></button>
<button class="nav" data-v="models"><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"/><circle cx="4" cy="5" r="1.5"/><circle cx="20" cy="5" r="1.5"/><circle cx="4" cy="19" r="1.5"/><circle cx="20" cy="19" r="1.5"/><path d="M9.5 10 5 6m9.5 4L19 6M9.5 14 5 18m9.5-4 4.5 4"/></svg><span>Models</span></button>
<button class="nav" data-v="agents"><svg viewBox="0 0 24 24"><rect x="4" y="4" width="7" height="7"/><rect x="13" y="4" width="7" height="7"/><rect x="4" y="13" width="7" height="7"/><rect x="13" y="13" width="7" height="7"/></svg><span>Agents</span></button><div class="space"></div>
<button class="nav" data-v="about"><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M12 11v6m0-10v1"/></svg><span>About</span></button></aside>
<main class="main"><header class="top"><div class="brand"><svg viewBox="0 0 48 48"><path d="M6 7h19v7H13v12H6V7zm22 0h14v14h-7v-7h-7V7zM22 27h13V14h7v20H29v7h-7V27zM6 29h7v12H6V29z" fill="currentColor"/></svg><div><h1>AMD <b>Enterprise AI</b></h1><div class="crumb">ROCm · Radeon · agentic edge infrastructure</div></div></div><div class="topright"><span class="pill STATECLASS"><i></i>EDGE NODE STATE</span><span class="pill">APP-TRACKED GPU HOURS</span><span class="pill">RADEON 840M · ARCH</span></div></header>
<section class="view active" id="overview"><div class="intro"><div><h2>AMD Command Center</h2><p>A live operating surface for the Radeon edge node, ROCm compute, model operations and future Enterprise AI infrastructure. Live and planned capabilities are identified explicitly.</p></div><div class="stamp">EDGE NODE 01 · STATE</div></div><div class="sect">System status</div><div class="g5"><div class="card kpi STATEKPI"><strong>STATE</strong><small>GPU backend</small></div><div class="card kpi"><strong>840M</strong><small>Radeon GPU</small></div><div class="card kpi blue"><strong>HIP</strong><small>ROCm / HIP</small></div><div class="card kpi green"><strong>GPUP%</strong><small>GPU utilization</small></div><div class="card kpi"><strong>0.0 / 30</strong><small>GPU hours tracked</small></div></div>
<div class="card" style="margin-top:13px"><div class="statusline"><span class="pill STATECLASS"><i></i>AMD SUPERVISOR STATE</span><button class="btn" disabled>Recheck now</button></div><div class="console">AMD EDGE SUPERVISOR
------------------------------------------------------------
GPU           GPU
Architecture  ARCH
ROCm / HIP    HIP
PyTorch       TORCH
CPU load      CPU%
Memory load   MEM%
State         STATE
Detail        REASON</div></div>
<div class="sect">What's real vs. pending</div><div class="g4"><div class="card feature"><span class="tag">CONFIRMED</span><h3>ROCm + PyTorch</h3><p>Real Radeon compute through the isolated Python environment.</p><div class="rows"><div class="row"><span>device</span><b>GPU</b></div><div class="row"><span>HIP</span><b>HIP</b></div></div></div><div class="card feature"><span class="tag">READY</span><h3>GPU benchmark</h3><p>Protected matrix benchmark exposed by the local Supervisor.</p><div class="rows"><div class="row"><span>endpoint</span><b>/api/benchmark</b></div></div></div><div class="card feature"><span class="tag pending">ON DEMAND</span><h3>Four-model catalog</h3><p>Four quantized slots, with one substantial model loaded at a time.</p><div class="rows"><div class="row"><span>installed</span><b>0 / 4</b></div></div></div><div class="card feature"><span class="tag pending">PLANNED</span><h3>Agent orchestration</h3><p>Coordinator, ROCm, research and code agents.</p><div class="rows"><div class="row"><span>state</span><b>runtime pending</b></div></div></div></div></section>
<section class="view" id="topology"><div class="intro"><div><h2>Compute Topology</h2><p>Control plane, secure edge transport and future enterprise infrastructure.</p></div></div><div class="topology"><div class="node"><h3>Streamlit Cloud</h3><p>amdeai.streamlit.app</p></div><div class="link">⇄</div><div class="node"><h3>Cloudflare Access</h3><p>secure tunnel</p></div><div class="link">⇄</div><div class="node"><h3>Edge Node 01</h3><p>Radeon 840M · STATE</p></div><div class="link">⇄</div><div class="node"><h3>Enterprise Cluster</h3><p>supported AMD GPU · future</p></div></div></section>
<section class="view" id="gpu"><div class="intro"><div><h2>ROCm GPU Operations</h2><p>Live telemetry from the protected AMD Supervisor.</p></div></div><div class="g4"><div class="card kpi"><strong>GPUP%</strong><small>GPU load</small><div class="bar"><i style="width:GPUP%"></i></div></div><div class="card kpi"><strong>CPU%</strong><small>CPU load</small><div class="bar"><i style="width:CPU%"></i></div></div><div class="card kpi"><strong>MEM%</strong><small>Memory load</small><div class="bar"><i style="width:MEM%"></i></div></div><div class="card kpi"><strong>ARCH</strong><small>GPU architecture</small></div></div><div class="card" style="margin-top:13px"><div class="sect">Telemetry history</div><svg class="chart" viewBox="0 0 900 210" preserveAspectRatio="none"><line x1="0" y1="52" x2="900" y2="52"/><line x1="0" y1="105" x2="900" y2="105"/><line x1="0" y1="158" x2="900" y2="158"/><polyline points="0,185 150,185 300,185 450,185 600,185 750,185 900,185"/></svg><div class="stamp">Historical storage activates in the observability phase</div></div></section>
<section class="view" id="aims"><div class="intro"><div><h2>AMD Inference Microservices</h2><p>AIM catalog and future deployment launchpad. Production AIM runtimes require supported AMD infrastructure.</p></div></div><div class="apps"><div class="card appcard"><span class="tag off">NOT INSTALLED</span><h3>Chat AIM</h3><p>OpenAI-compatible chat and generation service.</p><button class="btn gold" disabled>Deploy AIM</button></div><div class="card appcard"><span class="tag off">NOT INSTALLED</span><h3>Embedding AIM</h3><p>Vector embeddings for retrieval and enterprise search.</p><button class="btn gold" disabled>Deploy AIM</button></div><div class="card appcard"><span class="tag off">NOT INSTALLED</span><h3>Reranking AIM</h3><p>Search relevance and retrieval optimization.</p><button class="btn gold" disabled>Deploy AIM</button></div></div></section>
<section class="view" id="workbench"><div class="intro"><div><h2>AI Workbench</h2><p>Development and evaluation workspaces, with future cluster-backed integration.</p></div></div><div class="g3"><div class="card feature"><span class="tag">LOCAL</span><h3>VS Code</h3><p>Primary repository and development workspace on the laptop.</p></div><div class="card feature"><span class="tag pending">NEXT</span><h3>JupyterLab</h3><p>Notebook experiments and ROCm model benchmarks.</p></div><div class="card feature"><span class="tag off">FUTURE</span><h3>Enterprise Workbench</h3><p>Official experience when supported infrastructure is connected.</p></div></div></section>
<section class="view" id="models"><div class="intro"><div><h2>Model Registry</h2><p>Four quantized model slots; runtime selection follows real Radeon benchmarks.</p></div></div><div class="g4">MODELCARDS</div></section>
<section class="view" id="agents"><div class="intro"><div><h2>Agent Operations</h2><p>Four-agent edge orchestration activates after the inference runtime.</p></div></div><div class="g4">AGENTCARDS</div></section>
<section class="view" id="about"><div class="intro"><div><h2>Platform Boundaries</h2><p>Live laptop capabilities are separated from future enterprise-cluster services.</p></div></div><div class="g2"><div class="card"><h3>Live edge plane</h3><p>Windows 11 · Radeon 840M · ROCm/PyTorch · AMD Supervisor.</p></div><div class="card"><h3>Future enterprise plane</h3><p>Kubernetes · AIM Engine · AIM containers · AI Workbench · supported AMD accelerators.</p></div></div></section>
</main></div><script>document.querySelectorAll('.nav').forEach(b=>b.onclick=()=>{document.querySelectorAll('.nav,.view').forEach(x=>x.classList.remove('active'));b.classList.add('active');document.getElementById(b.dataset.v).classList.add('active');scrollTo(0,0)})</script>
'''

models="".join(f'<div class="card feature"><span class="tag off">NOT INSTALLED</span><h3>Model {n:02}</h3><p>Quantized edge model; role selected after benchmarking.</p><div class="rows"><div class="row"><span>loaded</span><b>no</b></div></div></div>' for n in range(1,5))
agents="".join(f'<div class="card feature"><span class="tag pending">PLANNED</span><h3>{n}</h3><p>{r}</p><div class="rows"><div class="row"><span>state</span><b>waiting</b></div></div></div>' for n,r in [("Coordinator","Task and model routing"),("ROCm Operator","GPU health and benchmarks"),("Research","Retrieval and synthesis"),("Code","Local development assistance")])
for old,new in [("STATECLASS","live" if online else "off"),("STATEKPI","green" if online else ""),("MODELCARDS",models),("AGENTCARDS",agents),("REASON",reason),("TORCH",torch),("ARCH",arch),("HIP",hip),("GPUP",str(gpup)),("CPU",str(cpu)),("MEM",str(mem)),("GPU",gpu),("STATE",state)]: shell=shell.replace(old,new)
components.html(shell,height=1050,scrolling=True)
