#!/bin/bash
# Setup script for the Raspberry Pi to install Redis as a replica of VM2

echo "Installing Redis Server natively..."
sudo apt-get update
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y redis-server

echo "Configuring Redis..."
# Bind exclusively to localhost and the Tailscale IP
sudo sed -i 's/^bind 127.0.0.1 -::1/bind 127.0.0.1 100.90.202.45/' /etc/redis/redis.conf

# Enable AOF persistence
sudo sed -i 's/^appendonly no/appendonly yes/' /etc/redis/redis.conf

# Set as replica of VM2's redis-primary container (100.117.244.106 on port 6379)
if ! grep -q "replicaof 100.117.244.106 6379" /etc/redis/redis.conf; then
    echo "replicaof 100.117.244.106 6379" | sudo tee -a /etc/redis/redis.conf
fi

echo "Restarting Redis..."
sudo systemctl restart redis-server

echo "Redis replication is configured! Check status with: redis-cli info replication"
