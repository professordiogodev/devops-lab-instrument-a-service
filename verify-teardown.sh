#!/usr/bin/env bash
# Proves the lab left nothing on your machine. Run with: ./verify-teardown.sh
cd "$(dirname "$0")" || exit 1
pass=0; failn=0
check() { local d="$1"; shift; if "$@" >/dev/null 2>&1; then echo "PASS  $d"; pass=$((pass+1)); else echo "FAIL  $d"; failn=$((failn+1)); fi; }
check "no container, network or volume of the project instrument-lab" bash -c '[ -z "$(docker ps -aq --filter label=com.docker.compose.project=instrument-lab)$(docker network ls -q --filter label=com.docker.compose.project=instrument-lab)$(docker volume ls -q --filter label=com.docker.compose.project=instrument-lab)" ]'
check "the image loyalty-lab:1 is gone" bash -c '! docker image inspect loyalty-lab:1'
echo
if [ "$failn" -eq 0 ]; then echo "TEARDOWN VERIFIED ($pass/$pass) on this machine"; else echo "NOT CLEAN: $failn leftover(s)."; fi
exit "$failn"
