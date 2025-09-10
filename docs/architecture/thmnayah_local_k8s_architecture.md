# Thmnayah - Local Kubernetes Architecture

## Architecture Overview

This document outlines the local Kubernetes architecture for Thmnayah, providing equivalent functionality to the AWS cloud architecture but deployed on a local Kubernetes cluster for development, testing, or on-premises deployment.

## Core Components & Kubernetes Services

### 1. **Ingress & Load Balancing**
```
┌─────────────────────────────────────────────────────────────┐
│                    External Users                            │
└─────────────────┬───────────────────────────────────────────┘
                  │
         ┌────────▼────────┐
         │   NGINX Ingress │ ◄── Ingress Controller + SSL
         │   Controller    │
         └────────┬────────┘
                  │
    ┌─────────────▼─────────────┐
    │   Kubernetes Services     │ ◄── Load Balancing & Service Discovery
    │   (ClusterIP/NodePort)    │
    └─────────────┬─────────────┘
                  │
         ┌────────▼────────┐
         │   API Gateway   │ ◄── Kong/Ambassador (Rate Limiting, Auth)
         │   (Kong/Envoy)  │
         └─────────────────┘
```

### 2. **Application Layer (Pods & Deployments)**
```
┌─────────────────────────────────────────────────────────────┐
│                  Kubernetes Cluster                         │
├─────────────────┬──────────────────┬────────────────────────┤
│   CMS Services  │ Discovery APIs   │   Background Workers   │
│   (Deployment)  │   (Deployment)   │   (Jobs/CronJobs)      │
│   - Replicas: 2 │   - Replicas: 3  │   - Media Processing   │
│   - Private     │   - Public       │   - Indexing Tasks     │
└─────────────────┴──────────────────┴────────────────────────┘
```

### 3. **Data Storage Layer**
```
┌─────────────────────────────────────────────────────────────┐
│                     Data Storage                            │
├────────────────┬─────────────────┬──────────────────────────┤
│   PostgreSQL   │    MongoDB/     │    MinIO/Local Storage   │
│   (StatefulSet │    Redis        │    (S3-Compatible)       │
│   + PV/PVC)    │   (StatefulSet) │                          │
└────────────────┴─────────────────┴──────────────────────────┘
```

## Detailed Service Architecture

### **Frontend & Content Delivery**
- **NGINX Ingress**: Traffic routing, SSL termination, rate limiting
- **Static File Server**: NGINX pod serving React build files
- **MinIO**: S3-compatible object storage for media files
- **Local DNS**: CoreDNS for internal service discovery

### **API & Authentication Layer**
- **Kong API Gateway**: 
  - Rate limiting, authentication, CORS
  - Plugin ecosystem for extensibility
  - Alternative: Ambassador or Envoy Gateway
- **Keycloak**: Self-hosted identity and access management
  - OAuth2/OpenID Connect
  - User federation
  - Role-based access control

### **Application Services**
```yaml
# Example Deployment Structure
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cms-service
spec:
  replicas: 2
  selector:
    matchLabels:
      app: cms-service
  template:
    spec:
      containers:
      - name: cms-api
        image: thmnayah/cms:latest
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi" 
            cpu: "500m"
```

### **Data & Storage**
- **PostgreSQL StatefulSet**: 
  - Primary/replica configuration
  - Persistent volumes for data persistence
  - Automated backups with pg_dump CronJobs
- **Redis StatefulSet**: 
  - Session storage, caching layer
  - Redis Sentinel for high availability
- **MinIO Cluster**: 
  - S3-compatible API
  - Distributed storage across nodes
  - Built-in versioning and lifecycle policies

### **Rich Content & Media Processing**
```
Media Upload → MinIO → Kubernetes Job → FFmpeg/Processing → MinIO Output
                ↓
            Event System → Multiple Processing Workflows
```
- **Kubernetes Jobs**: 
  - Video transcoding with FFmpeg
  - Image processing with ImageMagick
  - Audio processing pipelines
- **Custom Operators**: 
  - Media processing workflows
  - Content moderation pipelines

### **Search Infrastructure**
```
Content Changes → Event Bus → Worker Pods → Elasticsearch Indexing
                                         ↓
User Search Queries ← API Gateway ← Elasticsearch Cluster
```
- **Elasticsearch Cluster**: 
  - StatefulSet deployment
  - Multiple data/master nodes
  - Kibana for search analytics
- **Event Processing**: 
  - Apache Kafka or NATS for event streaming
  - Worker pods for real-time indexing

### **Workflows & Automation**
- **Argo Workflows**: Complex workflow orchestration
- **Apache Kafka/NATS**: Event-driven messaging
- **Kubernetes CronJobs**: Scheduled tasks
- **Custom Controllers**: Domain-specific automation

### **Personalization Engine**
- **Apache Spark**: ML processing on Kubernetes
- **MLflow**: Model management and deployment
- **Custom ML Services**: Recommendation engines
- **Feature Store**: Redis/PostgreSQL for ML features

### **Compliance & Security**
- **Falco**: Runtime security monitoring
- **Open Policy Agent (OPA)**: Policy enforcement
- **Cert-Manager**: Automated SSL certificate management
- **Vault**: Secrets management (HashiCorp Vault)

## Kubernetes-Specific Components

### **Networking**
```yaml
# Service Mesh (Optional - Istio)
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: thmnayah-gateway
spec:
  hosts:
  - thmnayah.local
  gateways:
  - thmnayah-gateway
  http:
  - match:
    - uri:
        prefix: /api/cms
    route:
    - destination:
        host: cms-service
        port:
          number: 8000
```

### **Storage Classes**
```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: fast-ssd
provisioner: kubernetes.io/no-provisioner
parameters:
  type: local-ssd
volumeBindingMode: WaitForFirstConsumer
```

### **Monitoring & Observability**
- **Prometheus Stack**: 
  - Metrics collection and alerting
  - Grafana for visualization
  - AlertManager for notifications
- **Jaeger**: Distributed tracing
- **Fluent Bit**: Log aggregation
- **ELK Stack**: Centralized logging (alternative)

## Local Development Setup

### **Development Environment**
```bash
# Local cluster options
- Kind (Kubernetes in Docker)
- Minikube 
- Docker Desktop Kubernetes
- k3s/k3d for lightweight deployment
```

### **Required Resources**
```
Minimum Hardware:
- CPU: 8 cores
- Memory: 16GB RAM  
- Storage: 100GB SSD
- Network: Gigabit Ethernet

Recommended:
- CPU: 16 cores
- Memory: 32GB RAM
- Storage: 500GB NVMe SSD
```

## Service Mapping: AWS → Kubernetes

| AWS Service | Kubernetes Equivalent |
|-------------|----------------------|
| ECS/Fargate | Deployments/Pods |
| ALB | Ingress Controller |
| API Gateway | Kong/Ambassador |
| RDS | PostgreSQL StatefulSet |
| DynamoDB | MongoDB/Redis |
| S3 | MinIO |
| CloudFront | NGINX + Caching |
| Lambda | Kubernetes Jobs |
| SQS/SNS | Kafka/NATS |
| CloudWatch | Prometheus + Grafana |
| Cognito | Keycloak |
| Secrets Manager | Kubernetes Secrets/Vault |

## Deployment Strategy

### **GitOps Approach**
- **ArgoCD**: Continuous deployment
- **Flux**: Alternative GitOps operator  
- **Helm Charts**: Package management
- **Kustomize**: Configuration management

### **CI/CD Pipeline**
```
Git Push → GitHub Actions → Build Images → Push to Registry → ArgoCD Sync → Deploy
```

## Scalability Features

### **Horizontal Pod Autoscaling**
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: cms-service-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: cms-service
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

### **Cluster Autoscaling**
- **Cluster Autoscaler**: Node scaling based on demand
- **Vertical Pod Autoscaler**: Resource optimization
- **KEDA**: Event-driven autoscaling

## Architecture Benefits

### **Development Advantages**
- **Consistency**: Same environment as production
- **Faster iteration**: Local development and testing
- **Cost-effective**: No cloud costs during development
- **Offline capability**: Work without internet dependency

### **Production Benefits**
- **Vendor independence**: Avoid cloud lock-in
- **Data sovereignty**: Keep data on-premises
- **Custom hardware**: Optimize for specific workloads
- **Hybrid deployment**: Mix of cloud and on-premises

### **Operational Benefits**
- **Infrastructure as Code**: Everything version controlled
- **Declarative management**: Desired state configuration
- **Self-healing**: Automatic recovery from failures
- **Service mesh**: Advanced traffic management

## Next Steps
1. Set up local Kubernetes cluster (Kind/Minikube)
2. Deploy core infrastructure (PostgreSQL, Redis, MinIO)
3. Implement CI/CD pipeline with ArgoCD
4. Configure monitoring and observability stack
5. Deploy application services incrementally