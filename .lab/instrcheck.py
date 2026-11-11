#!/usr/bin/env python3
import json, os, re, subprocess, sys, time, urllib.parse, urllib.request, urllib.error
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
os.chdir(ROOT)
SVC, PROM, JAEGER = "http://127.0.0.1:8080", "http://127.0.0.1:9096", "http://127.0.0.1:16686"
passed = failed = 0


def check(desc, ok, hint=""):
    global passed, failed
    if ok:
        passed += 1; print("PASS  " + desc, flush=True)
    else:
        failed += 1; print("FAIL  " + desc + (("   -> " + hint) if hint else ""), flush=True)


def sh(*a, timeout=600):
    r = subprocess.run(a, capture_output=True, text=True, timeout=timeout)
    return r.returncode, r.stdout, r.stderr


def call(method, path, body=None, headers=None):
    req = urllib.request.Request(SVC + path, data=json.dumps(body).encode() if body is not None else None, method=method, headers=dict({"Content-Type": "application/json"}, **(headers or {})))
    try:
        r = urllib.request.urlopen(req, timeout=10)
        return r.status, dict(r.headers), r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read().decode()


def wait_for(fn, secs, step=2):
    end = time.time() + secs
    while time.time() < end:
        try:
            r = fn()
            if r:
                return r
        except Exception:
            pass
        time.sleep(step)
    return None


code = "\n".join(l for l in open("service/app.py").read().split("\n") if not l.lstrip().startswith("#"))
print("== Rebuild and start ==")
sh("docker", "compose", "down", "-v", "--remove-orphans")
rc, out, err = sh("docker", "compose", "up", "-d", "--build")
check("the service builds and starts with your code", rc == 0, (out + err)[-300:])
up = wait_for(lambda: call("GET", "/healthz")[0] == 200, 40)
check("GET /healthz answers 200", bool(up), sh("docker", "compose", "logs", "--tail", "15", "loyalty")[1][-400:])
if not up:
    sys.exit(1)
check("no print() calls: logs go through the logging module", "print(" not in code)

print("== Send traffic ==")
SECRET = "Bearer SECRET-TOKEN-XYZ-12345"
s1 = call("POST", "/points/ana", {"points": 120}, {"X-Request-ID": "req-abc-123", "Authorization": SECRET})
call("POST", "/points/ana", {"points": 50})
call("POST", "/points/bruno", {"points": 10})
call("GET", "/points/ana")
call("GET", "/points/bruno")
s404 = call("GET", "/points/ghost")
s422 = call("POST", "/points/ana", {"points": -5})
for _ in range(3):
    call("GET", "/healthz")
check("the service still behaves: 200 with the 10% bonus (132), 404 and 422 as before", s1[0] == 200 and json.loads(s1[2]).get("total") == 132 and s404[0] == 404 and s422[0] == 422)

print("== Metrics ==")
st, hd, body = call("GET", "/metrics")
check("GET /metrics answers in the Prometheus text format", st == 200 and "# TYPE" in body, "expose generate_latest() at /metrics")


def series(name):
    return {m.group(1): float(m.group(2)) for m in re.finditer(r"^%s(\{[^}]*\})?\s+([0-9.eE+-]+)$" % re.escape(name), body, re.M) for m in [re.match(r"(.*)\s+(\S+)$", m.group(0))]}


req = {}
for m in re.finditer(r'^loyalty_http_requests_total\{(.*)\}\s+([0-9.eE+-]+)$', body, re.M):
    labels = dict(re.findall(r'(\w+)="([^"]*)"', m.group(1)))
    req[(labels.get("method"), labels.get("route"), labels.get("status"))] = float(m.group(2))
check("loyalty_http_requests_total{method,route,status} counts the requests: POST 200 x3, GET 200 x2, GET 404 x1, POST 422 x1",
      req.get(("POST", "/points/{customer}", "200")) == 3 and req.get(("GET", "/points/{customer}", "200")) == 2 and req.get(("GET", "/points/{customer}", "404")) == 1 and req.get(("POST", "/points/{customer}", "422")) == 1, str(req)[:200])
check("the route label is the TEMPLATE: no customer name and no /metrics in any label", not any(("ana" in (r or "") or "bruno" in (r or "") or "ghost" in (r or "") or r == "/metrics") for _, r, _ in req) and bool(req))
check("health checks are counted too (3 x GET /healthz 200 or more)", sum(v for (m, r, s), v in req.items() if r == "/healthz") >= 3)
buckets = re.findall(r'^loyalty_http_request_duration_seconds_bucket\{.*route="/points/\{customer\}".*le="([^"]+)".*\}\s', body, re.M) or re.findall(r'^loyalty_http_request_duration_seconds_bucket\{.*le="([^"]+)".*route="/points/\{customer\}".*\}\s', body, re.M)
check("a latency histogram with at least 6 buckets per route (found %d for /points/{customer})" % len(set(buckets)), len(set(buckets)) >= 6 and "+Inf" in buckets, "loyalty_http_request_duration_seconds{method,route}")
cnt = sum(float(x) for x in re.findall(r'^loyalty_http_request_duration_seconds_count\{.*\}\s+([0-9.eE+-]+)$', body, re.M))
check("the histogram counted every request (_count = %d, counter total = %d)" % (cnt, sum(req.values())), cnt == sum(req.values()) and cnt > 0)
awarded = re.search(r"^loyalty_points_awarded_total\s+([0-9.eE+-]+)$", body, re.M)
check("loyalty_points_awarded_total = 192 (120 + 12 bonus + 50 + 10)", bool(awarded) and float(awarded.group(1)) == 192, awarded.group(0) if awarded else "metric missing")
check("loyalty_http_requests_in_flight is a gauge", re.search(r"^# TYPE loyalty_http_requests_in_flight gauge", body, re.M) is not None)
r = wait_for(lambda: json.load(urllib.request.urlopen(PROM + "/api/v1/query?query=" + urllib.parse.quote("loyalty_points_awarded_total"), timeout=5))["data"]["result"], 40, 3)
check("Prometheus scrapes the service (loyalty_points_awarded_total is queryable)", bool(r) and float(r[0]["value"][1]) == 192)

print("== Logs ==")
rc, out, err = sh("docker", "compose", "logs", "--no-log-prefix", "loyalty")
lines = [l for l in out.split("\n") if l.strip().startswith("{")]
objs = []
for l in lines:
    try:
        objs.append(json.loads(l))
    except Exception:
        pass
non_json = [l for l in out.split("\n") if l.strip() and not l.strip().startswith("{") and "INFO:" not in l and "Started" not in l and "Uvicorn" not in l and "Waiting" not in l and "complete" not in l and "Application" not in l]
check("every application log line is JSON (%d JSON lines, %d other lines)" % (len(objs), len(non_json)), len(objs) >= 5 and len(non_json) <= 3, "\n".join(non_json[:3]))
acc = [o for o in objs if o.get("request_id") == "req-abc-123" and o.get("method")]
a = acc[0] if acc else {}
check("the access line has ts, level, service=loyalty, msg, request_id, method, route, status, duration_ms", bool(a) and all(k in a for k in ("ts", "level", "service", "msg", "request_id", "method", "route", "status", "duration_ms")) and a.get("service") == "loyalty", str(a)[:160])
check("the access line uses the route template and a numeric duration", a.get("route") == "/points/{customer}" and a.get("status") == 200 and isinstance(a.get("duration_ms"), (int, float)))
check("the request id sent by the client is used and returned in the X-Request-ID header", s1[1].get("X-Request-ID") == "req-abc-123" or s1[1].get("x-request-id") == "req-abc-123")
ids = {o.get("request_id") for o in objs if o.get("method")}
check("every other request got its own new request id (%d different)" % len(ids), len(ids) >= 8)
pa = [o for o in objs if o.get("msg") == "points added"]
check("a 'points added' business line per purchase, with the customer and without the total", len(pa) == 3 and all(o.get("customer") for o in pa) and not any("total" in o or "points" in o for o in pa))
check("the Authorization header and its secret appear nowhere in the logs", "SECRET-TOKEN-XYZ" not in out)
post = [o for o in objs if o.get("method") == "POST" and o.get("status") == 200]
check("with tracing on, access lines carry a 32-character trace_id", bool(post) and all(re.fullmatch(r"[0-9a-f]{32}", o.get("trace_id", "")) for o in post), str(post[:1]))

print("== Traces ==")
tr = wait_for(lambda: json.load(urllib.request.urlopen(JAEGER + "/api/traces?service=loyalty&limit=50", timeout=5))["data"], 60, 4)
check("Jaeger has traces for the service `loyalty`", bool(tr))
names = [sp["operationName"] for t in (tr or []) for sp in t["spans"]]
check("there is a custom span named compute_bonus, with the attribute points", "compute_bonus" in names and any(sp["operationName"] == "compute_bonus" and any(t_["key"] == "points" for t_ in sp["tags"]) for t in (tr or []) for sp in t["spans"]))
check("health checks and /metrics make no spans", not any(("healthz" in n or "readyz" in n or "metrics" in n) for n in names))
tid = (post[0].get("trace_id") if post else "")
found = False
if tid:
    try:
        d = json.load(urllib.request.urlopen(JAEGER + "/api/traces/" + tid, timeout=5))["data"]
        found = bool(d) and any(sp["operationName"] == "compute_bonus" for sp in d[0]["spans"])
    except Exception:
        found = False
check("the trace_id printed in a log line opens a trace in Jaeger that contains compute_bonus (logs and traces are joined)", found)
o = open("OBSERVABILITY.md").read()
check("OBSERVABILITY.md is filled in (no TODO left)", "TODO" not in o and len(o.split()) > 100)
print()
print(("ALL CHECKS PASSED (%d/%d)" % (passed, passed)) if failed == 0 else ("%d check(s) failed, %d passed" % (failed, passed)))
sys.exit(1 if failed else 0)
