# Static Website Hosting

Host a static site (HTML, CSS, JS, or a built React/Vue/Next.js app) on
Nirvana Object Storage without managing a VM.

## Enabling Static Hosting

1. Create a bucket with a globally unique name (ideally matching your domain).
2. Open **Bucket Settings → Static Website Hosting → Enable**.
3. Set the **Index document** (e.g., `index.html`) and **Error document** (e.g., `404.html`).
4. Upload your build output:
   ```bash
   aws s3 sync ./dist s3://my-site/ --endpoint-url https://storage.nirvanacloud.io
   ```
5. The site is accessible at `https://my-site.storage.nirvanacloud.io`.

## Custom Domain & HTTPS

1. Create a CNAME record: `www.example.com → my-site.storage.nirvanacloud.io`.
2. Request a managed TLS certificate under **Settings → Certificates → + Request**.
3. Attach the certificate to the bucket: **Bucket Settings → Custom Domain → Add**.

## CDN (Cache)

Enable the Nirvana CDN to serve assets from edge nodes closest to your users:
**Bucket Settings → CDN → Enable**.

Benefits:
- Static assets cached at 15+ edge locations
- Reduced origin bandwidth costs
- Automatic HTTPS at the edge

## Cache Invalidation

After deploying a new version, invalidate the CDN cache:
```bash
nirvana cdn invalidate --bucket my-site --paths "/*"
```

Or set cache-control headers on your files to control TTL:
```bash
aws s3 cp dist/ s3://my-site/ --recursive   --cache-control "public, max-age=31536000"   --endpoint-url https://storage.nirvanacloud.io
```

## Deployment Pipeline

```bash
# .github/workflows/deploy.yml snippet
- name: Deploy site
  run: |
    npm run build
    aws s3 sync dist/ s3://my-site/ --delete       --endpoint-url https://storage.nirvanacloud.io
    nirvana cdn invalidate --bucket my-site --paths "/*"
```
