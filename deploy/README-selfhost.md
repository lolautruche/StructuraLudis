# Self-Hosting Structura Ludis

This guide explains how to self-host Structura Ludis using Docker, including setup on Synology NAS with Container Manager.

## Requirements

- Docker Engine 20.10+ and Docker Compose v2
- 1GB RAM minimum (2GB recommended)
- 10GB disk space
- A domain name (for HTTPS)

## Quick Start

### 1. Download the deployment files

```bash
# Clone the repository (or download just the deploy folder)
git clone https://github.com/lolautruche/StructuraLudis.git
cd StructuraLudis/deploy
```

### 2. Configure environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit with your settings
nano .env
```

**Critical settings to change:**
- `POSTGRES_PASSWORD` - Use a strong password
- `SECRET_KEY` - Generate with `openssl rand -hex 32`
- `DOMAIN` - Your domain name
- `LETSENCRYPT_EMAIL` - For SSL certificates
- `SMTP_*` - Your email provider settings

### 3. Start the services

```bash
# Without reverse proxy (for testing)
docker compose -f docker-compose.prod.yml up -d

# With Traefik reverse proxy (recommended for production)
docker compose -f docker-compose.prod.yml -f traefik/docker-compose.traefik.yml up -d
```

### 4. Initialize the database

```bash
# Run database migrations
docker compose -f docker-compose.prod.yml exec sl-api alembic upgrade head

# (Optional) Seed with demo data
docker compose -f docker-compose.prod.yml exec sl-api python -m scripts.seed_db
```

### 5. Access the application

- Without Traefik: http://localhost:3000
- With Traefik: https://your-domain.com

---

## Synology NAS (Container Manager)

### Method 1: Using Container Manager Projects

1. **Open Container Manager** > **Project** > **Create**

2. **Upload docker-compose.prod.yml** as the project file

3. **Configure environment variables** in the Container Manager UI:
   - Click on the project settings
   - Add all required variables from `.env.example`

4. **Start the project**

5. **Run migrations** via SSH or Task Scheduler:
   ```bash
   docker exec sl_api alembic upgrade head
   ```

### Method 2: Manual Container Setup

If you prefer manual control:

1. **Create a network**: `sl-network` (bridge mode)

2. **Create PostgreSQL container**:
   - Image: `postgres:16-alpine`
   - Network: `sl-network`
   - Volume: Map a folder for `/var/lib/postgresql/data`
   - Environment: Set `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`

3. **Create API container**:
   - Image: `ghcr.io/lolautruche/structuraludis-api:latest`
   - Network: `sl-network`
   - Environment: Set all required variables

4. **Create Frontend container**:
   - Image: `ghcr.io/lolautruche/structuraludis-frontend:latest`
   - Network: `sl-network`
   - Port: Map to your desired port

### Reverse Proxy on Synology

If using Synology's built-in reverse proxy:

1. **Control Panel** > **Login Portal** > **Advanced** > **Reverse Proxy**

2. **Create rule for frontend**:
   - Source: `https://your-domain.com:443`
   - Destination: `http://localhost:3000`

3. **Create rule for API**:
   - Source: `https://your-domain.com:443/api`
   - Destination: `http://localhost:8000/api`

---

## Backup & Restore

### Backup

```bash
# Backup database
docker exec sl_postgres pg_dump -U sl_admin structura_ludis > backup_$(date +%Y%m%d).sql

# Backup volumes (if using named volumes)
docker run --rm -v sl_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_data.tar.gz /data
```

### Restore

```bash
# Restore database
cat backup_20260201.sql | docker exec -i sl_postgres psql -U sl_admin structura_ludis

# Restore volumes
docker run --rm -v sl_postgres_data:/data -v $(pwd):/backup alpine tar xzf /backup/postgres_data.tar.gz -C /
```

---

## Updating

```bash
# Pull latest images
docker compose -f docker-compose.prod.yml pull

# Restart with new images
docker compose -f docker-compose.prod.yml up -d

# Run any new migrations
docker compose -f docker-compose.prod.yml exec sl-api alembic upgrade head
```

---

## Troubleshooting

### Check logs

```bash
# All services
docker compose -f docker-compose.prod.yml logs -f

# Specific service
docker compose -f docker-compose.prod.yml logs -f sl-api
```

### Database connection issues

```bash
# Check if database is ready
docker exec sl_postgres pg_isready -U sl_admin

# Check database logs
docker logs sl_postgres
```

### Reset everything

```bash
# Stop and remove all containers and volumes (WARNING: deletes all data!)
docker compose -f docker-compose.prod.yml down -v
```

---

## Security Recommendations

1. **Change default passwords** - Never use example passwords in production
2. **Use HTTPS** - Always use a reverse proxy with SSL in production
3. **Firewall** - Only expose ports 80/443, keep database internal
4. **Updates** - Regularly update Docker images for security patches
5. **Backups** - Set up automated backups of the database

---

## Support

- Documentation: https://github.com/lolautruche/StructuraLudis
- Issues: https://github.com/lolautruche/StructuraLudis/issues
