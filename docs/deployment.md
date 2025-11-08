## OpenMediaTrust Deployment Guide

## Prerequisites

### System Requirements

**Minimum:**
- CPU: 4 cores
- RAM: 8 GB
- Storage: 100 GB SSD
- OS: Ubuntu 20.04+ / CentOS 8+ / RHEL 8+

**Recommended (Production):**
- CPU: 8+ cores
- RAM: 16+ GB
- Storage: 500 GB SSD + Object storage
- OS: Ubuntu 22.04 LTS

### Software Requirements

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- MinIO or S3-compatible storage
- Docker & Docker Compose (for containerized deployment)

## Installation Methods

### Method 1: Docker Compose (Recommended for Testing)

1. **Clone Repository:**

```bash
git clone https://github.com/yourusername/OpenMediaTrust.git
cd OpenMediaTrust
```

2. **Configure Environment:**

```bash
cp config/config.example.yaml config/config.yaml
# Edit config.yaml with your settings
```

3. **Start Services:**

```bash
docker-compose up -d
```

4. **Initialize Database:**

```bash
docker-compose exec api python scripts/init_db.py
```

5. **Verify Installation:**

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{"status": "healthy", "timestamp": "..."}
```

### Method 2: Manual Installation (Production)

#### 1. Install System Dependencies

**Ubuntu/Debian:**

```bash
sudo apt-get update
sudo apt-get install -y \
    python3.11 \
    python3.11-venv \
    python3-pip \
    postgresql-15 \
    redis-server \
    nginx \
    git
```

**RHEL/CentOS:**

```bash
sudo dnf install -y \
    python311 \
    python311-pip \
    postgresql15-server \
    redis \
    nginx \
    git
```

#### 2. Setup PostgreSQL

```bash
# Initialize database
sudo postgresql-setup --initdb

# Start PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database and user
sudo -u postgres psql <<EOF
CREATE DATABASE openmediatrust;
CREATE USER openmediatrust WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE openmediatrust TO openmediatrust;
EOF
```

#### 3. Setup MinIO (Object Storage)

```bash
# Download MinIO
wget https://dl.min.io/server/minio/release/linux-amd64/minio
chmod +x minio
sudo mv minio /usr/local/bin/

# Create data directory
sudo mkdir -p /data/minio

# Create systemd service
sudo tee /etc/systemd/system/minio.service <<EOF
[Unit]
Description=MinIO
After=network.target

[Service]
Type=simple
User=minio
Group=minio
ExecStart=/usr/local/bin/minio server /data/minio --console-address ":9001"
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

# Start MinIO
sudo systemctl start minio
sudo systemctl enable minio
```

#### 4. Install OpenMediaTrust

```bash
# Create application user
sudo useradd -r -s /bin/false openmediatrust

# Clone repository
cd /opt
sudo git clone https://github.com/yourusername/OpenMediaTrust.git
cd OpenMediaTrust

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure
cp config/config.example.yaml config/config.yaml
# Edit config.yaml with production settings

# Initialize database
python scripts/init_db.py

# Set permissions
sudo chown -R openmediatrust:openmediatrust /opt/OpenMediaTrust
```

#### 5. Setup Systemd Services

**API Service:**

```bash
sudo tee /etc/systemd/system/openmediatrust-api.service <<EOF
[Unit]
Description=OpenMediaTrust API
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=openmediatrust
Group=openmediatrust
WorkingDirectory=/opt/OpenMediaTrust
Environment="PATH=/opt/OpenMediaTrust/venv/bin"
ExecStart=/opt/OpenMediaTrust/venv/bin/uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF
```

**Worker Service:**

```bash
sudo tee /etc/systemd/system/openmediatrust-worker.service <<EOF
[Unit]
Description=OpenMediaTrust Worker
After=network.target redis.service

[Service]
Type=simple
User=openmediatrust
Group=openmediatrust
WorkingDirectory=/opt/OpenMediaTrust
Environment="PATH=/opt/OpenMediaTrust/venv/bin"
ExecStart=/opt/OpenMediaTrust/venv/bin/celery -A src.tasks worker --loglevel=info
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF
```

**Start Services:**

```bash
sudo systemctl daemon-reload
sudo systemctl start openmediatrust-api
sudo systemctl start openmediatrust-worker
sudo systemctl enable openmediatrust-api
sudo systemctl enable openmediatrust-worker
```

#### 6. Setup Nginx Reverse Proxy

```bash
sudo tee /etc/nginx/sites-available/openmediatrust <<EOF
upstream openmediatrust_api {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name openmediatrust.example.com;

    # Redirect to HTTPS
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name openmediatrust.example.com;

    ssl_certificate /etc/ssl/certs/openmediatrust.crt;
    ssl_certificate_key /etc/ssl/private/openmediatrust.key;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;

    # Proxy settings
    location / {
        proxy_pass http://openmediatrust_api;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # File upload limit
    client_max_body_size 100M;
}
EOF

sudo ln -s /etc/nginx/sites-available/openmediatrust /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### Method 3: Kubernetes Deployment

#### 1. Create Namespace

```yaml
# namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: openmediatrust
```

```bash
kubectl apply -f namespace.yaml
```

#### 2. Create ConfigMap

```yaml
# configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: openmediatrust-config
  namespace: openmediatrust
data:
  config.yaml: |
    application:
      name: "OpenMediaTrust"
      environment: "production"
    # ... rest of configuration
```

```bash
kubectl apply -f configmap.yaml
```

#### 3. Create Secrets

```bash
kubectl create secret generic openmediatrust-secrets \
  --from-literal=db-password='your_secure_password' \
  --from-literal=minio-access-key='admin' \
  --from-literal=minio-secret-key='your_secret' \
  --from-literal=jwt-secret='your_jwt_secret' \
  -n openmediatrust
```

#### 4. Deploy PostgreSQL

```yaml
# postgres-deployment.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  namespace: openmediatrust
spec:
  serviceName: postgres
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:15-alpine
        env:
        - name: POSTGRES_DB
          value: openmediatrust
        - name: POSTGRES_USER
          value: openmediatrust
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: openmediatrust-secrets
              key: db-password
        ports:
        - containerPort: 5432
        volumeMounts:
        - name: postgres-data
          mountPath: /var/lib/postgresql/data
  volumeClaimTemplates:
  - metadata:
      name: postgres-data
    spec:
      accessModes: [ "ReadWriteOnce" ]
      resources:
        requests:
          storage: 50Gi
```

#### 5. Deploy API

```yaml
# api-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: openmediatrust-api
  namespace: openmediatrust
spec:
  replicas: 3
  selector:
    matchLabels:
      app: openmediatrust-api
  template:
    metadata:
      labels:
        app: openmediatrust-api
    spec:
      containers:
      - name: api
        image: openmediatrust/api:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          value: "postgresql://openmediatrust:$(DB_PASSWORD)@postgres:5432/openmediatrust"
        envFrom:
        - secretRef:
            name: openmediatrust-secrets
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: openmediatrust-api
  namespace: openmediatrust
spec:
  selector:
    app: openmediatrust-api
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

```bash
kubectl apply -f postgres-deployment.yaml
kubectl apply -f api-deployment.yaml
```

## Post-Deployment Configuration

### 1. Create Admin User

```bash
# Via API
curl -X POST http://localhost:8000/api/v1/admin/users \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "admin",
    "username": "admin",
    "email": "admin@example.com",
    "roles": ["administrator"],
    "is_active": true
  }'
```

### 2. Generate Cryptographic Keys

```bash
# Generate ML-DSA keypair
python scripts/generate_keys.py --algorithm ml-dsa-65 --output keys/

# Generate certificate
python scripts/generate_cert.py \
  --key keys/ml-dsa-private.pem \
  --output certs/signing-cert.pem \
  --cn "OpenMediaTrust CA"
```

### 3. Setup Monitoring

**Prometheus:**

Access Prometheus at `http://localhost:9090`

**Grafana:**

1. Access Grafana at `http://localhost:3000`
2. Login with `admin/admin`
3. Add Prometheus data source
4. Import dashboards from `deployment/grafana-dashboards/`

### 4. Configure Backups

```bash
# Database backup script
sudo tee /etc/cron.daily/openmediatrust-backup <<EOF
#!/bin/bash
DATE=\$(date +%Y%m%d_%H%M%S)
BACKUP_DIR=/backups/openmediatrust
mkdir -p \$BACKUP_DIR

# Database backup
pg_dump -U openmediatrust openmediatrust | gzip > \$BACKUP_DIR/db_\$DATE.sql.gz

# Keep last 7 days
find \$BACKUP_DIR -name "db_*.sql.gz" -mtime +7 -delete
EOF

sudo chmod +x /etc/cron.daily/openmediatrust-backup
```

## Security Hardening

### 1. Firewall Configuration

```bash
# Allow only necessary ports
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

### 2. SSL/TLS Certificates

```bash
# Using Let's Encrypt
sudo apt-get install certbot python3-certbot-nginx
sudo certbot --nginx -d openmediatrust.example.com
```

### 3. HSM Integration

For production environments, integrate with Hardware Security Module:

```yaml
# config.yaml
crypto:
  hsm_enabled: true
  hsm_type: "pkcs11"
  hsm_library: "/usr/lib/softhsm/libsofthsm2.so"
  hsm_slot: 0
  hsm_pin: "your_hsm_pin"
```

## Maintenance

### Monitoring Logs

```bash
# API logs
sudo journalctl -u openmediatrust-api -f

# Worker logs
sudo journalctl -u openmediatrust-worker -f

# Nginx access logs
sudo tail -f /var/log/nginx/access.log
```

### Database Maintenance

```bash
# Vacuum database
sudo -u postgres psql openmediatrust -c "VACUUM ANALYZE;"

# Check table sizes
sudo -u postgres psql openmediatrust -c "
SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
"
```

### Updating

```bash
cd /opt/OpenMediaTrust
git pull
source venv/bin/activate
pip install -r requirements.txt
python scripts/migrate_db.py
sudo systemctl restart openmediatrust-api openmediatrust-worker
```

## Troubleshooting

### Common Issues

**Issue: API not starting**

```bash
# Check logs
sudo journalctl -u openmediatrust-api -n 100

# Common causes:
# - Database connection failure
# - Missing configuration
# - Port already in use
```

**Issue: High memory usage**

```bash
# Check worker processes
ps aux | grep celery

# Restart workers
sudo systemctl restart openmediatrust-worker
```

**Issue: Storage full**

```bash
# Check storage usage
df -h

# Archive old manifests
python scripts/archive_manifests.py --older-than 90
```

## Support

For issues and questions:
- GitHub Issues: https://github.com/yourusername/OpenMediaTrust/issues
- Documentation: https://docs.openmediatrust.org
- Email: support@openmediatrust.org
