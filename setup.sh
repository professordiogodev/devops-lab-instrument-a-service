#!/usr/bin/env bash
# Builds and starts the service with a Prometheus and a Jaeger next to it. Run: ./setup.sh   (run it again after each change of service/app.py)
set -u
cd "$(dirname "$0")"
for c in docker curl python3; do command -v "$c" >/dev/null || { echo "MISSING: $c"; exit 1; }; done
docker info >/dev/null 2>&1 || { echo "Docker is not running."; exit 1; }
docker compose version >/dev/null 2>&1 || { echo "Docker Compose v2 is missing."; exit 1; }
for port in 8080 9096 16686; do
  if ! docker compose ps -q 2>/dev/null | grep -q . && (exec 3<>"/dev/tcp/127.0.0.1/$port") 2>/dev/null; then echo "Port $port is in use on your machine."; exit 1; fi
done
docker compose up -d --build 2>&1 | tail -3
for _ in $(seq 1 40); do curl -fs http://127.0.0.1:8080/healthz >/dev/null 2>&1 && break; sleep 1; done
cat <<TXT
Service:     http://localhost:8080   (try: curl -s -X POST localhost:8080/points/ana -H 'Content-Type: application/json' -d '{"points": 120}')
Prometheus:  http://localhost:9096   (Status > Targets, then graph your metrics)
Jaeger:      http://localhost:16686  (pick the service "loyalty" once it has sent a span)
Logs:        docker compose logs -f loyalty
TXT
