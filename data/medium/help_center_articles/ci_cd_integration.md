# CI/CD Integration

## GitHub Actions

Deploy to a Nirvana VM from a GitHub Actions workflow:

```yaml
name: Deploy
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to Nirvana VM
        uses: appleboy/ssh-action@v1
        with:
          host: ${{ secrets.VM_IP }}
          username: ubuntu
          key: ${{ secrets.SSH_PRIVATE_KEY }}
          script: |
            cd /app
            git pull origin main
            docker compose up -d --build
```

Store `VM_IP` and `SSH_PRIVATE_KEY` as GitHub encrypted secrets.

## GitLab CI

```yaml
deploy:
  stage: deploy
  image: alpine:latest
  before_script:
    - apk add --no-cache openssh-client
    - eval $(ssh-agent -s)
    - echo "$SSH_PRIVATE_KEY" | ssh-add -
  script:
    - ssh ubuntu@$VM_IP "cd /app && git pull && docker compose up -d"
  only:
    - main
```

## Terraform in CI

```yaml
- name: Terraform Apply
  env:
    NIRVANA_API_KEY: ${{ secrets.NIRVANA_API_KEY }}
  run: |
    terraform init
    terraform plan
    terraform apply -auto-approve
```

## Rolling Deployments

Use the Nirvana API to perform rolling updates across a scaling group:
```bash
nirvana scaling-group rolling-update my-group   --launch-template new-template-id   --max-surge 1   --max-unavailable 0
```

## Container Registry in CI

```yaml
- name: Push image
  run: |
    docker login registry.nirvanacloud.io -u ${{ secrets.NCR_USER }} -p ${{ secrets.NCR_TOKEN }}
    docker build -t registry.nirvanacloud.io/my-org/my-app:$GITHUB_SHA .
    docker push registry.nirvanacloud.io/my-org/my-app:$GITHUB_SHA
```
