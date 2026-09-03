# AMD Intelligent Cloud Control

An executive command center and engineering control plane for an AMD-powered edge AI environment. The platform connects a live Ryzen AI laptop, ROCm/PyTorch telemetry, a local Kubernetes AI control plane, and a secure Streamlit Cloud experience through one truthful operating view.

> **Leadership objective:** demonstrate how enterprise AI can be governed from strategy to silicon—combining executive visibility, secure edge connectivity, model-serving infrastructure, and a staged path to AMD AI Workbench and Resource Manager.

## Executive overview

AMD Intelligent Cloud Control turns a developer laptop into a transparent enterprise AI laboratory. It separates the hosted visualization layer from the secured edge runtime, reports verified services as live, and keeps planned capabilities visibly distinct from deployed infrastructure.

The command center provides:

- A single-page neural compute map showing the flow from cloud experience to edge compute and AI services.
- Live ROCm, PyTorch, Radeon, Supervisor, and Kubernetes operating status.
- Secure laptop connectivity through an authenticated Supervisor and persistent Tailscale Funnel.
- AIM Engine and KServe control-plane visibility for Kubernetes-native model lifecycle management.
- Governed launch points for AI Workbench, Resource Manager, models, and agents as those applications become reachable.
- A leadership-ready roadmap that distinguishes validated, deployed, staged, and hardware-gated capabilities.

## Architecture

```text
Executive / Engineering User
            |
            v
Streamlit Cloud Command Center
            |
            v
Tailscale Funnel -- bearer-token boundary
            |
            v
AMD Edge Supervisor (localhost:8765)
       |                     |
       v                     v
ROCm + PyTorch          Docker Desktop
Radeon 840M                  |
                             v
                    Kubernetes Control Plane
                    |        |          |
                    v        v          v
               AIM Engine  KServe   cert-manager
                    |
                    v
      AI Workbench / Resource Manager / Models / Agents
```

The public Streamlit application is the **operations center**, not the compute host. Workloads and platform services remain on the laptop Kubernetes cluster; the dashboard receives authenticated health data and exposes application links only after the corresponding service is deployed and reachable.

## Verified deployment state

### Live and validated

- AMD Ryzen AI 5 PRO 435 with Radeon 840M (`gfx1153`).
- ROCm 7.14.60850 and PyTorch 2.12 with ROCm/HIP execution.
- Streamlit Cloud command center at `amdeai.streamlit.app`.
- Authenticated AMD Edge Supervisor on local port `8765`.
- Persistent Tailscale Funnel using a stable `ts.net` HTTPS endpoint.
- Docker Desktop Kubernetes single-node control plane.
- cert-manager and Kubernetes Gateway API resources.
- AIM Engine controller built from the AMD source line and running in `aim-system`.
- AIM custom resources, including the repaired and established `AIMArtifact` definition.
- KServe controllers for Kubernetes-native inference orchestration.
- CloudNativePG operator and a healthy single-instance AI Workbench PostgreSQL cluster.
- Persistent `hostpath` database and WAL volumes sized for the laptop lab.
- MinIO object storage with a persistent volume and validated management console.
- Keycloak 26.7.2 backed by PostgreSQL, with the `airm` realm, Workbench OIDC client,
  and `Platform Administrator` role.

### Next deployment wave

- AMD AI Workbench API and UI, with a pinned local deployment profile and authenticated callback configuration.
- AMD Resource Manager API, UI, RabbitMQ, and cluster agent.
- Bond 001, a governed local operations agent using native Windows Ollama and an initial Phi-4 Mini 3.8B quantized model.

These services remain labelled **staged**, **not deployed**, or **planned** in the dashboard until runtime checks prove that they are available. Repository links are source references; they are not presented as application UIs.

## Platform responsibilities

| Component | Operating responsibility |
|---|---|
| Streamlit Cloud | Executive visualization, architecture, status, and controlled application access |
| Tailscale Funnel | Stable encrypted public route to the edge without exposing the laptop address |
| AMD Edge Supervisor | Authenticated telemetry, health, benchmark, and integration boundary |
| ROCm + PyTorch | AMD GPU compute runtime and tensor execution layer |
| Docker Desktop + Kubernetes | Local container and orchestration foundation |
| AIM Engine | Kubernetes controller for AMD inference lifecycle resources |
| KServe | Model-serving control plane used to create and manage inference workloads |
| AI Workbench | Workspace, project, job, model, and experiment experience |
| Resource Manager | Multi-cluster resource governance, inventory, and policy layer |
| Keycloak | Identity, single sign-on, roles, and access control |
| PostgreSQL / MinIO | Application records and model/artifact persistence |
| Ollama | Native Windows inference runtime selected for measured Radeon/Vulkan compatibility |
| Bond 001 | Approval-gated local assistant that cannot mutate the laptop or cluster without an allow-listed tool |

## Security and trust boundaries

- Credentials are never committed to Git.
- Streamlit secrets hold the Supervisor URL and bearer token.
- The Supervisor binds locally; Tailscale provides the controlled HTTPS ingress path.
- Dashboard state is derived from runtime evidence, not hard-coded success labels.
- Application launch links are enabled only for deployed, tested endpoints.
- Kubernetes namespaces, service accounts, RBAC, and CRDs isolate platform responsibilities.

Expected Streamlit secrets:

```toml
AMD_API_URL = "https://your-stable-ts-endpoint"
AMD_API_TOKEN = "replace-with-a-rotated-secret"
```

Do not commit `.streamlit/secrets.toml`, tokens, package credentials, or identity-provider secrets.

## Run the command center locally

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run streamlit_app.py
```

Open `http://localhost:8501`. The authenticated Supervisor is started separately through the published Windows startup script and is designed to recover at user logon.

## Operational validation

The platform is considered healthy only when all applicable checks pass:

1. Docker Desktop reports Kubernetes `Ready`.
2. AIM Engine, KServe, and cert-manager pods report `Running` and ready.
3. The Supervisor health endpoint responds successfully with valid authentication.
4. Tailscale Funnel reports the stable public route to port `8765`.
5. Streamlit displays the edge node online and reports compute health separately.
6. Application buttons open real UIs only after their services and routes pass health checks.

## Repository structure

## Dell Supervisor

The authenticated Supervisor serves system telemetry even when ROCm cannot be
initialized, so a GPU-runtime fault does not falsely mark the entire Dell edge
node offline. Its status response reports `compute_state` separately. The
startup script is registered on the Dell as the `AMD Edge Supervisor` Windows
logon task and is published in this repository for reproducibility.

- `streamlit_app.py` — hosted command-center application.
- `agent/supervisor.py` — authenticated Dell/AMD edge Supervisor.
- `scripts/start_supervisor.ps1` — reproducible Windows Supervisor startup.
- `scripts/deploy_aiwb_local.ps1` — idempotent standalone AI Workbench deployment and verification.
- `scripts/setup_bond001.ps1` — native Ollama, model, Bond 001 and logon-task bootstrap.
- `agent/bond001.py` — authenticated local Bond 001 API with no unrestricted operating-system tools.
- `deploy/kubernetes/` — declarative Kubernetes manifests for persistent platform repairs and services.
- `requirements.txt` — Streamlit application dependencies.
- `requirements-agent.txt` — local Supervisor dependencies.

## Upstream AMD and open-source foundations

This project integrates and demonstrates upstream technologies; it does not claim to replace or redistribute them:

- [ROCm](https://github.com/ROCm/ROCm)
- [AMD Enterprise AI applications](https://github.com/amd-enterprise-ai/amd-eai-apps)
- [AIM Build](https://github.com/amd-enterprise-ai/aim-build)
- [AIM Deploy](https://github.com/amd-enterprise-ai/aim-deploy)
- [AIM Engine](https://github.com/amd-enterprise-ai/aim-engine)
- [KServe](https://github.com/kserve/kserve)

## Leadership roadmap

1. **Observe:** maintain truthful edge, ROCm, Kubernetes, and AIM health.
2. **Operate:** deploy AI Workbench with authenticated UI and persistent data services.
3. **Govern:** add Resource Manager, multi-cluster inventory, quotas, and policy controls.
4. **Serve:** publish tested model endpoints through AIM Engine and KServe.
5. **Automate:** introduce a human-approved operations agent for diagnostics and safe remediation.
6. **Scale:** move hardware-gated production inference to supported AMD accelerator infrastructure while retaining the command center as the management experience.

## Prepared execution sequence

Run these from a normal PowerShell terminal where `kubectl` and `helm` are already available:

```powershell
Set-Location "C:\Users\Fady KHELLA\Fady KHELLA Business\AMD EAI\amdai-enterprise-command-center"
& .\scripts\deploy_aiwb_local.ps1
& .\scripts\setup_bond001.ps1
```

AI Workbench is accepted only after its UI and API deployments are ready and their health endpoints respond. Bond 001 is accepted only after Ollama reports a version, the pinned model is present, and `http://127.0.0.1:8766/health` reports both the agent and runtime online.

## Repository positioning (About)

**Recommended GitHub description:**

> Executive AMD edge AI command center unifying ROCm telemetry, secure Tailscale connectivity, Kubernetes, AIM Engine, KServe, AI Workbench, Resource Manager, models, and governed agents.

**Recommended topics:** `amd`, `rocm`, `ryzen-ai`, `enterprise-ai`, `streamlit`, `kubernetes`, `kserve`, `aim-engine`, `ai-workbench`, `edge-ai`, `mlops`, `observability`

## License

MIT. See `LICENSE`.
