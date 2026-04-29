# Managed TLS Certificates

Nirvana Cloud provides free, automatically renewed TLS certificates via Let's Encrypt.

## Requesting a Certificate

1. Navigate to **Settings → Certificates → + Request Certificate**.
2. Enter the domain name(s) (supports wildcard: `*.example.com`).
3. Choose the validation method:
   - **DNS validation** (recommended): Nirvana adds a TXT record if your domain
     uses Nirvana DNS, or you add it manually.
   - **HTTP validation**: Nirvana places a file on port 80; requires a running VM.
4. Click **Request**. Issuance takes 30–60 seconds.

## Attaching to a Load Balancer

1. Navigate to the load balancer → **Listeners → + Add Listener**.
2. Protocol: HTTPS, Port: 443.
3. Certificate: Select the managed certificate.
4. Nirvana automatically renews the certificate before expiry.

## Wildcard Certificates

Wildcard certificates (`*.example.com`) cover all single-level subdomains:
- ✅ `api.example.com`
- ✅ `app.example.com`
- ❌ `api.v2.example.com` (two levels deep)

Wildcard certificates require DNS validation.

## Custom Certificates (BYOC)

To use a certificate from your own CA or a commercial provider:
1. **Settings → Certificates → + Upload Certificate**.
2. Upload the certificate PEM, private key PEM, and certificate chain PEM.
3. Nirvana stores the private key encrypted at rest.

## Certificate Expiry Alerts

Nirvana sends email warnings 30 days and 7 days before a certificate expires.
Managed certificates renew automatically — expiry alerts indicate a renewal issue.

## Troubleshooting

- **Certificate not issued**: Verify DNS records are correct and have propagated.
- **Browser shows wrong certificate**: Check the load balancer listener is using
  the correct certificate and the CDN cache has been cleared.
