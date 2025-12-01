#!/bin/bash
set -e

# Rollback script for DeFi Chat Platform
# Usage: ./scripts/rollback.sh [staging|production]

ENVIRONMENT=${1:-staging}
NAMESPACE=$ENVIRONMENT

echo "⏪ Rolling back deployment in $ENVIRONMENT..."

# Validate environment
if [[ "$ENVIRONMENT" != "staging" && "$ENVIRONMENT" != "production" ]]; then
    echo "❌ Invalid environment. Use 'staging' or 'production'"
    exit 1
fi

# Check current revision
echo "📊 Current deployment status:"
kubectl rollout status deployment/defi-chat -n $NAMESPACE

echo ""
echo "📜 Rollout history:"
kubectl rollout history deployment/defi-chat -n $NAMESPACE

# Confirm rollback
if [[ "$ENVIRONMENT" == "production" ]]; then
    read -p "⚠️  Rolling back PRODUCTION. Are you sure? (yes/no): " CONFIRM
    if [[ "$CONFIRM" != "yes" ]]; then
        echo "❌ Rollback cancelled"
        exit 1
    fi
fi

# Perform rollback
echo "⏪ Performing rollback..."
kubectl rollout undo deployment/defi-chat -n $NAMESPACE

# Wait for rollback
echo "⏳ Waiting for rollback to complete..."
kubectl rollout status deployment/defi-chat -n $NAMESPACE --timeout=5m

# Run health checks
echo "🏥 Running health checks..."
sleep 10

POD=$(kubectl get pod -n $NAMESPACE -l app=defi-chat -o jsonpath="{.items[0].metadata.name}")
kubectl exec -n $NAMESPACE $POD -- curl -f http://localhost:8000/health || {
    echo "❌ Health check failed after rollback"
    exit 1
}

echo ""
echo "✅ Rollback successful!"
echo ""
echo "📊 Current status:"
kubectl get deployment defi-chat -n $NAMESPACE
kubectl get pods -n $NAMESPACE -l app=defi-chat
