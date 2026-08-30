# Architecture

## Planes

### Presentation plane

Streamlit Community Cloud hosts the public command center. It displays laptop ROCm telemetry and, later, Enterprise AI cluster state.

### Edge compute plane

The Dell laptop runs PyTorch through ROCm/HIP on the Radeon 840M. A future localhost-only API will expose read-only status plus explicitly authorized benchmark and inference operations.

### Secure connectivity plane

Cloudflare Tunnel creates an outbound-only connection from the laptop. Cloudflare Access authenticates the cloud application. The laptop API independently verifies a bearer token.

### Enterprise compute plane

A future supported AMD server cluster will host Kubernetes, AMD GPU Operator, AIM Engine, KServe, AIMs, AI Workbench, and Resource Manager. The Ryzen laptop does not pretend to provide this plane.

## Trust boundaries

1. No inbound router port forwarding.
2. The edge API listens only on localhost.
3. Cloudflare service credentials remain in Streamlit Secrets.
4. Application bearer tokens are independently revocable.
5. Mutating operations are separated from read-only telemetry.
6. No secret values are logged or committed.

## Data flow

```text
Browser
  -> Streamlit Community Cloud
      -> Cloudflare Access
          -> Cloudflare Tunnel
              -> Laptop localhost API
                  -> PyTorch ROCm / Radeon 840M
```

The future Enterprise AI cluster is a separate backend with its own identity, API keys, quotas, and observability.
