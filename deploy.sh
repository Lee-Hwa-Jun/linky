#!/usr/bin/env bash
set -euo pipefail

COMPOSE_CMD=${COMPOSE_CMD:-"docker compose"}
SERVICES=(web_blue web_green)

info() { printf "[deploy] %s\n" "$*"; }

wait_for_service() {
  local service=$1
  local deadline=$((SECONDS + 90))

  info "Waiting for ${service} to become ready..."
  while true; do
    if ${COMPOSE_CMD} exec -T "${service}" sh -c '
      if command -v curl >/dev/null 2>&1; then
        curl -fsS --max-time 5 http://localhost:8000/healthz \
          || curl -fsS --max-time 5 http://localhost:8000/ \
          || exit 1
      else
        python - <<"PY"
import socket, sys
try:
    with socket.create_connection(("localhost", 8000), timeout=3) as sock:
        sock.sendall(b"HEAD / HTTP/1.0\r\nHost: localhost\r\n\r\n")
        data = sock.recv(15)
        if b"HTTP/1." not in data:
            sys.exit(1)
except Exception:
    sys.exit(1)
PY
      fi
    '; then
      info "${service} is responding"
      break
    fi

    if (( SECONDS >= deadline )); then
      echo "${service} failed to respond in time" >&2
      exit 1
    fi
    sleep 3
  done
}

info "Building shared image for blue/green services..."
${COMPOSE_CMD} build web_blue web_green

for service in "${SERVICES[@]}"; do
  info "Deploying ${service}"
  ${COMPOSE_CMD} up -d --no-deps "${service}"
  wait_for_service "${service}"
  info "${service} is ready"
  info "---"

done

if ${COMPOSE_CMD} ps --status running nginx >/dev/null 2>&1; then
  info "Reloading nginx to pick up upstream health"
  ${COMPOSE_CMD} exec -T nginx nginx -s reload || true
else
  info "Starting nginx"
  ${COMPOSE_CMD} up -d nginx
fi

info "Deployment complete. Both web instances should now be serving traffic."
