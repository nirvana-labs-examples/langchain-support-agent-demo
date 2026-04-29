# Nirvana Cloud Pulumi Provider

## Installation

```bash
pip install pulumi-nirvana     # Python
npm install @nirvana-labs/pulumi  # TypeScript/JavaScript
```

## Authentication

```bash
export NIRVANA_API_KEY=your-api-key
```

Or configure in `Pulumi.yaml`:
```yaml
config:
  nirvana:apiKey:
    secret: true
```

## Basic Example (Python)

```python
import pulumi
import pulumi_nirvana as nirvana

vpc = nirvana.Vpc("main",
    cidr_block="10.0.0.0/16",
    region="us-east-1",
)

vm = nirvana.Vm("web",
    instance_type="standard-4",
    image="ubuntu-22-04",
    region="us-east-1",
    vpc_id=vpc.id,
    public_ip=True,
)

pulumi.export("vm_ip", vm.public_ip)
```

## TypeScript Example

```typescript
import * as nirvana from "@nirvana-labs/pulumi";

const vm = new nirvana.Vm("api-server", {
    instanceType: "standard-8",
    image: "ubuntu-22-04",
    region: "us-east-1",
});

export const ip = vm.publicIp;
```

## State Management

Use Pulumi Cloud (free for individuals) or self-host the state in Nirvana Object Storage:

```bash
pulumi login s3://my-state-bucket?endpoint=https://storage.nirvanacloud.io
```

## Stack Configuration

```bash
pulumi config set nirvana:region us-east-1
pulumi config set --secret nirvana:apiKey your-api-key
```

## Resource Reference

Full resource reference: docs.nirvanacloud.io/pulumi
