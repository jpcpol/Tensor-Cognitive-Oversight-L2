# TCO — Tensor-Based Cognitive Oversight

## Propósito

Framework de investigación académica para supervisión cognitiva humana de pipelines multi-agente de IA. Propone el modelo NCF (Natural Cognitive Frontier): el operador humano orquesta estados del sistema, no valida artefactos individuales.

**Wiki del ecosistema**: `c:\Users\Usuario\Documents\Aural Syncro\Obsidian\wiki\proyectos\tco.md`

---

## Arquitectura: 6 capas

```
Layer 6 — Human Orchestration (NCF): lee {Ω,Δ,Ρ,Ξ}, inyecta política en lenguaje natural
Layer 5 — Inference I: T → {Ω, Δ, Ρ, Ξ}
Layer 4 — Tensor Aggregation: T[d,i,j,k] ∈ ℝⁿˣˢˣᵃˣᵗ  ← TCO CORE
Layer 3 — Vectorization: φ: A → V ∈ [0,1]¹¹
Layer 2 — QA Evaluation (multi-agente): qa_agent, security, perf, arch
Layer 1 — AI Generation: code_agent, design_agent, deploy_agent, test_agent
```

---

## Componentes y stack

| Componente          | Tecnología                              | Puerto | Estado      |
| ------------------- | --------------------------------------- | ------ | ----------- |
| `tco_engine`        | FastAPI + TimescaleDB + SonarQube + Bandit | 8000  | 0% — stubs  |
| `pipeline`          | LangGraph + Claude API (sonnet-4-6)     | —      | 0% — stubs  |
| `dashboard`         | React 18 + Recharts + TailwindCSS       | 3000   | 0% — stubs  |
| Infraestructura     | Docker Compose (5 servicios)            | —      | Configurado |

---

## Notación matemática clave

| Símbolo             | Definición                                               |
| ------------------- | -------------------------------------------------------- |
| `V ∈ [0,1]¹¹`       | Vector de calidad — 11 dimensiones normalizadas          |
| `T[d,i,j,k]`        | Tensor cognitivo: dimensión × etapa × agente × tiempo    |
| `φ: A → V`          | Función vectorizadora — artefacto a vector               |
| `f: {V} → T`        | Función de agregación — vectores a tensor                |
| `I: T → {Ω,Δ,Ρ,Ξ}` | Motor de inferencia — tensor a outputs de supervisión    |
| **Ω**               | Estado global (stable / warning / critical)              |
| **Δ**               | Tendencia — señal de alerta temprana                     |
| **Ρ**               | Riesgo sistémico — conflictos inter-agente               |
| **Ξ**               | Recomendaciones priorizadas por ∂Ω/∂acción              |

---

## Vector de calidad: 11 dimensiones

| Dim  | Nombre                  | Inversión |
| ---- | ----------------------- | --------- |
| v₁   | functional_correctness  | —         |
| v₂   | architectural_alignment | —         |
| v₃   | scalability_projection  | —         |
| v₄   | security_risk           | ↓ invertida (1 = sin riesgo) |
| v₅   | observability_coverage  | —         |
| v₆   | testability             | —         |
| v₇   | maintainability         | —         |
| v₈   | technical_debt          | ↓ invertida |
| v₉   | performance             | —         |
| v₁₀  | confidence              | —         |
| v₁₁  | anomaly_score           | ↓ invertida |

---

## Diseño experimental

- **Tipo**: Between-subjects RCT, single-blind, n=40 ingenieros de software
- **Grupos**: Control (HITL tradicional: raw outputs + IDE) vs. Experimental (TCO Dashboard + policy injection)
- **Tareas**: T1 detección de errores · T2 evaluación de riesgo · T3 decisión de deploy · T4 re-orquestación
- **Escenarios**: S1 auth (SQL injection) · S2 arch (dep. circular) · S3 debt (cyclomatic, **indetectable con raw**) · S4 deploy (K8s/Prometheus) · S5 conflict (inter-agente, **indetectable con raw**)
- **Métricas**: NASA Raw-TLX (carga cognitiva) + PIQ score (calidad de política inyectada)
- **Venue objetivo**: CHI 2027 (submission sep 2026)

---

## Archivos clave

| Archivo                               | Contenido                             |
| ------------------------------------- | ------------------------------------- |
| `README.md`                           | Paper working paper v3.0 completo     |
| `Documentacion/TCO_Paper_Final_v3.md` | Versión extendida del paper           |
| `src/tco_engine/`                     | FastAPI + vectorizer + aggregator + inference |
| `src/pipeline/`                       | LangGraph graph + agents + scenarios + fault_injector |
| `src/dashboard/`                      | React 18 + componentes + experiment UI |

---

## Estado del proyecto

**Working paper v3.0** — Abril 2026.

| Módulo                          | Estado          |
| ------------------------------- | --------------- |
| `core/vectorizer.py`            | ✅ Implementado  |
| `core/qa_evaluator.py`          | ✅ Implementado  |
| `core/aggregator.py`            | ✅ Implementado  |
| `core/inference_engine.py`      | ✅ Implementado  |
| `static_analysis/radon_runner`  | ✅ Implementado  |
| `static_analysis/bandit_runner` | ✅ Implementado  |
| `db/cache.py`                   | ✅ Implementado  |
| `pipeline/agents/qa_agent.py`   | ✅ Implementado  |
| `Documentacion/TCO_LaTeX/`      | ✅ Draft ACM     |
| `tco_engine API (FastAPI)`      | 🟡 Stubs        |
| `pipeline/graph.py`             | 🟡 Stubs        |
| `dashboard/`                    | 🟡 Stubs        |

Roadmap de 10 semanas: Sem 1–4 Build → Sem 5 Pilot → Sem 6 Calibración → Sem 7–8 Experimento → Sem 9–10 Análisis + Writing.

**Licencia**: CC BY-NC 4.0 (docs) + AGPL-3.0 (src).
