#!/usr/bin/env bash
rc=0
grep -q 'TODO' OBSERVABILITY.md && { echo "- ❌ OBSERVABILITY.md still has TODO"; rc=1; } || echo "- ✅ OBSERVABILITY.md is filled in"
grep -q 'prometheus_client' service/app.py && grep -q 'opentelemetry' service/app.py && echo "- ✅ app.py uses prometheus_client and opentelemetry" || { echo "- ❌ app.py is not instrumented yet"; rc=1; }
grep -qE '^ALL CHECKS PASSED \(' SUBMISSION.md && echo "- ✅ SUBMISSION.md shows ALL CHECKS PASSED" || { echo "- ❌ paste the verify.sh output ('ALL CHECKS PASSED') into SUBMISSION.md"; rc=1; }
exit $rc
