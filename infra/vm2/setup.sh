#!/bin/bash
# Setup script for oracle-cloud2-vm2 (Infrastructure Node)
# Run this script from within the infra/vm2 directory on the VM itself, or
# copy the directory there and execute.

echo "Setting up VM2 Infrastructure Stack..."

# Create necessary directories
mkdir -p ~/orion-infra/stack/prometheus 
mkdir -p ~/orion-infra/stack/redis/data 
mkdir -p ~/orion-infra/stack/grafana/data

# Grafana requires specific permissions for its data volume
sudo chown -R 472:472 ~/orion-infra/stack/grafana/data

# Copy configurations
cp docker-compose.yml ~/orion-infra/stack/
cp prometheus/prometheus.yml ~/orion-infra/stack/prometheus/

# Start the stack
cd ~/orion-infra/stack
docker compose up -d

echo "Infrastructure stack is up!"
