#!/bin/bash
set -e

# Check for token
if [ -z "$GITHUB_PAT" ]; then
  echo "❌ GITHUB_PAT is not set. Aborting."
  exit 1
fi

# Export model metadata
poetry run python src/model/export_mlflow_models.py

# Clone or pull frontend repo
if [ -d "smartCharge-frontend/.git" ]; then
  echo "✅ Frontend repo already cloned. Pulling latest..."
  cd smartCharge-frontend
  git pull
  cd ..
else
  git clone https://x-access-token:$GITHUB_PAT@github.com/BlazheManev/smartCharge-frontend.git
fi

# Copy file
cp public/ml_models.json smartCharge-frontend/public/ml_models.json

# Commit + push
cd smartCharge-frontend
git config user.name "mlflow-bot"
git config user.email "mlflow@automation.com"
git add public/ml_models.json
git commit -m "📦 Auto-update ml_models.json from DVC pipeline" || echo "No changes to commit"
git push || echo "Push failed"
