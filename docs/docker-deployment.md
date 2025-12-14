# Docker Compose Production Deployment

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                         nginx                                │
│              (Rate Limiting + Load Balancing)               │
│                      Port 80                                 │
└─────────────────────┬───────────────────┬───────────────────┘
                      │                   │
                      ▼                   ▼
┌─────────────────────────────┐ ┌─────────────────────────────┐
│        frontend             │ │        backend (x2)          │
│        (Next.js)            │ │        (FastAPI)             │
│        Port 3000            │ │        Port 8000             │
└─────────────────────────────┘ └──────────────┬──────────────┘
                                               │
                                               ▼
                                ┌─────────────────────────────┐
                                │          redis               │
                                │     (Caching Layer)          │
                                │        Port 6379             │
                                └─────────────────────────────┘
```

## Features

### Rate Limiting (nginx)
- **API analyze endpoint**: 10 requests/minute per IP (burst: 5)
- **General pages**: 30 requests/second per IP (burst: 50)
- **Connection limit**: 20 concurrent connections per IP

### Caching (Redis)
- Analysis results cached for 1 hour
- LRU eviction policy with 256MB max memory
- Persistent storage with AOF

### Concurrency Control (FastAPI)
- Maximum 5 concurrent analyses per backend instance
- 2 backend instances = 10 total concurrent analyses
- 503 response when all slots busy

### Resource Limits
| Service  | CPU   | Memory |
|----------|-------|--------|
| nginx    | 0.5   | 128MB  |
| frontend | 1.0   | 512MB  |
| backend  | 2.0   | 1GB    |
| redis    | 0.5   | 300MB  |

## Quick Start

```bash
# Build and start all services
docker compose up -d --build

# View logs
docker compose logs -f

# Check health
curl http://localhost/health

# Run an analysis
curl -X POST http://localhost/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

## Scaling

```bash
# Scale backend instances
docker compose up -d --scale backend=4

# Update nginx upstream for more backends
# (automatic with Docker Compose DNS)
```

## Environment Variables

### Backend (api.py)
| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_URL` | `redis://redis:6379` | Redis connection URL |
| `MAX_CONCURRENT_ANALYSES` | `5` | Max concurrent analyses per instance |
| `CACHE_TTL` | `3600` | Cache TTL in seconds |

### Frontend
| Variable | Default | Description |
|----------|---------|-------------|
| `BACKEND_URL` | `http://backend:8000` | Backend API URL |

## Monitoring

### Health Endpoints
- `GET /health` - Backend health check
- Returns: `{"status": "healthy", "redis": "connected", "concurrent_limit": 5}`

### Logs
```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f backend

# nginx access logs
docker compose exec nginx cat /var/log/nginx/access.log
```

## Development vs Production

| Feature | Development | Production (Docker) |
|---------|-------------|---------------------|
| Python execution | Direct spawn | FastAPI service |
| Caching | None | Redis |
| Rate limiting | None | nginx |
| Load balancing | None | nginx + replicas |
| Resource limits | None | Docker constraints |

## Stopping

```bash
# Stop all services
docker compose down

# Stop and remove volumes (clears cache)
docker compose down -v
```
