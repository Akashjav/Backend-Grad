# Render startup: CORS configuration

The reported worker crash occurs during configuration import, before the API starts.
Production CORS must name the HTTPS frontend origin. Local development defaults,
wildcards, empty values and URLs containing page paths are not valid.

For this frontend, set the backend Render service's **Environment** variable:

```dotenv
CORS_ORIGINS=https://frontend-grad.vercel.app
```

Choose **Save, rebuild, and deploy** after publishing the code changes. The checked-in
render.yaml now contains this origin, but an existing manually configured Docker
service does not automatically adopt the Blueprint file.

Keep APP_ENV=production. ALLOWED_HOSTS must contain the actual backend hostname
(for example your-service.onrender.com), without https:// or a path. It is separate
from CORS_ORIGINS. Keep the existing PostgreSQL, strong JWT secret and Redis settings.
Do not copy local development CORS values into the production service.

Configuration now accepts comma-separated origins or a JSON array, normalizes
trailing slashes, and validates HTTPS origins. scripts/serve.py validates settings
before starting workers, so invalid configuration exits once with a specific error.
No production security checks have been disabled.

After deployment, check /ready and sign in from https://frontend-grad.vercel.app.
The frontend VITE_API_URL must point to the actual HTTPS backend URL. A /ready
failure can indicate a separate database, migration or Redis issue.

Reference: https://render.com/docs/configure-environment-variables
