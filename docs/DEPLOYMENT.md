# Deployment Guide

## Production Deployment

### Infrastructure Requirements

#### Compute Resources
- **Supervisor Agent**: 4 vCPU, 8GB RAM
- **Data Enrichment Agent**: 8 vCPU, 16GB RAM (API intensive)
- **Risk Scoring Agent**: 4 vCPU, 8GB RAM
- **Context Builder Agent**: 4 vCPU, 8GB RAM
- **Decision Maker Agent**: 4 vCPU, 8GB RAM

#### External Services
- **PostgreSQL**: 12+ (for alert records and audit trails)
- **Redis**: 6+ (for caching and agent state)
- **Message Queue**: RabbitMQ or Kafka (for inter-agent communication)

### Docker Deployment

#### Build Docker Image

```dockerfile
# Dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry

# Copy project files
COPY pyproject.toml poetry.lock ./
COPY src/ ./src/

# Install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-dev --no-interaction --no-ansi

# Expose port
EXPOSE 8000

# Run application
CMD ["python", "-m", "aml_triage"]
```

Build and run:
```bash
docker build -t aml-triage:latest .
docker run -e ANTHROPIC_API_KEY=your_key aml-triage:latest
```

### Kubernetes Deployment

#### Deployment YAML

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: aml-triage-supervisor
  labels:
    app: aml-triage
    component: supervisor
spec:
  replicas: 3
  selector:
    matchLabels:
      app: aml-triage
      component: supervisor
  template:
    metadata:
      labels:
        app: aml-triage
        component: supervisor
    spec:
      containers:
      - name: supervisor
        image: aml-triage:latest
        resources:
          requests:
            memory: "8Gi"
            cpu: "4"
          limits:
            memory: "16Gi"
            cpu: "8"
        env:
        - name: ANTHROPIC_API_KEY
          valueFrom:
            secretKeyRef:
              name: llm-credentials
              key: anthropic-api-key
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: database-credentials
              key: url
        - name: REDIS_URL
          valueFrom:
            configMapKeyRef:
              name: aml-triage-config
              key: redis-url
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: aml-triage-service
spec:
  selector:
    app: aml-triage
  ports:
  - port: 8000
    targetPort: 8000
  type: LoadBalancer
```

Deploy:
```bash
kubectl apply -f deployment.yaml
```

### Environment Configuration

#### Production .env

```env
# LLM API Keys
ANTHROPIC_API_KEY=sk-ant-xxx
OPENAI_API_KEY=sk-xxx

# Database
DATABASE_URL=postgresql://user:password@postgres-host:5432/aml_triage
REDIS_URL=redis://redis-host:6379/0

# Agent Models
SUPERVISOR_MODEL=claude-sonnet-4-5-20250929
DATA_ENRICHMENT_MODEL=claude-haiku-4-5-20250929
RISK_SCORING_MODEL=claude-sonnet-4-5-20250929
CONTEXT_BUILDER_MODEL=claude-sonnet-4-5-20250929
DECISION_MAKER_MODEL=claude-opus-4-5-20251101

# Thresholds
AUTO_CLEAR_THRESHOLD=0.85
ESCALATE_L2_THRESHOLD=0.70
RISK_SCORE_HIGH_THRESHOLD=70
RISK_SCORE_SEVERE_THRESHOLD=85

# Performance
MAX_CONCURRENT_ALERTS=50
AGENT_TIMEOUT_SECONDS=30
MAX_RETRIES=3

# Monitoring
PROMETHEUS_PORT=9090
LOG_LEVEL=INFO

# External APIs
EXTERNAL_DATA_API_KEY=xxx
EXTERNAL_DATA_API_URL=https://api.example.com/v1
```

### Database Setup

#### Initialize PostgreSQL

```sql
-- Create database
CREATE DATABASE aml_triage;

-- Create user
CREATE USER aml_user WITH PASSWORD 'secure_password';

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE aml_triage TO aml_user;

-- Connect to database
\c aml_triage

-- Create tables (run migrations)
-- Tables will be created by application migrations
```

#### Run Migrations

```bash
poetry run alembic upgrade head
```

### Redis Configuration

```conf
# redis.conf
maxmemory 4gb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
```

### Monitoring Setup

#### Prometheus Configuration

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'aml-triage'
    static_configs:
      - targets: ['localhost:9090']
    metrics_path: /metrics
```

#### Grafana Dashboard

Import dashboard for monitoring:
- Alert processing rate
- Agent latency (P50, P95, P99)
- Error rates
- Decision disposition breakdown
- Confidence score distribution

### Load Balancing

#### NGINX Configuration

```nginx
upstream aml_triage {
    least_conn;
    server app1:8000;
    server app2:8000;
    server app3:8000;
}

server {
    listen 80;
    server_name aml-triage.example.com;

    location / {
        proxy_pass http://aml_triage;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    location /health {
        proxy_pass http://aml_triage;
        access_log off;
    }
}
```

### Auto-Scaling Configuration

#### Horizontal Pod Autoscaler

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: aml-triage-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: aml-triage-supervisor
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### Security Hardening

#### API Key Management

Use secrets management:
```bash
# Kubernetes secrets
kubectl create secret generic llm-credentials \
  --from-literal=anthropic-api-key='sk-ant-xxx'

# AWS Secrets Manager
aws secretsmanager create-secret \
  --name aml-triage/anthropic-key \
  --secret-string 'sk-ant-xxx'
```

#### Network Security

```yaml
# NetworkPolicy for pod isolation
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: aml-triage-policy
spec:
  podSelector:
    matchLabels:
      app: aml-triage
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: api-gateway
    ports:
    - protocol: TCP
      port: 8000
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: postgresql
    ports:
    - protocol: TCP
      port: 5432
  - to:
    - podSelector:
        matchLabels:
          app: redis
    ports:
    - protocol: TCP
      port: 6379
```

### Backup and Recovery

#### Database Backups

```bash
# Automated daily backups
0 2 * * * pg_dump -U aml_user -h postgres-host aml_triage | gzip > /backups/aml_triage_$(date +\%Y\%m\%d).sql.gz

# Retention policy: keep 30 days
find /backups -name "aml_triage_*.sql.gz" -mtime +30 -delete
```

#### Disaster Recovery

```bash
# Restore from backup
gunzip -c /backups/aml_triage_20240115.sql.gz | psql -U aml_user -h postgres-host aml_triage
```

### Performance Optimization

#### Redis Caching Strategy

```python
# Cache configuration
CACHE_TTL = 900  # 15 minutes
CACHE_PREFIX = "aml_triage:"

# Cache keys
HISTORICAL_DATA_KEY = f"{CACHE_PREFIX}historical:{{customer_id}}"
SCREENING_RESULTS_KEY = f"{CACHE_PREFIX}screening:{{entity_name}}"
```

#### Database Indexing

```sql
-- Create indexes for performance
CREATE INDEX idx_alerts_customer_id ON alerts(customer_id);
CREATE INDEX idx_alerts_timestamp ON alerts(timestamp DESC);
CREATE INDEX idx_decisions_disposition ON decisions(disposition);
CREATE INDEX idx_audit_entries_alert_id ON audit_entries(alert_id);
```

### Logging and Observability

#### Centralized Logging

Use ELK stack or similar:
```yaml
# Filebeat configuration
filebeat.inputs:
- type: log
  enabled: true
  paths:
    - /var/log/aml-triage/*.log
  json.keys_under_root: true
  json.add_error_key: true

output.elasticsearch:
  hosts: ["elasticsearch:9200"]
  index: "aml-triage-%{+yyyy.MM.dd}"
```

#### Distributed Tracing

```python
# Add OpenTelemetry for tracing
from opentelemetry import trace
from opentelemetry.exporter.jaeger import JaegerExporter

# Configure tracer
tracer = trace.get_tracer(__name__)

# Instrument code
with tracer.start_as_current_span("process_alert"):
    decision = await system.process_alert(alert)
```

### Health Checks

```python
# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "0.1.0"
    }

@app.get("/ready")
async def readiness_check():
    # Check dependencies
    checks = {
        "database": await check_database(),
        "redis": await check_redis(),
        "llm_api": await check_llm_api()
    }

    if all(checks.values()):
        return {"status": "ready", "checks": checks}
    else:
        raise HTTPException(status_code=503, detail=checks)
```

### Rollout Strategy

#### Blue-Green Deployment

```bash
# Deploy to green environment
kubectl apply -f deployment-green.yaml

# Verify green environment
kubectl exec -it green-pod -- pytest

# Switch traffic to green
kubectl patch service aml-triage-service \
  -p '{"spec":{"selector":{"version":"green"}}}'

# Monitor for issues
# If successful, decommission blue
# If issues, rollback to blue
```

### Maintenance

#### Regular Tasks

1. **Daily**:
   - Monitor error rates
   - Review failed alerts
   - Check system performance

2. **Weekly**:
   - Review agent performance metrics
   - Analyze decision accuracy
   - Update model prompts if needed

3. **Monthly**:
   - Database maintenance (VACUUM, ANALYZE)
   - Review and rotate logs
   - Update dependencies
   - Performance benchmarking

4. **Quarterly**:
   - Security audit
   - Disaster recovery test
   - Capacity planning review
   - Model retraining evaluation

### Troubleshooting

#### Common Production Issues

**High Latency**:
```bash
# Check agent processing times
kubectl logs -l app=aml-triage --tail=100 | grep processing_time_ms

# Verify external API latency
curl -w "@curl-format.txt" -o /dev/null -s https://api.anthropic.com/v1/health
```

**Memory Issues**:
```bash
# Check memory usage
kubectl top pods -l app=aml-triage

# Scale up if needed
kubectl scale deployment aml-triage-supervisor --replicas=5
```

**Database Connections**:
```bash
# Check active connections
psql -U aml_user -c "SELECT count(*) FROM pg_stat_activity;"

# Increase connection pool if needed
# Update DATABASE_MAX_CONNECTIONS in config
```

## Compliance Checklist

- [ ] All API keys stored in secrets management
- [ ] Database encrypted at rest
- [ ] Network traffic encrypted (TLS)
- [ ] Audit logs enabled and retained
- [ ] Backup and recovery tested
- [ ] Access controls configured (RBAC)
- [ ] Monitoring and alerting active
- [ ] Incident response plan documented
- [ ] Data retention policy enforced
- [ ] Regular security audits scheduled
