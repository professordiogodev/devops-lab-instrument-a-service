#!/usr/bin/env bash
# Removes the containers, network, volumes and image. Run with: ./teardown.sh
cd "$(dirname "$0")" || exit 1
docker compose down -v --remove-orphans 2>&1 | tail -3
docker image rm loyalty-lab:1 >/dev/null 2>&1 && echo "removed the image"
echo "Now run ./verify-teardown.sh"
