#!/bin/bash
# Deploy the worker agent to a specific worker VM
# Usage: ./deploy-worker.sh <worker-hostname>

WORKER=$1
if [ -z "$WORKER" ]; then
  echo "Usage: ./deploy-worker.sh <worker-hostname>"
  exit 1
fi

echo "Deploying Orion Worker Agent to $WORKER..."

# Transfer files
scp -o ProxyCommand="tailscale nc %h %p" ../../scripts/orion-worker.py ubuntu@$WORKER:/tmp/
scp -o ProxyCommand="tailscale nc %h %p" ../../scripts/orion-worker.service ubuntu@$WORKER:/tmp/

# Run setup commands securely over SSH
ssh -o ProxyCommand="tailscale nc %h %p" ubuntu@$WORKER << 'EOF'
  sudo mv /tmp/orion-worker.py /usr/local/bin/
  sudo chmod +x /usr/local/bin/orion-worker.py
  sudo mv /tmp/orion-worker.service /etc/systemd/system/
  
  sudo apt-get update
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y python3-redis prometheus-node-exporter
  
  sudo systemctl daemon-reload
  sudo systemctl enable --now orion-worker
  echo "Deployment successful!"
EOF
