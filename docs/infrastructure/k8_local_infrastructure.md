# Local K8 Infrastructure Components

## Data Layer:

- ✅ PostgreSQL - Primary database with persistent storage
- ✅ Redis - Caching and session storage
- ✅ MongoDB - DynamoDB alternative for NoSQL needs
- ✅ MinIO - S3-compatible object storage for media

## Security & Identity:

- ✅ Keycloak - Identity and access management
- ✅ HashiCorp Vault - Secrets management
- ✅ Kubernetes Secrets - Built-in secret storage

## API & Networking:

- ✅ Kong API Gateway - Rate limiting, routing, plugins
- ✅ NGINX Ingress Controller - External traffic routing
- ✅ NATS - Message broker for event-driven architecture

## Processing & Jobs:

- ✅ Kubernetes Jobs - One-time media processing tasks
- ✅ CronJobs - Scheduled tasks (indexing, cleanup)

## Monitoring:

- ✅ Prometheus - Metrics collection
- ✅ Grafana - Visualization and dashboards

## Quick Deployment:
Apply all infrastructure
```
kubectl apply -f thmnayah-infrastructure.yaml
```

## Verify deployments
```
kubectl get all -n thmnayah
```

## Access services locally
```
kubectl port-forward -n thmnayah svc/grafana-service 3000:3000
kubectl port-forward -n thmnayah svc/keycloak-service 8080:8080
kubectl port-forward -n thmnayah svc/minio-service 9001:9001
```
