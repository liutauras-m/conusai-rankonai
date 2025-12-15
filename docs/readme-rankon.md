# RankOnAI Docker Compose Fixes for Swarm Deployment

## Issues Found & Fixes

### 1. ❌ Middleware Reference Mismatch

**Problem:** Traefik labels reference middlewares with `@docker` suffix, but in Swarm mode they need `@swarm`.

**Original (broken):**
```yaml
- "traefik.http.routers.rankonai-secure.middlewares=rankonai-ratelimit@docker,rankonai-headers@docker"
- "traefik.http.routers.rankonai.middlewares=redirect-to-https@docker"
```

**Fixed:**
```yaml
- "traefik.http.routers.rankonai-secure.middlewares=rankonai-ratelimit@swarm,rankonai-headers@swarm"
- "traefik.http.routers.rankonai.middlewares=redirect-to-https@swarm"
```

---

### 2. ❌ Rate Limit Too Aggressive

**Problem:** Rate limit of 5 requests/hour is too low and blocks normal usage.

**Original (broken):**
```yaml
- "traefik.http.middlewares.rankonai-ratelimit.ratelimit.average=5"
- "traefik.http.middlewares.rankonai-ratelimit.ratelimit.burst=2"
- "traefik.http.middlewares.rankonai-ratelimit.ratelimit.period=1h"
```

**Fixed:**
```yaml
- "traefik.http.middlewares.rankonai-ratelimit.ratelimit.average=100"
- "traefik.http.middlewares.rankonai-ratelimit.ratelimit.burst=50"
- "traefik.http.middlewares.rankonai-ratelimit.ratelimit.period=1m"
```

---

### 3. ❌ Healthcheck Causing Container Exits

**Problem:** The healthcheck uses `curl` but the frontend image only has `wget` installed (Alpine-based). This causes healthcheck failures, and combined with `restart_policy: condition: on-failure`, containers exit cleanly (code 0) and don't restart.

**Critical finding:** The frontend image does NOT have `curl` - only `wget` is available!

**Original (broken - curl not available):**
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:3000"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

**Options to fix:**

**Option A - Use wget (RECOMMENDED - it's available in the image):**
```yaml
healthcheck:
  test: ["CMD", "wget", "-q", "--spider", "http://localhost:3000"]
  interval: 30s
  timeout: 10s
  retries: 5
  start_period: 60s
```

**Option B - Disable healthcheck:**
```yaml
healthcheck:
  test: ["CMD", "true"]
  interval: 30s
```

**Option C - Disable via CLI (for running services):**
```bash
docker service update --no-healthcheck tools-conusairankonai-0jfhgi_frontend
```

---

### 4. ❌ Traefik Network Label (Swarm Mode)

**Problem:** Using `traefik.docker.network` which is for Docker provider, but in Swarm mode should use `traefik.swarm.network`.

**Original (may cause issues):**
```yaml
- "traefik.docker.network=dokploy-network"
```

**Fixed:**
```yaml
- "traefik.swarm.network=dokploy-network"
```

---

### 5. ⚠️ Private Registry Authentication

**Problem:** Worker nodes need to authenticate to `ghcr.io` to pull images.

**Solution:** Either:

1. **Pre-pull images on all nodes** before deploying:
   ```bash
   # On each node
   echo "YOUR_GITHUB_PAT" | docker login ghcr.io -u YOUR_USERNAME --password-stdin
   docker pull ghcr.io/liutauras-m/conusai-rankonai-frontend:latest
   docker pull ghcr.io/liutauras-m/conusai-rankonai-backend:latest
   ```

2. **Use `--with-registry-auth` when deploying:**
   ```bash
   docker stack deploy --with-registry-auth -c docker-compose.yml rankonai
   ```

3. **Configure Dokploy registry** and ensure it's used during compose deployment.

---

### 6. ⚠️ Image Architecture

**Problem:** Images must be built for `linux/amd64` (server architecture), not `arm64` (Apple Silicon).

**Fix in CI/CD:**
```bash
docker buildx build --platform linux/amd64 -t ghcr.io/liutauras-m/conusai-rankonai-frontend:latest --push .
```

---

## Updated Docker Compose (Fixed)

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
        condition: any  # Changed from on-failure to ensure restarts
        delay: 5s
        max_attempts: 5
      update_config:
        parallelism: 1
        delay: 10s
        failure_action: rollback
      rollback_config:
        parallelism: 1
        delay: 10s
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
        # Middlewares - Rate Limiting (more reasonable limits)
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
        # Apply middlewares to HTTPS router (FIXED: @swarm instead of @docker)
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
        condition: any  # Changed from on-failure
        delay: 5s
        max_attempts: 5
      update_config:
        parallelism: 1
        delay: 10s
        failure_action: rollback
      rollback_config:
        parallelism: 1
        delay: 10s
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
        max_attempts: 3
      placement:
        constraints:
          - node.role == worker  # Run on worker node
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

## Summary of Changes

| Issue | Original | Fixed |
|-------|----------|-------|
| Middleware suffix | `@docker` | `@swarm` |
| Traefik network label | `traefik.docker.network` | `traefik.swarm.network` |
| Rate limit average | 5/hour | 100/minute |
| Rate limit burst | 2 | 50 |
| Restart policy | `on-failure` | `any` |
| Healthcheck retries | 3 | 5 |
| Start period | 40s | 60s |
| Frontend healthcheck | `curl` (not available) | `wget` (available in image) |
