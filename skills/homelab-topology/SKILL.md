---
name: homelab-topology
description: Harmony cluster topology — node IPs, roles, service domains, DNS model, and expected state. Load when diagnosing cluster issues, writing workloads, or reasoning about network paths.
category: domain
durability: durable
tier: subject
---

## Nodes

All 3 Talos nodes are control-plane. Every workload requires a control-plane toleration to schedule.

| Node name | Proxmox host IP | Talos VM IP | Talos node ID | GPU |
|---|---|---|---|---|
| manager-01 | 192.168.8.203 | 192.168.8.211 | talos-1102 | — |
| workstation-01 | 192.168.8.201 | 192.168.8.212 | talos-2101 | Yes |
| workstation-02 | 192.168.8.202 | 192.168.8.213 | talos-2201 | Yes |

The Omni VM runs on manager-01's Proxmox host at **192.168.8.210**.

## Service domains

**Management services** (`*.manage.pixeloven.com` → 192.168.8.210, Omni VM Traefik):

| Domain | Service |
|---|---|
| `omni.manage.pixeloven.com` | Sidero Omni dashboard |
| `auth.manage.pixeloven.com` | Authentik SSO |
| `traefik.manage.pixeloven.com` | Omni VM Traefik dashboard |

**Lab services** (`*.lab.pixeloven.com` → Talos VM IPs 192.168.8.211/.212/.213, in-cluster Traefik DaemonSet):

| Domain | Service | Namespace |
|---|---|---|
| `traefik.lab.pixeloven.com` | Traefik dashboard | traefik |
| `grafana.lab.pixeloven.com` | Grafana | monitoring |
| `prometheus.lab.pixeloven.com` | Prometheus | monitoring |
| `comfyui.lab.pixeloven.com` | ComfyUI | comfyui |
| `coder.lab.pixeloven.com` + `*.coder.lab.pixeloven.com` | Coder workspace orchestrator + per-workspace browser URLs | coder |
| `pi-web.lab.pixeloven.com` | PI WEB operator surface | pi-web |
| `open-webui.lab.pixeloven.com` | Open WebUI | open-webui |
| `immich.lab.pixeloven.com` | Immich | immich |
| `searxng.lab.pixeloven.com` | SearXNG | searxng |
| `agents.lab.pixeloven.com` | AI Agents | ai-agents |
| `litellm.lab.pixeloven.com` | LiteLLM (Nexus) | nexus |
| `argocd.lab.pixeloven.com` | ArgoCD | argocd |
| `home.lab.pixeloven.com` | Homepage | homepage |
| `files.lab.pixeloven.com` | FileBrowser | filebrowser |

**Webhook services** (Cloudflare Tunnel → operator workstation):

| Domain | Target |
|---|---|
| `webhooks.pixeloven.com` | Cloudflare Tunnel → localhost:8000 (FastAPI) |

## DNS

Managed via Cloudflare (Terraform `stage1-omni`):
- Management domains → A records to 192.168.8.210 (Omni VM)
- Lab domains → A records to Talos VM IPs (192.168.8.211/.212/.213, hostPort 80/443)
- Webhook domain → Cloudflare Tunnel (not a DNS A record)

## Quick diagnostics

```bash
kubectl get nodes -o wide                          # Node status + IPs
talosctl health --nodes 192.168.8.211              # Talos node health
kubectl get pods -A | grep -v Running              # Non-running pods across all namespaces
kubectl get externalsecret -A                      # ESO sync status
```

## Monitoring namespace

The `monitoring` namespace uses `privileged` PodSecurity enforcement (required for Node Exporter and DCGM Exporter — hostNetwork, hostPID, hostPath). Do not downgrade to `baseline`.
