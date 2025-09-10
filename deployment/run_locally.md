# 🔧 Quick Setup:
```bash
# 1. Create chart directory
mkdir -p thmnayah-helm/{templates,charts}

# 2. Add Bitnami repo
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update

# 3. Install NGINX Ingress
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.2/deploy/static/provider/cloud/deploy.yaml

# 4. Deploy Thmnayah
helm install thmnayah ./thmnayah-helm -n thmnayah --create-namespace

# 5. Add to hosts file
echo "127.0.0.1 thmnayah.local" >> /etc/hosts

# 6. Port forward (for local clusters)
kubectl port-forward -n ingress-nginx service/ingress-nginx-controller 8080:80
```

# 🌐 Test Your API:
```bash
# Hello endpoint (bilingual)
curl -H "Host: thmnayah.local" http://localhost:8080/api/hello

# Arabic endpoint
curl -H "Host: thmnayah.local" http://localhost:8080/api/hello/ar

# English endpoint  
curl -H "Host: thmnayah.local" http://localhost:8080/api/hello/en

# Health check
curl -H "Host: thmnayah.local" http://localhost:8080/health
```

# 🚀 Access Swagger UI:
```bash

# Open in browser
open http://thmnayah.local:8080/docs
```
