# SwiftDeploy

Declarative deployment CLI. Edit manifest.yaml, run swiftdeploy.

## Quick Start
docker build -t swift-deploy-1-node:latest .
python swiftdeploy deploy

## Commands
python swiftdeploy init
python swiftdeploy validate
python swiftdeploy deploy
python swiftdeploy promote canary
python swiftdeploy promote stable
python swiftdeploy teardown
python swiftdeploy teardown --clean

## Endpoints
GET  http://localhost:8080/
GET  http://localhost:8080/healthz
POST http://localhost:8080/chaos
