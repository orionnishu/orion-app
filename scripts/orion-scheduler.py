#!/usr/bin/env python3
import time
import json
import logging
import subprocess
import os

try:
    import redis
except ImportError:
    print("Error: redis module not installed.")
    import sys
    sys.exit(1)

# --- Configuration ---
REDIS_HOST = "100.117.244.106"
REDIS_PORT = 6379

QUEUE_MAP = {
    "orion:queue:medium": "cloud2-vm1",
    "orion:queue:large": "cloud1-vm1"
}

START_COOLDOWN_SEC = 300  # 5 minutes
WORKER_TIMEOUT_SEC = 300  # Consider worker dead if not seen in 5 minutes
POLL_INTERVAL_SEC = 10

ORION_NODE_CMD = "/home/orion/server/scripts/orion-node"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_active_workers_per_queue(r):
    """Returns a dict mapping queue_name -> count of active workers"""
    active_counts = {q: 0 for q in QUEUE_MAP.keys()}
    
    workers_data = r.hgetall("orion:workers")
    now = time.time()
    
    for worker_name, data_str in workers_data.items():
        try:
            data = json.loads(data_str)
            last_seen = data.get("last_seen", 0)
            queue = data.get("queue")
            
            # If the worker checked in recently, count it as active for its queue
            if now - last_seen < WORKER_TIMEOUT_SEC and queue in active_counts:
                active_counts[queue] += 1
                
        except json.JSONDecodeError:
            continue
            
    return active_counts

def main():
    logging.info("Starting Orion Job Scheduler...")
    
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    last_started = {node: 0 for node in QUEUE_MAP.values()}
    
    while True:
        try:
            active_workers = get_active_workers_per_queue(r)
            
            for queue, target_node in QUEUE_MAP.items():
                queue_len = r.llen(queue)
                
                if queue_len > 0:
                    workers_count = active_workers.get(queue, 0)
                    
                    if workers_count == 0:
                        # Jobs in queue, but no active workers! Schedule a start.
                        time_since_last_start = time.time() - last_started[target_node]
                        
                        if time_since_last_start > START_COOLDOWN_SEC:
                            logging.info(f"Queue {queue} has {queue_len} jobs but 0 active workers. Starting {target_node}...")
                            
                            # Trigger start (non-blocking)
                            subprocess.Popen(
                                [ORION_NODE_CMD, "start", target_node],
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL
                            )
                            
                            last_started[target_node] = time.time()
                            logging.info(f"Start command issued for {target_node}. Cooldown initialized.")
                        else:
                            logging.debug(f"Queue {queue} has jobs, no workers, but {target_node} is within start cooldown ({int(START_COOLDOWN_SEC - time_since_last_start)}s left).")
                    else:
                        logging.debug(f"Queue {queue} has {queue_len} jobs and {workers_count} active workers. Doing nothing.")
            
        except redis.ConnectionError as e:
            logging.error(f"Redis connection error: {e}")
        except Exception as e:
            logging.error(f"Unexpected error in scheduler: {e}")
            
        time.sleep(POLL_INTERVAL_SEC)

if __name__ == "__main__":
    main()
