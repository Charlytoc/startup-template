# Environment Configuration

## API URL Configuration

The mobile app connects to your Django backend API. You can configure the API URL in two ways:

### Method 1: app.json (Current)
The API URL is configured in `app.json` under the `extra` section:

```json
{
  "expo": {
    "extra": {
      "apiUrl": "https://1gm40gnb-8000.use2.devtunnels.ms/api"
    }
  }
}
```

### Method 2: Environment Variables (Future)
You can also use environment variables by creating a `.env` file:

```bash
# .env
API_URL=https://1gm40gnb-8000.use2.devtunnels.ms/api
```

## Changing the API URL

To change the API URL:

1. **For Development (Local):**
   ```json
   "apiUrl": "http://localhost:8000/api"
   ```

2. **For Production:**
   ```json
   "apiUrl": "https://your-production-domain.com/api"
   ```

3. **For Dev Tunnels:**
   ```json
   "apiUrl": "https://your-tunnel-url.use2.devtunnels.ms/api"
   ```

## Current Configuration

- **API URL:** `https://1gm40gnb-8000.use2.devtunnels.ms/api`
- **Timeout:** 10 seconds
- **Authentication:** Bearer token (stored securely)
