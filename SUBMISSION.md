# Submission

Fork URL: <!-- paste the URL of your fork here -->

## Files to commit

- [ ] `service/app.py`: the instrumented service
- [ ] `OBSERVABILITY.md`: what each signal is for

## Questions

Answer in your own words. Where a question asks for output, paste it in a code block.

### Q1. Paste your request-counting middleware. Why must the metric label be the route TEMPLATE (`/points/{customer}`) and not the real path (`/points/ana`)? What happens to Prometheus if you use the path, and which kind of label problem is this?

**Your answer:**

<!-- replace this line with your answer -->

### Q2. Paste one JSON access log line of your service. Which fields did you add beyond the message, and why does every line need a `request_id` and, when tracing is on, a `trace_id`? How does a support engineer use them?

**Your answer:**

<!-- replace this line with your answer -->

### Q3. Explain your histogram: which buckets did you choose and why? What is the difference between a histogram and a summary, and why can histograms of several instances be added together but percentiles cannot?

**Your answer:**

<!-- replace this line with your answer -->

### Q4. Show the custom span `compute_bonus` in Jaeger (describe it: parent, duration). What is the difference between a trace, a span and the context that links them across services, and which HTTP header carries it?

**Your answer:**

<!-- replace this line with your answer -->

### Q5. What do `/healthz` and `/readyz` each answer, and who uses each (the kubelet, a load balancer)? What should `/readyz` check in this service?

**Your answer:**

<!-- replace this line with your answer -->

### Q6. Name one thing you chose NOT to log or measure, and why (hint: personal data, a label with unbounded values, a header with a token).

**Your answer:**

<!-- replace this line with your answer -->

### Q7. Paste the output of `./verify.sh`. It must end with **ALL CHECKS PASSED**.

**Your answer:**

<!-- replace this line with your answer -->

### Q8. **Tear down.** Paste the output of `./verify-teardown.sh`. It must end with **TEARDOWN VERIFIED**.

**Your answer:**

<!-- replace this line with your answer -->
