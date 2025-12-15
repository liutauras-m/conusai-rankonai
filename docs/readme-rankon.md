# RankOnAI Docker Compose - Swarm Deployment Guide

## Converting Local Docker Compose to Swarm

This guide documents how to convert the original local docker-compose.yml to work with Docker Swarm deployment via Dokploy.

---

## Original (Local Development) vs Swarm (Production)

### Key Differences

| Aspect | Local (docker-compose) | Swarm (Dokploy) |
|--------|------------------------|-----------------|
| Proxy | nginx container | Traefik (external) |
| Build | `build: ./frontend` | Pre-built images from registry |
| Restart | `restart: unless-stopped` | `deploy.restart_policy` |
| Replicas | Single or `replicas: N` | `deploy.mode: replicated` |
| Networks | Default bridge | Overlay networks |
| Labels | None needed | Traefik routing labels |

---

## Issues Found & Fixes

### 1. ❌ Frontend Healthcheck Uses Wrong Command

**Problem:** The frontend image (Alpine-based) has `wget` but NOT `curl`. Using `curl` causes healthcheck failures, containers exit with code 0, and don't restart.

**Original (broken):**
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:3000"]
```

**Fixed:**
```yaml
healthcheck:
  test: ["CMD", "wget", "-q", "--spider", "http://localhost:3000"]
  interval: 30s
  timeout: 10s
  retries: 5
  start_period: 60s
```

**CLI fix for running service:**
```bash
docker service update --no-healthcheck <stack>_frontend
```

---

### 2. ❌ Middleware Suffix for Swarm

**Problem:** Traefik middleware references must use `@swarm` suffix (not `@docker`) when using Swarm provider.

**Original (broken):**
```yaml
- "traefik.http.routers.rankonai-secure.middlewares=rankonai-ratelimit@docker"
```

**Fixed:**
```yaml
- "traefik.http.routers.rankonai-secure.middlewares=rankonai-ratelimit@swarm,rankonai-headers@swarm"
```

---

### 3. ❌ Traefik Network Label

**Problem:** Use `traefik.swarm.network` instead of `traefik.docker.network` in Swarm mode.

**Original:**
```yaml
- "traefik.docker.network=dokploy-network"
```

**Fixed:**
```yaml
- "traefik.swarm.network=dokploy-network"
```

---

### 4. ❌ DNS Resolution Issues (Frontend → Backend)

**Problem:** Docker Swarm overlay network DNS can return stale IPs when services restart, causing "fetch failed" or "Connection refused" errors.

**Symptoms:**
- Frontend returns 500 error with `fetch failed`
- Logs show `ECONNREFUSED` or `UND_ERR_HEADERS_TIMEOUT`
- `wget` from frontend container to `http://backend:8000` fails
- But backend is running and healthy

**Diagnosis:**
```bash
# Check backend VIP
docker service inspect <stack>_backend --format '{{range .Endpoint.VirtualIPs}}{{.Addr}}{{end}}'
# Example: 10.0.2.2/24

# Check what frontend resolves
docker exec <frontend_container> getent hosts backend
# Example: 10.0.1.49 (WRONG - stale IP!)
```

**Fix - Add hosts entry:**
```bash
# Get current backend VIP
BACKEND_VIP=$(docker service inspect <stack>_backend --format '{{range .Endpoint.VirtualIPs}}{{.Addr}}{{end}}' | cut -d'/' -f1)

# Add hosts entry to frontend
docker service update --host-add "backend:$BACKEND_VIP" <stack>_frontend
```

**Note:** This is a workaround. If backend VIP changes after redeployment, update the hosts entry.

---

### 5. ⚠️ Worker Node Placement

**Recommendation:** Run all application services on worker nodes, not the manager.

**Add to each service:**
```yaml
deploy:
  placement:
    constraints:
      - node.role == worker
```

---

### 6. ⚠️ Private Registry Authentication

**Problem:** Worker nodes need authentication to pull from `ghcr.io`.

**Solutions:**

1. **Login on each node:**
   ```bash
   echo "YOUR_GITHUB_PAT" | docker login ghcr.io -u YOUR_USERNAME --password-stdin
   ```

2. **Use registry auth with deploy:**
   ```bash
   docker stack deploy --with-registry-auth -c docker-compose.yml <stack>
   ```

3. **Configure registry in Dokploy** (recommended)

---

### 7. ⚠️ Image Architecture

**Problem:** Images must be `linux/amd64`, not `arm64` (Apple Silicon).

**CI/CD fix:**
```bash
docker buildx build --platform linux/amd64 -t ghcr.io/liutauras-m/conusai-rankonai-frontend:latest --push .
```

---

## Final Working Docker Compose

```yaml
version: "3.8"

services:
  # Next.js Frontend
  frontend:
    image: ghcr.io/liutauras-m/conusai-rankonai-frontend:${IMAGE_TAG:-latest}
    environment:
      - NODE_ENV=production
      - BACKEND_URL=http://backend:8000
      - NEXT_PUBLIC_TURNSTILE_SITE_KEY=${NEXT_PUBLIC_TURNSTILE_SITE_KEY}
      - TURNSTILE_SECRET_KEY=${TURNSTILE_SECRET_KEY}
      - NEXT_PUBLIC_POSTHOG_KEY=${NEXT_PUBLIC_POSTHOG_KEY}
      - NEXT_PUBLIC_POSTHOG_HOST=${NEXT_PUBLIC_POSTHOG_HOST:-https://eu.i.posthog.com}
    networks:
      - app-network
      - dokploy-network
    deploy:
      mode: replicated
      replicas: 2
      resources:
        limits:
          cpus: "1"
          memory: 512M
      restart_policy:
        condition: any
        delay: 5s
        max_attempts: 5
      update_config:
        parallelism: 1
        delay: 10s
        failure_action: rollback
      rollback_config:
        parallelism: 1
        delay: 10s
      placement:
        constraints:
          - node.role == worker
      labels:
        - "traefik.enable=true"
        - "traefik.swarm.network=dokploy-network"
        # HTTP Router - redirect to HTTPS
        - "traefik.http.routers.rankonai.rule=Host(`rankonai.cloud.conusai.com`)"
        - "traefik.http.routers.rankonai.entrypoints=web"
        - "traefik.http.routers.rankonai.middlewares=redirect-to-https@swarm"
        # HTTPS Router
        - "traefik.http.routers.rankonai-secure.rule=Host(`rankonai.cloud.conusai.com`)"
        - "traefik.http.routers.rankonai-secure.entrypoints=websecure"
        - "traefik.http.routers.rankonai-secure.tls=true"
        - "traefik.http.routers.rankonai-secure.tls.certresolver=letsencrypt"
        - "traefik.http.routers.rankonai-secure.service=rankonai"
        # Service
        - "traefik.http.services.rankonai.loadbalancer.server.port=3000"
        # Middlewares - Rate Limiting (per IP)
        - "traefik.http.middlewares.rankonai-ratelimit.ratelimit.average=100"
        - "traefik.http.middlewares.rankonai-ratelimit.ratelimit.burst=50"
        - "traefik.http.middlewares.rankonai-ratelimit.ratelimit.period=1m"
        - "traefik.http.middlewares.rankonai-ratelimit.ratelimit.sourcecriterion.ipstrategy.depth=1"
        # Middlewares - Redirect HTTP to HTTPS
        - "traefik.http.middlewares.redirect-to-https.redirectscheme.scheme=https"
        - "traefik.http.middlewares.redirect-to-https.redirectscheme.permanent=true"
        # Middlewares - Security Headers
        - "traefik.http.middlewares.rankonai-headers.headers.stsSeconds=31536000"
        - "traefik.http.middlewares.rankonai-headers.headers.stsIncludeSubdomains=true"
        - "traefik.http.middlewares.rankonai-headers.headers.frameDeny=true"
        - "traefik.http.middlewares.rankonai-headers.headers.contentTypeNosniff=true"
        - "traefik.http.middlewares.rankonai-headers.headers.browserXssFilter=true"
        # Apply middlewares to HTTPS router
        - "traefik.http.routers.rankonai-secure.middlewares=rankonai-ratelimit@swarm,rankonai-headers@swarm"
    healthcheck:
      test: ["CMD", "wget", "-q", "--spider", "http://localhost:3000"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 60s
    depends_on:
      - backend

  # FastAPI Backend (SEO Analyzer)
  backend:
    image: ghcr.io/liutauras-m/conusai-rankonai-backend:${IMAGE_TAG:-latest}
    environment:
      - REDIS_URL=redis://redis:6379
      - MAX_CONCURRENT_ANALYSES=5
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - XAI_API_KEY=${XAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}
      - MISTRAL_API_KEY=${MISTRAL_API_KEY}
      - DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}
    networks:
      - app-network
    deploy:
      mode: replicated
      replicas: 2
      resources:
        limits:
          cpus: "2"
          memory: 1G
      restart_policy:
        condition: any
        delay: 5s
        max_attempts: 5
      update_config:
        parallelism: 1
        delay: 10s
        failure_action: rollback
      rollback_config:
        parallelism: 1
        delay: 10s
      placement:
        constraints:
          - node.role == worker
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 60s
    depends_on:
      - redis

  # Redis for caching
  redis:
    image: redis:alpine
    command: redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru
    volumes:
      - redis_data:/data
    networks:
      - app-network
    deploy:
      mode: replicated
      replicas: 1
      resources:
        limits:
          cpus: "0.5"
          memory: 300M
      restart_policy:
        condition: any
        delay: 5s
        max_attempts: 5
      placement:
        constraints:
          - node.role == worker
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

networks:
  app-network:
    driver: overlay
    attachable: true
  dokploy-network:
    external: true

volumes:
  redis_data:
    driver: local
```

---

## Troubleshooting Commands

### Check service status
```bash
docker service ls | grep rankonai
docker service ps <stack>_frontend --no-trunc
```

### View logs
```bash
docker service logs <stack>_frontend -f
docker service logs <stack>_backend -f
```

### Test connectivity
```bash
# Test backend directly
docker run --rm --network <stack>_app-network alpine wget -qO- http://backend:8000/health

# Test from frontend container
docker exec <frontend_container> wget -qO- http://backend:8000/health
```

### Fix healthcheck issues
```bash
docker service update --no-healthcheck <stack>_frontend
docker service update --no-healthcheck <stack>_backend
```

### Fix DNS issues
```bash
# Get backend VIP and add to frontend
BACKEND_VIP=$(docker service inspect <stack>_backend --format '{{range .Endpoint.VirtualIPs}}{{.Addr}}{{end}}' | cut -d'/' -f1)
docker service update --host-add "backend:$BACKEND_VIP" <stack>_frontend
```

### Force restart services
```bash
docker service update --force <stack>_frontend
docker service update --force <stack>_backend
```

---

## Summary of Changes from Original

| Component | Original | Swarm |
|-----------|----------|-------|
| Nginx proxy | Included | Removed (use Traefik) |
| Build context | `build: ./frontend` | Pre-built images |
| Networks | Default | `app-network` + `dokploy-network` |
| Traefik labels | None | Full routing config |
| Frontend healthcheck | `curl` | `wget` (curl not in image) |
| Middleware suffix | N/A | `@swarm` |
| Placement | None | `node.role == worker` |
| Restart policy | `unless-stopped` | `condition: any` |
