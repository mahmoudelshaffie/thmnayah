# CMS Docker Setup

This directory contains Docker configuration files for the CMS service, including development and production setups.

## 🐳 Quick Start

### Development Environment

1. **Copy environment file:**
   ```bash
   cp .env.example .env
   ```

2. **Edit environment variables in `.env`:**
   - Update database credentials
   - Set Redis password
   - Configure API settings

3. **Start services:**
   ```bash
   cd docker/
   docker-compose up -d
   ```

4. **Run database migrations:**
   ```bash
   docker-compose exec cms_app alembic upgrade head
   ```

5. **Create superuser (optional):**
   ```bash
   docker-compose exec cms_app python scripts/create_superuser.py
   ```

### Production Environment

1. **Prepare production environment:**
   ```bash
   cp .env.example .env.prod
   # Edit .env.prod with production values
   ```

2. **Create data directories:**
   ```bash
   mkdir -p ./data/{postgres,redis,media,logs}
   mkdir -p ./backups
   ```

3. **Deploy with production compose:**
   ```bash
   docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d
   ```

## 📁 File Structure

```
docker/
├── Dockerfile                    # Multi-stage Dockerfile
├── docker-compose.yml           # Development environment
├── docker-compose.prod.yml      # Production environment
├── init-scripts/               # Database initialization
│   └── 01-create-extensions.sql
├── nginx/                      # Nginx configuration
│   └── nginx.conf
├── redis/                      # Redis configurations
│   ├── redis.conf             # Development
│   └── redis-prod.conf        # Production
└── README.md                   # This file
```

## 🏗️ Architecture

### Development Stack
- **CMS App**: FastAPI with hot-reload
- **PostgreSQL 16**: Database with extensions
- **Redis 7**: Caching and sessions
- **MailHog**: Email testing
- **Adminer**: Database management UI
- **Redis Commander**: Redis management UI

### Production Stack
- **CMS App**: Multi-instance deployment
- **PostgreSQL 16**: Production-optimized
- **Redis 7**: Production configuration
- **Nginx**: Reverse proxy, SSL, static files
- **Backup Service**: Automated database backups
- **Monitoring**: Prometheus + Grafana (optional)

## 🔧 Services

### CMS Application
- **Development Port**: 8000
- **Production**: Behind Nginx (80/443)
- **Health Check**: `/health`
- **API Documentation**: `/docs`

### Database (PostgreSQL)
- **Port**: 5432
- **Extensions**: uuid-ossp, pg_trgm, btree_gin, unaccent
- **Development**: Data in named volume
- **Production**: Bind mount to host path

### Cache (Redis)
- **Port**: 6379
- **Password Protected**: Yes
- **Persistence**: AOF + RDB
- **Development**: Basic config
- **Production**: Memory optimized

### Management Tools (Development Only)
- **Adminer**: http://localhost:8080
- **Redis Commander**: http://localhost:8081
- **MailHog Web**: http://localhost:8025

## 🔒 Security Features

### Production Security
- **HTTPS Only**: Force SSL redirect
- **Security Headers**: HSTS, XSS protection, etc.
- **Rate Limiting**: API and auth endpoints
- **Non-root User**: All services run as non-root
- **Resource Limits**: CPU and memory constraints

### Network Security
- **Internal Networks**: Services communicate internally
- **Port Exposure**: Only necessary ports exposed
- **SSL Certificates**: Required for production

## 🚀 Deployment Commands

### Development
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f cms_app

# Stop services
docker-compose down

# Rebuild and restart
docker-compose up -d --build
```

### Production
```bash
# Deploy production stack
docker-compose -f docker-compose.prod.yml up -d

# Scale application instances
docker-compose -f docker-compose.prod.yml up -d --scale cms_app=3

# Update application
docker-compose -f docker-compose.prod.yml build cms_app
docker-compose -f docker-compose.prod.yml up -d --no-deps cms_app

# View production logs
docker-compose -f docker-compose.prod.yml logs -f cms_app
```

## 📊 Monitoring (Production)

Enable monitoring stack with:
```bash
docker-compose -f docker-compose.prod.yml --profile monitoring up -d
```

**Access:**
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000

## 🔄 Database Operations

### Migrations
```bash
# Create new migration
docker-compose exec cms_app alembic revision --autogenerate -m "Description"

# Apply migrations
docker-compose exec cms_app alembic upgrade head

# Migration history
docker-compose exec cms_app alembic history
```

### Backup & Restore
```bash
# Manual backup
docker-compose exec postgres pg_dump -U cms_user cms_db > backup.sql

# Restore from backup
docker-compose exec -T postgres psql -U cms_user cms_db < backup.sql
```

## 🧪 Testing

### Run Tests in Container
```bash
# Unit tests
docker-compose exec cms_app pytest

# With coverage
docker-compose exec cms_app pytest --cov=app

# Specific test file
docker-compose exec cms_app pytest tests/test_categories.py
```

## 🔧 Troubleshooting

### Common Issues

1. **Port Conflicts**
   ```bash
   # Check if ports are in use
   lsof -i :8000
   lsof -i :5432
   ```

2. **Permission Issues**
   ```bash
   # Fix volume permissions
   sudo chown -R $(id -u):$(id -g) ./data
   ```

3. **Database Connection Issues**
   ```bash
   # Check database logs
   docker-compose logs postgres
   
   # Test connection
   docker-compose exec cms_app python -c "from app.db.session import SessionLocal; print('DB OK')"
   ```

4. **Memory Issues**
   ```bash
   # Check resource usage
   docker stats
   
   # Increase memory limits in docker-compose
   ```

### Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f cms_app
docker-compose logs -f postgres
docker-compose logs -f redis

# With timestamps
docker-compose logs -f -t cms_app
```

## 🌐 Environment Variables

### Required Variables
- `POSTGRES_PASSWORD`: Database password
- `REDIS_PASSWORD`: Redis password
- `SECRET_KEY`: Application secret key

### Optional Variables
- `CMS_PORT`: Application port (default: 8000)
- `DATA_PATH`: Production data path
- `BACKUP_PATH`: Backup storage path

### Production-Specific
- `ALLOWED_HOSTS`: Comma-separated hostnames
- `CORS_ORIGINS`: Comma-separated allowed origins
- `SENTRY_DSN`: Error tracking DSN

## 📈 Performance Tuning

### Database Optimization
```bash
# Production PostgreSQL settings
POSTGRES_MAX_CONNECTIONS=200
POSTGRES_SHARED_BUFFERS=256MB
POSTGRES_EFFECTIVE_CACHE_SIZE=1GB
```

### Redis Optimization
```bash
# Memory settings
REDIS_MAXMEMORY=512mb
REDIS_MAXMEMORY_POLICY=allkeys-lru
```

### Application Scaling
```bash
# Worker processes
WEB_CONCURRENCY=4
WORKERS_PER_CORE=1
MAX_WORKERS=8
```

---

For more detailed information, see the main project documentation.