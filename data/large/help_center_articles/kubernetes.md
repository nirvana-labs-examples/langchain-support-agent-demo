# Nirvana Kubernetes Service (NKS)

## Creating a Cluster

1. Navigate to **Containers → Kubernetes → + Create Cluster**.
2. Select Kubernetes version (latest stable recommended).
3. Configure the control plane region.
4. Add node pools (groups of identically-sized worker VMs).
5. Click **Create** — the cluster is ready in 3–5 minutes.

## Node Pools

A node pool is a set of VMs sharing the same instance type and configuration:

- Add pools for different workload types (CPU-optimized, GPU, memory-optimized).
- Enable **Autoscaling** per pool: specify min/max node count.
- Nodes are replaced with zero-downtime rolling updates during Kubernetes upgrades.

## Accessing Your Cluster

Download the kubeconfig:
```bash
nirvana kubernetes get-credentials <cluster-name> --region us-east-1
```
This writes the kubeconfig to `~/.kube/config` (or merges it).

## Persistent Volumes

NKS integrates with Nirvana Block Storage via a CSI driver pre-installed on every
cluster. Use the `nirvana-block` StorageClass:

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: my-pvc
spec:
  storageClassName: nirvana-block
  accessModes: [ReadWriteOnce]
  resources:
    requests:
      storage: 50Gi
```

## Load Balancer Integration

Kubernetes `Service` resources of type `LoadBalancer` automatically provision a
Nirvana Layer 4 load balancer. Annotations control advanced options:

```yaml
metadata:
  annotations:
    service.beta.kubernetes.io/nirvana-load-balancer-type: "layer7"
```

## Upgrades

Control-plane upgrades are performed in-place. Worker nodes are drained, upgraded,
and uncordoned one at a time (rolling update). Typical upgrade time: 10–20 minutes
per node pool.

## Pricing

- Control plane: $0.10/hour (managed, highly available)
- Worker nodes: billed at standard VM rates
