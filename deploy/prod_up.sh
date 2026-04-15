#!/bin/bash
# Aviation Singularity - Production Launch Script

echo "🛫 Preparing for takeoff (Aviation Singularity v27.0)..."

# Ensure log directory exists and has correct permissions
mkdir -p logs backups
chmod 777 logs

# Check for .env file
if [ ! -f .env ]; then
    echo "⚠️ .env file missing. Using environment defaults."
fi

# Build and Start
docker compose up --build -d

echo "📊 Waiting for systems to stabilize..."
sleep 5

# Check core health
curl -fsS http://localhost:8501/healthz > /dev/null
if [ $? -eq 0 ]; then
    echo "✅ Core Platform is UP and Healthy."
else
    echo "❌ Core Platform failed health check. Check logs with 'docker compose logs aviation-core'"
fi

echo "✨ Deployment Complete. Access Dashboard at Port 8501 or via Reverse Proxy Port 80."
