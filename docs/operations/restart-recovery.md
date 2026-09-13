# Restart Recovery

## Objective

The platform should recover from container and EC2 restarts without manual service launches.

## Permanent Restart Policy

Application services use Docker's `unless-stopped` restart policy.

Runtime API deployment:

    deployment/runtime-api/docker-compose.yml

Key settings:

    image: enterprise-runtime-api:3.19
    restart: unless-stopped

Streamlit deployment:

    deployment/frontend/docker-compose.yml

uses:

    restart: unless-stopped

## Runtime API Recovery

    curl -fsS http://127.0.0.1:8001/health

Expected response contains:

    "status": "healthy"
    "service": "runtime-api"

## Streamlit Recovery

    curl -fsS http://127.0.0.1:8501/_stcore/health

Expected:

    ok

## Controlled Restart Validation

Stage 11 validated both application services.

Runtime API:

    docker restart enterprise-runtime-api
    sleep 5
    curl -fsS http://127.0.0.1:8001/health

Streamlit:

    docker restart enterprise-streamlit
    sleep 8
    curl -fsS http://127.0.0.1:8501/_stcore/health

Result:

    Runtime API -> PASS
    Streamlit   -> PASS

Restart policies:

    enterprise-runtime-api -> unless-stopped
    enterprise-streamlit   -> unless-stopped

## Recreating Runtime API

Use the repository deployment definition:

    docker compose \
      -f deployment/runtime-api/docker-compose.yml \
      up -d

## Image Version Synchronization

Whenever a new Runtime API image is built, update the deployment image reference before deployment.

Example:

    New image:
    enterprise-runtime-api:3.20

    Deployment:
    image: enterprise-runtime-api:3.20

The Runtime API image tag and deployment image reference must remain synchronized.

## EC2 Stop/Start Recovery

After EC2 restart:

    docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'

Validate Runtime API:

    curl -fsS http://127.0.0.1:8001/health

Validate Streamlit:

    curl -fsS http://127.0.0.1:8501/_stcore/health

Validate Prometheus:

    curl -fsS http://127.0.0.1:9090/-/healthy

## Cost-Control Operation

The `unless-stopped` policy does not force the EC2 instance to remain running.

Intentional shutdown remains possible:

    docker stop enterprise-runtime-api enterprise-streamlit

During longer periods without development activity, stop platform workloads to avoid unnecessary GPU and runtime usage.

Persistent AWS resources such as EBS volumes and snapshots are separate from Docker container lifecycle.

## Stage 11 Result

    Runtime API restart          -> PASS
    Runtime API health           -> PASS
    Streamlit restart            -> PASS
    Streamlit health             -> PASS
    Permanent Runtime API config -> PASS
    Restart policy               -> unless-stopped

## Architecture Lesson

Reliable container operations require:

1. Correct runtime configuration.
2. A reproducible deployment definition.

A one-time `docker update` fixes an existing container. A version-controlled deployment definition ensures future Runtime API containers are created with the same recovery behavior.
