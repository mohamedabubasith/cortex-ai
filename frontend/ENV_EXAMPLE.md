# Frontend Environment Variables

Create a `.env.local` file in the frontend directory with:

```bash
# API Base URL - Update this for production
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## For Production:
```bash
NEXT_PUBLIC_API_URL=https://your-api-domain.com
```

## For Docker:
This is already configured in `docker-compose.yml`
