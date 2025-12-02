#!/bin/bash
# Simple endpoint counter - counts @router.{method} decorators

cd /home/ubuntu/anvil_backend/src/app/presentation/http/controllers

echo "=== Endpoint Count by Router File ==="
for file in $(find . -name "*router.py" | sort); do
    count=$(grep -E "@router\.(get|post|put|patch|delete)" "$file" | wc -l)
    if [ $count -gt 0 ]; then
        echo "$file: $count endpoints"
    fi
done

echo ""
echo "=== Total Endpoint Count ==="
grep -rE "@router\.(get|post|put|patch|delete)" . | wc -l
