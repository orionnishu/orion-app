#!/usr/bin/env python3
import os
import sys
import time
import json
import socket
import logging
import subprocess
import urllib.request
import urllib.parse
from datetime import datetime

# --- Configuration ---
REDIS_HOST = "100.117.244.106"
REDIS_PORT = 6379
PUSHGATEWAY_URL = "http://100.117.244.106:9091/metrics/job/orion_jobs/instance"
PI_API_BASE = "http://100.90.202.45:8000/admin/api"
API_USER = "orion"
API_PASS = "orion1812"

IDLE_TIMEOUT_SEC = 600  # 10 minutes
POLL_INTERVAL_SEC = 5

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_node_name():
    return socket.gethostname()

NODE_NAME = get_node_name()

def push_metrics(job_id, status, duration):
    try:
        data = f'orion_job_duration_seconds{{job_id="{job_id}",status="{status}"}} {duration}\n'
        req = urllib.request.Request(f"{PUSHGATEWAY_URL}/{NODE_NAME}", data=data.encode('utf-8'), method='POST')
        urllib.request.urlopen(req, timeout=5)
    except Exception as e:
        logging.error(f"Failed to push metrics: {e}")

def self_shutdown():
    logging.info("Idle timeout reached. Requesting self-shutdown via Pi API...")
    try:
        passman = urllib.request.HTTPPasswordMgrWithDefaultRealm()
        passman.add_password(None, PI_API_BASE, API_USER, API_PASS)
        authhandler = urllib.request.HTTPBasicAuthHandler(passman)
        opener = urllib.request.build_opener(authhandler)
        urllib.request.install_opener(opener)
        
        req = urllib.request.Request(f"{PI_API_BASE}/node/{NODE_NAME}/stop", method='POST')
        urllib.request.urlopen(req, timeout=10)
        logging.info("Shutdown request sent successfully. Goodnight!")
    except Exception as e:
        logging.error(f"Shutdown request failed: {e}. Falling back to local poweroff.")
        subprocess.run(["sudo", "poweroff"])
    
    sys.exit(0)

def main():
    logging.info(f"Orion Worker starting on {NODE_NAME}")
    
    try:
        import redis
    except ImportError:
        logging.error("redis module not installed. Please run 'pip install redis'")
        sys.exit(1)

    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    
    # Determine queue based on hostname
    queue_name = "orion:queue:default"
    if "cloud1-vm1" in NODE_NAME:
        queue_name = "orion:queue:large"
    elif "cloud2-vm1" in NODE_NAME:
        queue_name = "orion:queue:medium"

    logging.info(f"Listening on queue: {queue_name}")
    
    last_job_time = time.time()
    
    # Register worker
    r.hset("orion:workers", NODE_NAME, json.dumps({
        "status": "idle",
        "last_seen": time.time(),
        "queue": queue_name
    }))

    while True:
        try:
            # Check idle timeout FIRST
            if time.time() - last_job_time > IDLE_TIMEOUT_SEC:
                r.hdel("orion:workers", NODE_NAME)
                self_shutdown()
                
            # Update heartbeat
            current_data = r.hget("orion:workers", NODE_NAME)
            if current_data:
                data = json.loads(current_data)
                data["last_seen"] = time.time()
                r.hset("orion:workers", NODE_NAME, json.dumps(data))

            # Poll for job (blocking for 5 seconds)
            job = r.blpop(queue_name, timeout=POLL_INTERVAL_SEC)
            if not job:
                continue

            _, job_data_str = job
            job_data = json.loads(job_data_str)
            job_id = job_data.get("id", f"job-{int(time.time())}")
            command = job_data.get("command")
            
            if not command:
                logging.warning(f"Job {job_id} has no command. Skipping.")
                continue

            logging.info(f"Processing job {job_id}: {command}")
            
            # Set status to working
            data["status"] = "working"
            data["current_job"] = job_id
            r.hset("orion:workers", NODE_NAME, json.dumps(data))
            
            start_time = time.time()
            
            # Execute the job
            process = subprocess.run(command, shell=True, capture_output=True, text=True)
            
            duration = time.time() - start_time
            status = "success" if process.returncode == 0 else "failed"
            
            logging.info(f"Job {job_id} {status} in {duration:.2f}s")
            
            # Save results
            result_key = f"orion:result:{job_id}"
            r.set(result_key, json.dumps({
                "job_id": job_id,
                "node": NODE_NAME,
                "status": status,
                "duration": duration,
                "exit_code": process.returncode,
                "stdout": process.stdout,
                "stderr": process.stderr,
                "completed_at": time.time()
            }))
            r.expire(result_key, 86400) # Keep results for 24h
            
            # Record metrics
            push_metrics(job_id, status, duration)
            
            # Reset idle timer and status
            last_job_time = time.time()
            data["status"] = "idle"
            data["current_job"] = None
            r.hset("orion:workers", NODE_NAME, json.dumps(data))

        except KeyboardInterrupt:
            logging.info("Shutting down worker...")
            r.hdel("orion:workers", NODE_NAME)
            break
        except Exception as e:
            logging.error(f"Worker error: {e}")
            time.time() # just backoff slightly
            time.sleep(5)

if __name__ == "__main__":
    main()
