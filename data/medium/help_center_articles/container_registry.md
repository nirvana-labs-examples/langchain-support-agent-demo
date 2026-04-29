# Nirvana Container Registry (NCR)

## Creating a Registry

1. Navigate to **Containers → Registry → + Create Registry**.
2. Choose a name (becomes part of the image URL: `registry.nirvanacloud.io/<org>/<name>`).
3. Set visibility: **Private** (default) or **Public**.

## Pushing Images

Authenticate Docker with NCR:
```bash
nirvana registry login
# or:
docker login registry.nirvanacloud.io -u <username> -p <api-key>
```

Tag and push:
```bash
docker tag my-app:latest registry.nirvanacloud.io/my-org/my-app:latest
docker push registry.nirvanacloud.io/my-org/my-app:latest
```

## Pulling in Kubernetes

NKS clusters are pre-authorized to pull from registries in the same organisation.
No imagePullSecret configuration required.

For external clusters, create a pull secret:
```bash
kubectl create secret docker-registry ncr-secret   --docker-server=registry.nirvanacloud.io   --docker-username=<username>   --docker-password=<api-key>
```

## Image Scanning

All pushed images are automatically scanned for known CVEs using Trivy:
- Results appear under the image tag in the registry UI.
- Optionally block pushes of images with critical vulnerabilities:
  **Registry Settings → Security → Block on Critical CVEs**.

## Retention Policies

Auto-delete old image tags to control storage costs:
- **Registry Settings → Retention → + Add Rule**.
- Example: keep only the 10 most recent tags per repository.

## Pricing

- Storage: $0.025/GB/month
- Data transfer (pull): free within the same region; $0.09/GB cross-region or egress
