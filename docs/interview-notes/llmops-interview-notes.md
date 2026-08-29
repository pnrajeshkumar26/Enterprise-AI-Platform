# LLMOps Interview Notes

## 1. What is LLMOps?

**Answer:** LLMOps is the engineering discipline around operating Large Language Model systems across deployment, inference, monitoring, evaluation, reliability, security and lifecycle management.

In this project I demonstrate those concepts through model routing, containerized inference, GPU telemetry, Prometheus/Grafana observability, alerting, quality guardrails, CI and restart recovery.

## 2. Why put a Runtime API in front of vLLM?

It creates a stable application-facing abstraction. Clients do not need to know which inference backend is running. The Runtime API can handle routing, validation, metrics and backend selection while vLLM remains an inference-serving component.

## 3. Why use two models?

Not every request needs the same model capability. A smaller model can handle simpler workloads, while a stronger model can handle more technical or complex tasks. This is a basis for capability/cost-aware routing.

## 4. Why deterministic routing?

It makes the behavior reproducible, explainable and easy to unit test. Once telemetry is reliable, routing can evolve toward resource-, latency- or cost-aware policies.

## 5. Why Prometheus?

Prometheus provides time-series metrics collection and a query model that works well for service health, request rates, latency, failures and resource telemetry.

## 6. Why DCGM?

LLM inference is GPU-intensive. DCGM gives GPU-level visibility such as utilization and framebuffer memory so application behavior can be correlated with the underlying accelerator state.

## 7. Why Grafana?

Grafana turns time-series metrics into operational dashboards and alert rules that engineers can use for diagnosis and monitoring.

## 8. What is the difference between service health and model quality?

A service can return HTTP 200 while the generated answer is wrong. This project encountered that exact class of problem, which led to a quality guardrail in addition to infrastructure observability.

## 9. How did you troubleshoot the model-quality problem?

I isolated the stack layer by layer. The Runtime API and routing behavior were correct, so I bypassed them and called vLLM directly. The same issue reproduced there, proving the defect was in generation behavior rather than the routing/HTTP integration.

## 10. Why not just replace incorrect phrases in the output?

Blind post-processing can corrupt text and does not generalize. The project therefore uses a bounded validation check and one corrective regeneration instead.

## 11. How does Streamlit recover after EC2 restart?

Streamlit is now containerized with Docker and `restart: unless-stopped`. The container has a health check and reaches the Runtime API using Docker service DNS. After EC2 restart, Docker restores the service without a manual `streamlit run` command.

## 12. What happens after EC2 restart?

Docker restarts the configured services, the inference backends reload, Prometheus and Grafana become available, DCGM resumes GPU telemetry, and Streamlit starts automatically.

## 13. Why use Docker service names instead of container IPs?

Container IP addresses are ephemeral. Service names are stable within the Docker network and are therefore the correct service-discovery mechanism.

## 14. Why restrict Prometheus/DCGM to localhost?

The metrics endpoints are operational interfaces and do not need to be publicly exposed in this development setup. Binding them to localhost reduces host exposure while preserving internal container communication.

## 15. What would you add for production?

Authentication/authorization, TLS, secrets management, ingress/API gateway, network policy, image/dependency scanning, centralized logging, tracing, formal evaluation, SLOs, autoscaling, capacity planning and infrastructure-as-code.

## 16. What is your one-minute project explanation?

> I built a practical LLMOps platform around a FastAPI Runtime API that routes requests between TinyLlama through llama.cpp and Phi-3 through vLLM. I containerized the services, added Prometheus metrics and NVIDIA DCGM GPU telemetry, built Grafana dashboards and alerts, and containerized Streamlit so the frontend automatically recovers after an EC2 restart. During observability validation I discovered that infrastructure health did not guarantee model quality, so I added verified platform context and a bounded deterministic response guard. The platform is tested with an automated pytest suite and documented as a learning-oriented reference architecture rather than a claim of production readiness.

## 17. Questions I should expect from recruiters

### What is your role in the project?

Explain which parts you personally designed, implemented, tested and troubleshot. Keep the answer concrete and avoid claiming tools or production environments that were not actually validated.

### Why is this an LLMOps project instead of an API project?

Because it covers operational concerns around inference: model routing, multiple serving backends, GPU telemetry, metrics, dashboards, alerting, restart recovery, quality controls and CI.

### What was the hardest problem?

A strong example is isolating the difference between infrastructure health and model-quality failure, then proving where the issue existed by bypassing application layers and testing vLLM directly.

## 18. Recruiter-friendly keywords

`LLMOps`, `MLOps`, `GenAI`, `LLM inference`, `vLLM`, `llama.cpp`, `FastAPI`, `Docker`, `Docker Compose`, `NVIDIA GPU`, `Tesla T4`, `Prometheus`, `Grafana`, `DCGM`, `observability`, `model routing`, `quality guardrails`, `CI/CD`, `GitHub Actions`, `Python`, `Kubernetes`.
