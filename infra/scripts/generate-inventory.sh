#!/bin/bash
# Generate Ansible inventory from Terraform output and verify SSH.
set -e

cd "$(dirname "$0")/../terraform"

GP3_3K_IP=$(terraform output -raw gp3_3k_ip 2>/dev/null || true)
GP3_16K_IP=$(terraform output -raw gp3_16k_ip 2>/dev/null || true)
IO2_32K_IP=$(terraform output -raw io2_32k_ip 2>/dev/null || true)
IO2_64K_IP=$(terraform output -raw io2_64k_ip 2>/dev/null || true)
NIRVANA_IP=$(terraform output -raw nirvana_ip 2>/dev/null || true)

if [ -z "$GP3_3K_IP" ] && [ -z "$GP3_16K_IP" ] && [ -z "$NIRVANA_IP" ]; then
    echo "Error: terraform output has no IPs at all. Run 'terraform apply' first."
    exit 1
fi

mkdir -p ../ansible/inventory

cat > ../ansible/inventory/hosts.yml <<EOF
all:
  children:
EOF

# AWS group only when at least one AWS IP is non-empty (skip_aws=false)
if [ -n "$GP3_3K_IP" ] || [ -n "$GP3_16K_IP" ] || [ -n "$IO2_32K_IP" ] || [ -n "$IO2_64K_IP" ]; then
    cat >> ../ansible/inventory/hosts.yml <<EOF
    aws:
      hosts:
EOF
    if [ -n "$GP3_3K_IP" ]; then
        cat >> ../ansible/inventory/hosts.yml <<EOF
        gp3-3k:
          ansible_host: ${GP3_3K_IP}
          ansible_user: ubuntu
          platform_name: gp3-3k
EOF
    fi
    if [ -n "$GP3_16K_IP" ]; then
        cat >> ../ansible/inventory/hosts.yml <<EOF
        gp3-16k:
          ansible_host: ${GP3_16K_IP}
          ansible_user: ubuntu
          platform_name: gp3-16k
EOF
    fi
    if [ -n "$IO2_32K_IP" ]; then
        cat >> ../ansible/inventory/hosts.yml <<EOF
        io2-32k:
          ansible_host: ${IO2_32K_IP}
          ansible_user: ubuntu
          platform_name: io2-32k
EOF
    fi
    if [ -n "$IO2_64K_IP" ]; then
        cat >> ../ansible/inventory/hosts.yml <<EOF
        io2-64k:
          ansible_host: ${IO2_64K_IP}
          ansible_user: ubuntu
          platform_name: io2-64k
EOF
    fi
fi

# Nirvana host only when its IP is non-empty (skip_nirvana=false)
if [ -n "$NIRVANA_IP" ]; then
    cat >> ../ansible/inventory/hosts.yml <<EOF
    nirvana:
      hosts:
        nirvana-abs:
          ansible_host: ${NIRVANA_IP}
          ansible_user: ubuntu
          platform_name: nirvana-abs
EOF
fi

echo "Inventory written to infra/ansible/inventory/hosts.yml:"
[ -n "$GP3_3K_IP" ]  && echo "  gp3-3k:       $GP3_3K_IP"  || echo "  gp3-3k:       (skipped)"
[ -n "$GP3_16K_IP" ] && echo "  gp3-16k:      $GP3_16K_IP" || echo "  gp3-16k:      (skipped)"
[ -n "$IO2_32K_IP" ] && echo "  io2-32k:      $IO2_32K_IP" || echo "  io2-32k:      (skipped)"
[ -n "$IO2_64K_IP" ] && echo "  io2-64k:      $IO2_64K_IP" || echo "  io2-64k:      (skipped)"
[ -n "$NIRVANA_IP" ]  && echo "  nirvana-abs:  $NIRVANA_IP"  || echo "  nirvana:      (skipped)"

# Wait for SSH on each host (parallel)
echo
echo "Verifying SSH (up to 60s per host)..."

wait_for_ssh() {
    local host=$1 name=$2
    for i in $(seq 1 12); do
        if ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no -o BatchMode=yes "ubuntu@$host" exit 2>/dev/null; then
            echo "  $name: ok"
            return 0
        fi
        sleep 5
    done
    echo "  $name: FAILED" >&2
    return 1
}

[ -n "$GP3_3K_IP" ]  && wait_for_ssh "$GP3_3K_IP"  "gp3-3k"  &
[ -n "$GP3_16K_IP" ] && wait_for_ssh "$GP3_16K_IP" "gp3-16k" &
[ -n "$IO2_32K_IP" ] && wait_for_ssh "$IO2_32K_IP" "io2-32k" &
[ -n "$IO2_64K_IP" ] && wait_for_ssh "$IO2_64K_IP" "io2-64k" &
[ -n "$NIRVANA_IP" ] && wait_for_ssh "$NIRVANA_IP" "nirvana-abs" &
wait

echo
echo "Ready. Next: cd infra/ansible && ansible-playbook playbook.yml"
