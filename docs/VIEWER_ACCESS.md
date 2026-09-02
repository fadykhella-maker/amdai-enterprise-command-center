# Secure Viewer Access

The hosted Streamlit dashboard is protected by a viewer-only authentication gate. Authentication runs before the dashboard or its telemetry clients load. Hosted users receive the `viewer` role only; deployment, configuration, restart, secret, and delete operations remain outside the public application.

## Configure Streamlit Community Cloud

In **App settings → Secrets**, add:

```toml
[auth]
viewer_username = "your-viewer-name"
viewer_name = "Team Viewer"
viewer_password_hash = "$2b$12$..."
cookie_name = "amd_eai_viewer"
cookie_key = "a-long-random-secret-known-only-to-this-app"
```

Never commit the real values. The stored password value is a bcrypt hash, not the password. The cookie key signs remembered sessions and must also remain secret.

To change the password, replace `viewer_password_hash`. To immediately sign out every remembered browser, rotate `cookie_key` at the same time. Each platform should use a different cookie name and cookie key.

## Security boundary

- The public app provides observation and navigation only.
- Management operations stay on the private/local control plane.
- Hiding controls is not the authorization boundary; management endpoints must independently reject viewer identities.
- Streamlit's toolbar is configured in viewer mode. Repository and deployment permissions continue to be controlled by Streamlit Community Cloud and GitHub.

## Release acceptance checks

1. Incorrect credentials are rejected and rate-limited.
2. Correct credentials open the dashboard without exposing secrets.
3. A normal viewer sees no deploy, edit, restart, configuration, user-management, or delete action.
4. A remembered session survives a browser restart; an unremembered session does not.
5. Rotating the cookie key invalidates remembered sessions.
6. Desktop and mobile layouts remain usable.
7. The dashboard loads when remote compute is offline and labels it truthfully as offline.
8. Direct access to any protected route or action is denied without authentication.
