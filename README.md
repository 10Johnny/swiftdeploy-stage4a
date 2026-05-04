# SwiftDeploy

SwiftDeploy is a declarative deployment CLI tool built for the HNG DevOps Stage 4A task.

The project uses `manifest.yaml` as the single source of truth. The `swiftdeploy` CLI reads the manifest, generates `nginx.conf` and `docker-compose.yml` from templates, deploys the stack with Docker Compose, and supports stable/canary deployment modes.

## Architecture

```text
User / Browser / curl
        |
        v
Nginx container on port 8080
        |
        v
Python API service container on internal port 3000
```

Only Nginx is exposed to the host. The Python API service is not exposed directly. All traffic must pass through Nginx.

## Project Structure

```text
.
├── manifest.yaml
├── swiftdeploy
├── Dockerfile
├── README.md
├── app/
│   ├── main.py
│   └── requirements.txt
└── templates/
    ├── nginx.conf.j2
    └── docker-compose.yml.j2
```

Generated files:

```text
nginx.conf
docker-compose.yml
```

These generated files can be deleted and recreated by running:

```powershell
python swiftdeploy init
```

## Requirements

- Docker Desktop
- Docker Compose v2
- Python 3
- PyYAML
- Jinja2

Install required Python packages:

```powershell
pip install pyyaml jinja2
```

## Manifest

The deployment is controlled from `manifest.yaml`.

```yaml
services:
  image: swift-deploy-1-node:latest
  port: 3000
  mode: stable
  version: "1.0.0"
  restart_policy: unless-stopped

nginx:
  image: nginx:latest
  port: 8080
  proxy_timeout: 30

network:
  name: swiftdeploy-net
  driver_type: bridge
```

## Build the Docker Image

```powershell
docker build -t swift-deploy-1-node:latest .
```

## CLI Commands

### Init

Generates `nginx.conf` and `docker-compose.yml` from the templates and `manifest.yaml`.

```powershell
python swiftdeploy init
```

### Validate

Runs five pre-flight checks:

1. `manifest.yaml` exists and is valid YAML
2. Required fields are present and non-empty
3. Docker image exists locally
4. Nginx port is not already bound on the host
5. Generated `nginx.conf` syntax is valid

```powershell
python swiftdeploy validate
```

### Deploy

Runs init, starts the Docker Compose stack, and waits until the health check passes.

```powershell
python swiftdeploy deploy
```

### Promote to Canary

Switches the deployment mode to canary.

This command:

- updates `manifest.yaml`
- regenerates `docker-compose.yml`
- restarts only the service container
- confirms the mode through `/healthz`

```powershell
python swiftdeploy promote canary
```

### Promote to Stable

Switches the deployment mode back to stable.

```powershell
python swiftdeploy promote stable
```

### Teardown

Stops containers and removes networks and volumes.

```powershell
python swiftdeploy teardown
```

### Teardown With Clean

Stops containers, removes networks and volumes, and deletes generated files.

```powershell
python swiftdeploy teardown --clean
```

## API Endpoints

### Root Endpoint

```powershell
curl.exe http://localhost:8080/
```

Returns:

- welcome message
- current mode
- app version
- server timestamp

### Health Check

```powershell
curl.exe http://localhost:8080/healthz
```

Returns:

- status
- current mode
- process uptime in seconds

### Chaos Endpoint

The chaos endpoint works in canary mode.

Slow mode:

```powershell
curl.exe -X POST http://localhost:8080/chaos -H "Content-Type: application/json" -d "{\"mode\":\"slow\",\"duration\":3}"
```

Error mode:

```powershell
curl.exe -X POST http://localhost:8080/chaos -H "Content-Type: application/json" -d "{\"mode\":\"error\",\"rate\":0.5}"
```

Recover:

```powershell
curl.exe -X POST http://localhost:8080/chaos -H "Content-Type: application/json" -d "{\"mode\":\"recover\"}"
```

## Testing

After deployment:

```powershell
curl.exe http://localhost:8080/
curl.exe http://localhost:8080/healthz
curl.exe -I http://localhost:8080/
```

In stable mode, the response header should include:

```text
X-Deployed-By: swiftdeploy
```

In canary mode, the response headers should include:

```text
X-Mode: canary
X-Deployed-By: swiftdeploy
```

## Nginx Configuration

Nginx:

- listens on port `8080`
- proxies traffic to the internal service container
- adds `X-Deployed-By: swiftdeploy`
- forwards `X-Mode` from the upstream service
- returns JSON error bodies for 502, 503, and 504
- writes access logs in the required format

Required access log format:

```text
$time_iso8601 | $status | ${request_time}s | $upstream_addr | $request
```

View Nginx logs:

```powershell
docker compose -p swiftdeploy logs nginx
```

## Docker and Security Best Practices

This project includes:

- non-root service container
- dropped Linux capabilities
- `no-new-privileges` security option
- service port not exposed directly to the host
- only Nginx exposed on the host
- health check on `/healthz`
- named volume for logs
- lightweight Python Alpine image

## Screenshots Required for Submission

The Google Drive folder should include screenshots of:

1. validate output
2. deploy output
3. promote canary + `/healthz` confirmation
4. generated `nginx.conf`
5. generated `docker-compose.yml`
6. Nginx access logs output

## Final Submission

Submit:

```text
Public GitHub repository link
Google Drive screenshots folder link
```

Required repository contents:

```text
manifest.yaml
swiftdeploy
Dockerfile
README.md
app/
templates/
```

## Troubleshooting

### Port 8080 is already in use

This can happen when the stack is already running.

Fix:

```powershell
python swiftdeploy teardown
python swiftdeploy validate
```

### Docker image not found

Build the image first:

```powershell
docker build -t swift-deploy-1-node:latest .
```

### Health check fails

Check service logs:

```powershell
docker compose -p swiftdeploy logs service
```

### Nginx logs

```powershell
docker compose -p swiftdeploy logs nginx
```
