# AMD Edge Kubernetes Deployment Assets

This directory contains declarative, non-secret resources used by the AMD Intelligent Cloud Control laptop lab. Runtime credentials are created as Kubernetes Secrets and are deliberately excluded from Git.

## Current assets

- `kubernetes/aim-engine-runtime-access.yaml` persists the Gateway API and KServe permissions required by AIM Engine.
- `kubernetes/keycloak.yaml` deploys the pinned Keycloak identity service and its internal Kubernetes Service. Database and bootstrap credentials must exist before application.

## Verified runtime checkpoint

At the September 1, 2026 checkpoint, the following services were validated on Docker Desktop Kubernetes:

- AIM Engine `1/1 Running` after persistent HTTPRoute and InferenceService RBAC repair.
- KServe and cert-manager controllers running.
- CloudNativePG operator running.
- AI Workbench PostgreSQL cluster healthy with persistent data and WAL volumes.
- MinIO running with persistent object storage and a validated console.
- Keycloak 26.7.2 running with PostgreSQL, health probes, an `airm` realm, an `aiwb-ui` OIDC client, and a `Platform Administrator` role.

AMD AI Workbench and Resource Manager remain pending until their complete dependency and authentication checks pass. The public dashboard must continue to show those applications as not deployed until their real UI and API endpoints are validated.

## Security rule

Never commit bearer tokens, database passwords, MinIO credentials, Keycloak client secrets, session secrets, generated realm exports containing credentials, or local `.env`/Streamlit secret files.
