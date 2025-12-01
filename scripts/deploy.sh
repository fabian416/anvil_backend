#!/bin/bash
set -e

# Deployment script for DeFi Chat Platform
# Usage: ./scripts/deploy.sh [staging|production]

ENVIRONMENT=${1:-staging}
NAMESPACE=$ENVIRONMENT

echo "🚀 Deploying to $ENVIRONMENT environment..."

# Validate environment
if [[ "$ENVIRONMENT" != "staging" && "$ENVIRONMENT" != "production" ]]; then
    echo "❌ Invalid environment. Use 'staging' or 'production'"
    exit 1
fi

# Check kubectl access
echo "🔍 Checking kubectl access..."
kubectl cluster-info || {
    echo "❌ Cannot connect to Kubernetes cluster"
    exit 1
}

# Check namespace
kubectl get namespace $NAMESPACE 2>/dev/null || {
    echo "📦 Creating namespace $NAMESPACE..."
    kubectl create namespace $NAMESPACE
}

# Apply ConfigMaps
echo "📝 Applying ConfigMaps..."
kubectl apply -f k8s/configmap.yaml -n $NAMESPACE

# Apply Secrets (if not exists)
echo "🔐 Checking Secrets..."
kubectl get secret defi-chat-secrets -n $NAMESPACE 2>/dev/null || {
    echo "⚠️  Secrets not found. Please create them first:"
    echo "kubectl create secret generic defi-chat-secrets \\"
    echo "  --from-literal=database-url=postgresql://... \\"
    echo "  --from-literal=redis-url=redis://... \\"
    echo "  --from-literal=jwt-secret=... \\"
    echo "  --from-literal=oneinch-api-key=... \\"
    echo "  -n $NAMESPACE"
    exit 1
}

# Apply Deployment
echo "🎯 Deploying application..."
kubectl apply -f k8s/deployment.yaml -n $NAMESPACE

# Apply Service
echo "🌐 Creating service..."
kubectl apply -f k8s/service.yaml -n $NAMESPACE

# Apply Ingress (production only)
if [[ "$ENVIRONMENT" == "production" ]]; then
    echo "🔗 Configuring ingress..."
    kubectl apply -f k8s/ingress.yaml -n $NAMESPACE
fi

# Wait for rollout
echo "⏳ Waiting for rollout to complete..."
kubectl rollout status deployment/defi-chat -n $NAMESPACE --timeout=5m || {
    echo "❌ Rollout failed"
    kubectl rollout undo deployment/defi-chat -n $NAMESPACE
    exit 1
}

# Run health checks
echo "🏥 Running health checks..."
sleep 10

POD=$(kubectl get pod -n $NAMESPACE -l app=defi-chat -o jsonpath="{.items[0].metadata.name}")
kubectl exec -n $NAMESPACE $POD -- curl -f http://localhost:8000/health || {
    echo "❌ Health check failed"
    exit 1
}

kubectl exec -n $NAMESPACE $POD -- curl -f http://localhost:8000/health/ready || {
    echo "❌ Readiness check failed"
    exit 1
}

# Get deployment info
echo ""
echo "✅ Deployment successful!"
echo ""
echo "📊 Deployment Info:"
kubectl get deployment defi-chat -n $NAMESPACE
echo ""
echo "🎯 Pods:"
kubectl get pods -n $NAMESPACE -l app=defi-chat
echo ""
echo "🌐 Service:"
kubectl get svc defi-chat -n $NAMESPACE

if [[ "$ENVIRONMENT" == "production" ]]; then
    echo ""
    echo "🔗 Ingress:"
    kubectl get ingress defi-chat -n $NAMESPACE
    echo ""
    echo "🌍 Application URL: https://api.defi-chat.example.com"
fi

echo ""
echo "📝 View logs:"
echo "kubectl logs -f deployment/defi-chat -n $NAMESPACE"
echo ""
echo "🔍 Monitor:"
echo "kubectl get pods -n $NAMESPACE -w"
