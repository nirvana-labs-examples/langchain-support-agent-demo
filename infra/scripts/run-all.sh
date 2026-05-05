#!/bin/bash
# End-to-end driver: generate inventory from terraform output, run the playbook,
# aggregate results into a markdown table.
#
# Assumes `terraform apply` has already succeeded.
set -e

DATASET="${1:-medium}"
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

cd "$REPO_ROOT/infra"

echo "==> Generating Ansible inventory from terraform output"
./scripts/generate-inventory.sh

echo
echo "==> Running benchmarks on all VMs (dataset: $DATASET)"
cd ansible
ansible-playbook playbook.yml -e "dataset=$DATASET"

echo
echo "==> Aggregating results"
cd "$REPO_ROOT"
.venv/bin/python infra/scripts/compare-results.py "$DATASET"

echo
echo "Done. See results/comparison_${DATASET}.md"
