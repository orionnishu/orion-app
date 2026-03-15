#!/bin/bash
# Deploy or update the worker agent to a specific worker VM
# Usage: ./deploy-worker.sh <worker-hostname>

WORKER=$1
if [ -z "$WORKER" ]; then
  echo "Usage: ./deploy-worker.sh <worker-hostname>"
  exit 1
fi

echo "Deploying Orion Worker Agent to $WORKER via Git..."

ssh -o ConnectTimeout=10 -o BatchMode=yes ubuntu@$WORKER << 'EOF'
  set -e
  
  # 1. Update repository
  echo "Updating repository..."
  if [ ! -d ~/server ]; then
    git clone https://github.com/orionnishu/orion-app.git ~/server
  fi
  cd ~/server
  git fetch origin
  git checkout cloud_integration
  git pull origin cloud_integration
  
  # 2. Install dependencies
  echo "Installing dependencies..."
  sudo apt-get update
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y python3-redis prometheus-node-exporter
  
  # 3. Symlink systemd service (if not already done)
  echo "Configuring service..."
  if [ ! -f /etc/systemd/system/orion-worker.service ]; then
    sudo ln -s /home/ubuntu/server/scripts/orion-worker.service /etc/systemd/system/orion-worker.service
  fi
  
  # 4. Reload and restart
  sudo systemctl daemon-reload
  sudo systemctl enable --now orion-worker
  sudo systemctl restart orion-worker
  
  echo "Deployment successful! Status:"
  systemctl status orion-worker --no-pager | grep Active
EOF
