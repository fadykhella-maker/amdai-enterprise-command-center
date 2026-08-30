# AMD AI Command Center

A cloud command center for an AMD Ryzen AI laptop running ROCm and PyTorch, with a roadmap to integrate AMD Inference Microservices (AIMs), AIM Engine, AMD AI Workbench, and AMD Resource Manager when supported Kubernetes infrastructure is connected.

## Current state

### Installed and validated locally

- AMD Ryzen AI 5 PRO 435
- AMD Radeon 840M (`gfx1153`)
- Windows 11
- Python 3.12 isolated environment
- ROCm 7.14.0
- PyTorch 2.12.0 with ROCm/HIP
- Local Streamlit validation dashboard

### This repository

- Executive AMD estate overview
- ROCm observability UI
- Remote benchmark controls
- AIM Catalog preview
- AI Workbench preview
- Architecture and security boundaries
- Deployment roadmap

### Not yet installed

- Official AMD AI Workbench
- AIM Engine
- AMD Resource Manager
- AMD GPU Operator/Kubernetes reference stack

Those services require supported server infrastructure. The portal labels them as planned and never presents them as active.

## Run locally

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run streamlit_app.py
```

Open `http://localhost:8501`.

## Cloud deployment

Deploy `streamlit_app.py` through Streamlit Community Cloud. The preferred app address is `amdai.streamlit.app` if the name is available.

Live laptop connectivity will use:

1. A localhost-only authenticated telemetry and inference API.
2. A persistent Tailscale Funnel with a stable `ts.net` HTTPS hostname.
3. Application bearer-token authentication at the AMD Supervisor.
4. Restricted secrets configured in Streamlit Community Cloud.

## Repository secrets

Never commit credentials. The application can read these values from Streamlit Secrets after the laptop service exists:

- `AMD_API_URL`
- `AMD_API_TOKEN`
- `CF_ACCESS_CLIENT_ID`
- `CF_ACCESS_CLIENT_SECRET`

## Upstream projects

This project integrates with and documents, but does not claim to replace, these upstream projects:

- [ROCm](https://github.com/ROCm/ROCm)
- [AMD Enterprise AI applications](https://github.com/amd-enterprise-ai/amd-eai-apps)
- [AIM build](https://github.com/amd-enterprise-ai/aim-build)
- [AIM deploy](https://github.com/amd-enterprise-ai/aim-deploy)
- [AIM Engine](https://github.com/amd-enterprise-ai/aim-engine)

## License

MIT. See `LICENSE`.
