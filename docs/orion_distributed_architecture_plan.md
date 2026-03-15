# ORION Distributed Edge--Cloud Architecture Plan (v1)

> [!WARNING]
> **This document is the original ChatGPT-generated plan and has been superseded.**
> The refined, implemented version is in [`docs/cloud_integration_plan.md`](cloud_integration_plan.md).
> This file is kept for historical reference only.

This document defines the **ORION distributed compute architecture**
using:

-   Raspberry Pi 5 (Edge Control Plane)
-   Oracle Cloud VM1 (Compute Worker -- Medium)
-   Oracle Cloud VM2 (Infrastructure + Gateway)
-   Oracle Cloud VM3 (Compute Worker -- Large)
-   Windows Desktop PC (Local Worker / Backup)

The goal is to create a **low-cost hybrid edge--cloud compute system**
where heavy workers run **on-demand** and shut down automatically when
idle.

------------------------------------------------------------------------

# 1. Node Inventory

  Node                Specs            Role
  ------------------- ---------------- -------------------------------
  Raspberry Pi 5      4 cores / 4GB    Edge Control Plane
  oracle-cloud2-vm1   3 OCPU / 18GB    Medium Compute Worker
  oracle-cloud2-vm2   1 OCPU / 6GB     Infrastructure + Gateway
  oracle-cloud1-vm1   4 OCPU / 23GB    Large Compute Worker
  Windows Desktop     6 cores / 16GB   Local Worker (Wake-on-demand)

------------------------------------------------------------------------

# 2. SSH Access Configuration

These hosts are already configured in `~/.ssh/config`.

    Host oracle-cloud2-vm1
        HostName 130.162.191.16
        User ubuntu
        IdentityFile ~/.ssh/orion-cloud2-vm1-ssh.key

    Host oracle-cloud2-vm2
        HostName 141.147.97.52
        User ubuntu
        IdentityFile ~/.ssh/orion-cloud2-vm2-ssh.key

    Host oracle-cloud1-vm1
        HostName 80.225.250.148
        User ubuntu
        IdentityFile ~/.ssh/orion-cloud1-vm1-ssh.key

Verify connectivity:

    ssh oracle-cloud2-vm1
    ssh oracle-cloud2-vm2
    ssh oracle-cloud1-vm1

------------------------------------------------------------------------

# 3. High-Level Architecture

                     Internet
                         |
                 oracle-cloud2-vm2
              (Gateway + Infrastructure)
                         |
                     Tailscale
                         |
                  Raspberry Pi 5
                Edge Control Plane
                         |
                   Redis Job Queue
                         |
            --------------------------------
            |                              |
    oracle-cloud2-vm1               oracle-cloud1-vm1
     Medium Worker                    Large Worker
       3 OCPU / 18GB                  4 OCPU / 23GB
            |
            |
        Windows PC (fallback worker)

------------------------------------------------------------------------

# 4. Always-On Nodes

These machines remain online permanently.

## Raspberry Pi (Edge Control Plane)

Responsibilities:

-   FastAPI dashboard
-   Mosquitto MQTT
-   ESP32 device communication
-   Redis job queue
-   Jellyfin
-   WebDAV
-   Pi-monitor
-   Task scheduler
-   Worker lifecycle manager

The Pi acts as the **brain of ORION**.

------------------------------------------------------------------------

## oracle-cloud2-vm2 (Infrastructure Node)

Specs:

    1 OCPU
    6GB RAM

Responsibilities:

-   Nginx reverse proxy
-   TLS termination
-   Grafana dashboards
-   Prometheus monitoring
-   Node exporter aggregation
-   System logging

Traffic flow:

    Internet → VM2 → Tailscale → Pi services

------------------------------------------------------------------------

# 5. On-Demand Workers

Workers normally remain **stopped** and are started only when jobs
exist.

------------------------------------------------------------------------

## oracle-cloud2-vm1 (Medium Worker)

Specs:

    3 OCPU
    18GB RAM

Best suited for:

-   ffmpeg transcoding
-   Python batch processing
-   moderate AI inference
-   data analysis tasks

Typical concurrency:

    2–4 jobs

------------------------------------------------------------------------

## oracle-cloud1-vm1 (Large Worker)

Specs:

    4 OCPU
    23GB RAM

Best suited for:

-   large compute tasks
-   parallel workloads
-   AI pipelines
-   heavy transcoding

Typical concurrency:

    4–8 jobs

------------------------------------------------------------------------

## Windows Desktop Worker

Specs:

    6 cores
    16GB RAM

Used when:

-   cloud workers unavailable
-   GPU workload required
-   large local compute needed

Activation:

-   Wake-on-LAN
-   ESP32 power button fallback

------------------------------------------------------------------------

# 6. Worker Lifecycle

Workers follow this lifecycle.

    OFF
     ↓
    Job arrives
     ↓
    Scheduler decides worker type
     ↓
    Start VM
     ↓
    Worker registers
     ↓
    Execute tasks
     ↓
    Idle timeout
     ↓
    Shutdown VM

------------------------------------------------------------------------

# 7. Job Execution Pipeline

    User action
         |
    FastAPI (Pi)
         |
    Redis Queue
         |
    Scheduler
         |
    ------------------------------
    |                            |
    VM1 Worker               VM3 Worker

Workers pull jobs from Redis.

------------------------------------------------------------------------

# 8. Worker Selection Strategy

Scheduler priority order:

1.  oracle-cloud2-vm1 (medium worker)
2.  oracle-cloud1-vm1 (large worker)
3.  Windows Desktop

Cloud workers are preferred to **minimize local power usage**.

------------------------------------------------------------------------

# 9. Worker Registration Protocol

Workers register with the Pi when they start.

Example payload:

    {
      "node": "oracle-cloud1-vm1",
      "cpu": 4,
      "ram": 23,
      "slots": 6
    }

Registration allows the scheduler to allocate jobs dynamically.

------------------------------------------------------------------------

# 10. Idle Shutdown Policy

Workers shut down automatically when idle.

Example logic:

    if no jobs for 10 minutes:
        shutdown worker VM

VM shutdown may be triggered by:

-   OCI CLI
-   ORION control scripts

------------------------------------------------------------------------

# 11. Daily Keep-Alive Task

Oracle sometimes reclaims unused free-tier resources.

Each worker VM should run **once per day**.

Example:

    start VM
    run health check
    run small compute job
    shutdown VM

Possible tasks:

-   system updates
-   backup verification
-   compute benchmark

------------------------------------------------------------------------

# 12. Monitoring

Prometheus on VM2 monitors:

-   Raspberry Pi
-   oracle-cloud2-vm1
-   oracle-cloud2-vm2
-   oracle-cloud1-vm1
-   Windows Desktop

Metrics collected:

-   CPU
-   RAM
-   disk usage
-   job queue length
-   worker activity

Grafana dashboards visualize system status.

------------------------------------------------------------------------

# 13. Job Categories

Jobs should be categorized for better scheduling.

Example categories:

    transcode
    ai
    automation
    maintenance
    data_processing

Scheduler routes jobs to appropriate workers.

------------------------------------------------------------------------

# 14. Scheduler Logic

Example decision logic:

    if job small:
        run locally on Pi

    if job medium:
        start oracle-cloud2-vm1

    if job large:
        start oracle-cloud1-vm1

    if cloud unavailable:
        wake Windows PC

------------------------------------------------------------------------

# 15. Verification Checklist

Before production deployment:

-   SSH connectivity to all VMs
-   Redis queue reachable
-   Workers register correctly
-   Jobs execute successfully
-   Idle shutdown works
-   Monitoring dashboards operational

------------------------------------------------------------------------

# 16. Final System Outcome

    ESP32 Sensors
         |
    MQTT Broker
         |
    Raspberry Pi Control Plane
         |
    Redis Job Queue
         |
    Tailscale Mesh Network
         |
    Cloud Compute Workers
         |
    Results returned to ORION dashboard

This architecture provides:

-   distributed compute
-   minimal idle resource usage
-   hybrid edge-cloud automation
-   scalable workloads
