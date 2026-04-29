# Instance Metadata Service (IMDS)

The Instance Metadata Service provides information about the running VM,
accessible from within the VM at `http://169.254.169.254`.

## Available Metadata

```bash
# VM ID
curl http://169.254.169.254/latest/meta-data/instance-id

# Instance type
curl http://169.254.169.254/latest/meta-data/instance-type

# Region
curl http://169.254.169.254/latest/meta-data/placement/region

# Public IP
curl http://169.254.169.254/latest/meta-data/public-ipv4

# Private IP
curl http://169.254.169.254/latest/meta-data/local-ipv4

# Hostname
curl http://169.254.169.254/latest/meta-data/hostname
```

## User Data

Access the user data script passed at VM creation:
```bash
curl http://169.254.169.254/latest/user-data
```

## Spot Instance Interruption Notice

Check if a spot instance is scheduled for interruption:
```bash
curl http://169.254.169.254/latest/meta-data/spot/termination-time
# Returns 404 if not being terminated
# Returns timestamp if termination is imminent
```

## IMDSv2 (Session-Oriented)

For enhanced security, use IMDSv2, which requires a session token:
```bash
TOKEN=$(curl -X PUT   -H "X-aws-ec2-metadata-token-ttl-seconds: 21600"   http://169.254.169.254/latest/api/token)

curl -H "X-aws-ec2-metadata-token: $TOKEN"   http://169.254.169.254/latest/meta-data/instance-id
```

## Restricting IMDS Access

Prevent container escapes from accessing IMDS:
```bash
# Block IMDS from Docker containers
iptables -I DOCKER-USER -d 169.254.169.254 -j REJECT
```

## Use Cases

- Auto-discover VM ID and region for logging and monitoring.
- Detect spot interruption in application code.
- Bootstrap configuration without hardcoding values.
