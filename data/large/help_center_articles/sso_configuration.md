# SSO Configuration

Nirvana Cloud supports SAML 2.0 and OIDC for single sign-on (Enterprise plan).

## SAML 2.0 Setup

### Step 1: Get Nirvana SP Metadata

Navigate to **Settings → Security → SSO → Download SP Metadata**.
This XML file contains the entity ID and ACS URL needed to configure your IdP.

### Step 2: Configure Your IdP

Common IdPs (Okta, Azure AD, Google Workspace):

**Okta**:
1. Create a new SAML app.
2. Upload the SP metadata or enter the ACS URL and Entity ID manually.
3. Map the `email` and `name` attributes.
4. Assign users/groups to the app.

**Azure AD**:
1. Enterprise Applications → New Application → Create your own.
2. Set up Single Sign-On → SAML.
3. Upload SP metadata or configure manually.

### Step 3: Configure Nirvana

1. **Settings → Security → SSO → + Configure SAML**.
2. Paste your IdP metadata XML or enter the SSO URL, entity ID, and certificate.
3. Test the connection before enabling.
4. Enable SSO: once active, all members must sign in via SSO.

## OIDC Setup

1. Create an OIDC application in your IdP (Okta, Auth0, Google).
2. Set the redirect URI to `https://app.nirvanacloud.io/auth/callback`.
3. In Nirvana: **Settings → Security → SSO → + Configure OIDC**.
4. Enter Client ID, Client Secret, and the IdP's discovery URL.

## Just-in-Time Provisioning

New users who sign in via SSO are automatically provisioned in Nirvana with the
**Developer** role by default. Adjust the default role under SSO settings.

## Troubleshooting

- **SAML signature validation failed**: Ensure the IdP certificate is current and
  the clock on your IdP is synchronised (NTP).
- **User not provisioned**: Check that the `email` attribute is being sent by the IdP.
- **Redirect loop**: Verify the ACS URL in your IdP matches exactly (including trailing slash).
