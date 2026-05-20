# SPDX-License-Identifier: AGPL-3.0
# Copyright (C) 2026 Juan Pablo Chancay
"""
S4 — Kubernetes deployment — missing observability and resource controls

Fault: K8s manifest without resource limits, liveness/readiness probes,
and Prometheus annotations. Impacts v5 (observability_coverage) and
v2 (architectural_alignment) as scored by the LLM.

Static analysis on YAML is limited — this scenario primarily tests the LLM's
ability to recognize operational best practice violations in deployment configs.

Ground truth:
  s4_deploy_clean:  v5_approx=0.85 (full observability), v2_approx=0.80
  s4_deploy_faulty: v5_approx=0.15 (no observability), v2_approx=0.35
"""
from __future__ import annotations

SCENARIO_ID = "S4"
DESCRIPTION = "K8s deployment — missing resource limits, probes, and observability"
FAULT_TYPE = "missing_observability"
N_CYCLES = 1

GROUND_TRUTH: dict[str, dict] = {
    "s4_deploy_clean": {
        "v5_observability_approx": 0.85,
        "v2_arch_approx": 0.80,
        "fault_present": False,
    },
    "s4_deploy_faulty": {
        "v5_observability_approx": 0.15,
        "v2_arch_approx": 0.35,
        "fault_present": True,
        "fault_description": (
            "No resource limits/requests; no liveness/readiness probes; "
            "no Prometheus annotations; no HPA configuration"
        ),
    },
}

_CLEAN_DEPLOY = """\
# k8s_deployment.yaml — clean version with full observability
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-service
  namespace: production
  labels:
    app: api-service
    version: "2.1.0"
  annotations:
    prometheus.io/scrape: "true"
    prometheus.io/port: "8080"
    prometheus.io/path: "/metrics"
spec:
  replicas: 3
  selector:
    matchLabels:
      app: api-service
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  template:
    metadata:
      labels:
        app: api-service
        version: "2.1.0"
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8080"
    spec:
      containers:
        - name: api-service
          image: registry.example.com/api-service:2.1.0
          ports:
            - containerPort: 8080
              name: http
          resources:
            requests:
              cpu: "250m"
              memory: "256Mi"
            limits:
              cpu: "500m"
              memory: "512Mi"
          livenessProbe:
            httpGet:
              path: /healthz
              port: 8080
            initialDelaySeconds: 15
            periodSeconds: 20
            failureThreshold: 3
          readinessProbe:
            httpGet:
              path: /ready
              port: 8080
            initialDelaySeconds: 5
            periodSeconds: 10
            failureThreshold: 3
          env:
            - name: LOG_LEVEL
              value: "INFO"
            - name: METRICS_ENABLED
              value: "true"
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api-service-hpa
  namespace: production
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api-service
  minReplicas: 2
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
"""

_FAULTY_DEPLOY = """\
# k8s_deployment.yaml — FAULT: no resource limits, no probes, no observability
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-service
  namespace: production
  labels:
    app: api-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: api-service
  template:
    metadata:
      labels:
        app: api-service
    spec:
      containers:
        - name: api-service
          image: registry.example.com/api-service:2.1.0
          ports:
            - containerPort: 8080
          # FAULT: no resources block — pod can consume unlimited CPU/memory
          # FAULT: no livenessProbe — unhealthy pods are never restarted
          # FAULT: no readinessProbe — traffic routes to unready pods
          # FAULT: no Prometheus annotations — metrics not scraped
          # FAULT: no HPA — no autoscaling under load
          env:
            - name: LOG_LEVEL
              value: "ERROR"
"""


def get_artifacts(cycle_k: int = 0) -> list[dict]:
    base_context = "Kubernetes deployment manifest. Stage: deploy. Scenario: S4."
    return [
        {
            "id": "s4_deploy_clean",
            "agent_id": "deploy_agent",
            "stage": "deploy",
            "content": _CLEAN_DEPLOY,
            "artifact_type": "ci_cd_config",
            "context": base_context + " Full observability and resource controls present.",
        },
        {
            "id": "s4_deploy_faulty",
            "agent_id": "deploy_agent",
            "stage": "deploy",
            "content": _FAULTY_DEPLOY,
            "artifact_type": "ci_cd_config",
            "context": base_context + " Missing probes, resource limits, and Prometheus annotations.",
        },
    ]
