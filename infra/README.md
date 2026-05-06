# Cross-cloud benchmark infrastructure

Provisions five identical-spec VMs (4× AWS EC2 with different EBS variants + 1× Nirvana Cloud with ABS), runs both `benchmarks.ingest` and `benchmarks.retrieval` plus a raw-disk `fio` test, and pulls JSON results back to `results/<platform>/`.

## What gets provisioned

| Platform | Instance | Storage | IOPS |
|---|---|---|---|
| `gp3-3k` | AWS m6i.xlarge | 256 GB gp3 | 3,000 |
| `gp3-16k` | AWS m6i.xlarge | 256 GB gp3 | 16,000 |
| `io2-32k` | AWS m6i.xlarge | 256 GB io2 | 32,000 |
| `io2-64k` | AWS m6i.xlarge | 256 GB io2 | 64,000 |
| `nirvana-abs` | Nirvana n1-standard-4 | 256 GB ABS | dynamic |

All VMs: 4 vCPU, 16 GB RAM, Ubuntu 24.04 LTS. AWS in `us-west-1`, Nirvana in `us-sva-2` by default.

## Prerequisites (local machine)

- Terraform ≥ 1.5
- Ansible ≥ 2.14
- Python 3.11 with the repo's `.venv` already set up
- AWS credentials in env (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, optional `AWS_SESSION_TOKEN`)
- Nirvana credentials in env:
  ```bash
  export NIRVANA_LABS_API_KEY=...
  export TF_VAR_nirvana_project_id=prj_...
  export TF_VAR_ssh_public_key="$(cat ~/.ssh/your_key.pub)"  # whichever key your SSH agent uses
  ```

### AWS-only mode (skip Nirvana)

If you don't have a Nirvana API key yet:

```bash
export TF_VAR_skip_nirvana=true
export NIRVANA_LABS_API_KEY=stub  # any non-empty value; provider init only, no API calls
export TF_VAR_ssh_public_key="$(cat ~/.ssh/your_key.pub)"
```

`generate-inventory.sh` will produce an inventory without the `nirvana` group, and the playbook will only run on the 4 AWS hosts. If you already have results from a manual Nirvana run in `results/nirvana-abs/`, `compare-results.py` will pick them up alongside the AWS rows.

## Run end-to-end

```bash
# 1. Provision (~5 min — 5 VMs in parallel)
cd infra/terraform
terraform init
terraform apply

# 2. Run benchmarks (~15-20 min)
cd ../..
./infra/scripts/run-all.sh

# 3. View comparison
cat results/comparison_medium.md

# 4. Tear down (manual — verify nothing's left)
cd infra/terraform && terraform destroy
```

## What `run-all.sh` does

1. **`generate-inventory.sh`** — reads `terraform output` for each VM IP, writes `infra/ansible/inventory/hosts.yml`, and waits for SSH on all five hosts.
2. **`ansible-playbook playbook.yml`** — applies two roles to every host in parallel:
   - **`benchmark-services`** — installs Docker + fio, runs a 4k random-read fio benchmark on the root volume (caches dropped first), starts Qdrant via `docker compose`.
   - **`benchmark-runner`** — rsyncs the repo (incl. `data/.cache/`), installs Python deps via `uv`, runs `benchmarks.ingest <dataset>`, runs `app.ingest <dataset> --recreate` to populate Qdrant (with `qdrant_on_disk=true` so vectors and the HNSW graph are mmap'd from the block device), then runs a **retrieval concurrency sweep** at `c=1, 4, 16, 64` — dropping the OS page cache before each iteration so storage starts cold every time. Fetches `ingest_<dataset>.json`, `retrieval_<dataset>_c<N>.json` (one per concurrency level), and `fio.json` back to `results/<platform>/`. Dataset defaults to `medium`; pass via `./infra/scripts/run-all.sh large`.
3. **`compare-results.py`** — aggregates all `results/<platform>/*.json` files into `results/comparison_<dataset>.md` with tables for raw disk, ingest, and retrieval p50/p99/qps across the concurrency sweep. Pass dataset as first arg (default: `medium`).

### Why the concurrency sweep matters

Single-stream retrieval (`c=1`) issues one HNSW traversal at a time, generating only a few outstanding I/Os — far below what high-IOPS storage like ABS is built for. The platform ranking from `c=1` understates the storage advantage. At `c=16` and above, multiple traversals overlap and the page-fault stream actually saturates the block device — that's where the fio numbers translate into application-level latency differences.

Override the sweep with an Ansible extra var: `ansible-playbook playbook.yml -e 'retrieval_concurrency_levels=[1,8,32]'`. Tune query count per run with `-e retrieval_queries=1000` (default 500 — high enough to give stable percentiles even at `c=64`).

## Layout

```
infra/
├── README.md                       — this file
├── terraform/
│   ├── main.tf                     — 4× AWS instances + Nirvana VM + networking
│   ├── variables.tf
│   ├── terraform.tfvars.example
│   └── .gitignore
├── ansible/
│   ├── ansible.cfg
│   ├── playbook.yml
│   ├── inventory/                  — hosts.yml is generated, gitignored
│   ├── group_vars/
│   │   ├── aws.yml
│   │   └── nirvana.yml
│   └── roles/
│       ├── benchmark-services/
│       │   ├── tasks/main.yml      — Docker + fio + Qdrant
│       │   └── templates/docker-compose.yml.j2
│       └── benchmark-runner/
│           └── tasks/main.yml      — rsync repo, install deps, run benchmarks
└── scripts/
    ├── generate-inventory.sh
    ├── run-all.sh
    └── compare-results.py
```

## Cost note

Five VMs running for ~30 min each is roughly $1–2 on AWS (mostly the io2-64k instance) plus a small Nirvana charge. The risk is forgetting `terraform destroy` — io2 volumes accrue ~$0.65/GB-month + $0.065/IOPS-month, so a 256 GB / 64,000 IOPS volume left running is ~$5,500/month. **Always run `terraform destroy` after the run.**

## Troubleshooting

- **`terraform output` returns nothing** — `terraform apply` didn't complete. Check `terraform plan` first.
- **Ansible can't SSH** — `generate-inventory.sh` waits 60s per host. If it fails, the security group may not have your IP, or the VM is still booting. Try `ssh ubuntu@<ip>` manually.
- **Qdrant connection refused on the VM** — the playbook waits for port 6333 with a 60s timeout. If it times out, `docker compose logs qdrant` on the VM.
- **`data/.cache/` missing on the VM** — rsync excludes `.git` but should include the cache. If the cache is missing, `benchmarks.ingest` falls back to the slow embed path. Check that the cache exists in your local repo.
