# Hoja de Ruta Experimental v2 — CAL Research Program

**Versión:** 2.0 — post-auditoría 2026-06-02  
**Versión anterior:** roadmap de 10 semanas en README.md v1

---

## Cambios respecto a v1

| Cambio | Razón |
|---|---|
| 10 semanas → 12 semanas | DT-030/031/032 identificados en auditoría como críticos previos al piloto |
| H3 → H_OBS como primaria | Reencuadre a observabilidad causal; CCI como moderador |
| Paper 1 (SID) + Paper 2 (RCT) | Programa dual con benchmark compartido y H_cross pre-registrada |
| DT-032 antes del RCT | Restricción de secuencia: SID_C*(S1–S5) debe pre-registrarse antes de recolectar datos del RCT |
| Venue: FAccT (Paper 1) + CHI 2027 (Paper 2) | Reencuadre causal es más afín a FAccT que a venues de ML |

---

## Restricciones de secuencia no negociables

```
1. DT-036 (frontend React) → completo antes del piloto
2. DT-030 (análisis estadístico) → scripts existentes y probados antes del experimento
3. DT-032 (SID S1-S5) → ejecutado y pre-registrado ANTES de semana 10
4. Piloto n=4 → después de plataforma completa (DT-028 Fase 1+2+3)
5. Calibración φ (Spearman ρ ≥ 0.75) → gate previo al experimento
6. Experimento n=40 → solo después de pasar calibración Y pre-registro H_cross
```

---

## Timeline de 12 semanas

### Semanas 1–4 — Build (Completado)

| Sem | Deliverable | Estado |
|---|---|---|
| 1–2 | Core engine: φ, f, I — todos los módulos | ✅ |
| 3 | Pipeline S1–S5 + corpus.json (12 artefactos) + φ calibration suite + DT-024 evaluator reliability | ✅ |
| 4 | NCF proxies + PIQ rubric + warm-up S0 + ControlGroupViewer | ✅ |

---

### Semana 5 — DT-028 Backend (Completado)

| Deliverable | Estado |
|---|---|
| DB models `cal_*` layer-aware + database.py | ✅ |
| Auth JWT + bcrypt (core/auth.py) | ✅ |
| Randomización estratificada (core/randomization.py) | ✅ |
| Rutas `/cal/api`: register, login, consent, me, admin | ✅ |
| Wire vector/tensor/inference al core | ✅ |
| Email service (bienvenida + invitación) | ✅ |
| Bootstrap admin CLI (scripts/create_admin.py) | ✅ |
| Fase 2 backend: endpoints sesión + scenario + NCF compute | ✅ |

---

### Semana 6 — DT-036: Frontend React + DT-031: Tests

**Objetivo:** plataforma completa de extremo a extremo (web frontend funcional) + red de seguridad de regresión para el core.

#### DT-036 — Frontend React (TaskSequencer y runner)

| Componente | Archivo | Descripción |
|---|---|---|
| Shell + routing | `App.tsx` | Rutas /cal, /cal/login, /cal/register, /cal/dashboard, /cal/session/run, /cal/results, /cal/admin |
| Auth guards | `App.tsx` | Redirect si no hay token; role check participant vs admin |
| Clientes API | `tcoClient.ts` + `experimentClient.ts` | Wrappers fetch sobre /cal/api y /vector, /inference |
| Task Sequencer | `TaskSequencer.tsx` | Orquesta: pre-test (10m) → S0 (15m) → T1 → T2 → TLX#1 → **PAUSA** → T3 → T4 → TLX#2 |
| NASA-TLX form | `NASATLXForm.tsx` | 6 subscales 0–100, submit a `/session/{id}/tlx` |
| Interaction tracker | `InteractionTracker.ts` | Timestamps de eventos → `/session/{id}/task` payload |
| Dashboard experimental | `VectorRadar.tsx`, `TensorHeatmap.tsx`, `InferencePanel.tsx`, `PolicyInjection.tsx` | Wire al backend via tcoClient |
| Admin dashboard | `AdminDashboard.tsx` (nuevo) | Listado participantes, grupos, completitud, invitación, resultados |
| Debriefing results | `ResultsView.tsx` (nuevo) | Accuracy por tarea, faults reales, TLX scores — post-sesión |

**Timer policy (Fase 4 del pilot_protocol.md):**

```
Pre-test:       10 min → auto-close
Warm-up S0:     15 min → no timer pressure
T1:             25 min → auto-close, partial capture
T2:             20 min → auto-close
NASA-TLX #1:     5 min → auto-close
PAUSA ACTIVA:   10 min → countdown visible
T3:             15 min → auto-close
T4:             30 min → auto-close
NASA-TLX #2:     5 min → auto-close
```

#### DT-031 — Core test suite

| Test file | Cobertura mínima |
|---|---|
| `test_aggregator.py` | Shape de T, NaN handling, slicing nombrado, cycle indexing |
| `test_inference_engine.py` | omega stable/warning/critical, Δ slope threshold, Ρ conflict Δ>0.30, S3 detectado en 4 ciclos, S5 Ρ entre j1/j2 |
| `test_vectorizer.py` | clip [0,1], cache hit/miss, consensus v10, anomaly v11=0 sin baseline |
| `test_qa_evaluator.py` | Mock LLM → parsing correcto, fallback regex, max_tokens=2048 |

---

### Semana 7 — DT-030: Análisis estadístico + DT-032: SID S1–S5 + Pre-registro

**Esta semana es el gate crítico del programa.** Nada del experimento puede correr hasta que DT-032 produzca SID_C*(S1..S5) y sea pre-registrado.

#### DT-030 — Scripts de análisis estadístico

| Script | Hipótesis | Contenido |
|---|---|---|
| `h1_cognitive_load.py` | H1 | Mann-Whitney U sobre TLX; Cohen's d; bootstrap CIs |
| `h2_decision_accuracy.py` | H2 | Precision/Recall; Cohen's d; per-scenario breakdown |
| `h4_early_detection.py` | H4 | Wilcoxon time-to-correct; ARIMA sobre trayectoria S3 |
| `h5_policy_quality.py` | H5 | Spearman ρ PIQ → Δ_vector; regresión lineal; κ inter-rater |
| `h_obs_causal.py` | **H_OBS** | Mixed ANOVA Group × CCI; ΔPIQ(S3,S5) vs ΔPIQ(S1,S4) |
| `ancova_all.py` | Todos | ANCOVA: experience + pre-test + ai_familiarity; partial η² |
| `effect_sizes.py` | Todos | Tabla unificada de effect sizes con CIs 95% |
| `h_cross_correlation.py` | **H_cross** | r_Spearman(SID_C*, ΔPIQ) sobre 5 escenarios; run post-experimento |

**Todos los scripts deben poder ejecutarse con datos sintéticos** (modo `--dry-run` o fixtures) para verificar el pipeline analítico antes del experimento real.

#### DT-032 — SID Study S1–S5 (infraestructura mínima)

| Componente | Archivo | Descripción |
|---|---|---|
| Probe lineal | `analysis/sid_study/probe.py` | LogisticRegression sobre representaciones raw/V/T |
| Probe estructural | `analysis/sid_study/probe.py` | Lectura directa de índices (P_structural) para T |
| MI estimator | `analysis/sid_study/mi_estimator.py` | I(R; Y) para representaciones R con Y=(D,C) desde corpus |
| SID compute | `analysis/sid_study/sid_compute.py` | SID*(R) = I(R;Y)/(C(R)+λH_noise(R)); SID_D* y SID_C* |
| Benchmark runner | `analysis/sid_study/benchmark_s1s5.py` | Corre probes sobre 12 artefactos del corpus.json; produce SID_C*(s) por escenario |

**Output del benchmark runner:**

```json
{
  "SID_C_star": {
    "S1": 0.XX,
    "S2": 0.XX,
    "S3": 0.XX,
    "S4": 0.XX,
    "S5": 0.XX
  },
  "predicted_order": ["S3", "S5", "S2", "S4", "S1"],
  "h_cross_prediction": "ΔPIQ ordering will follow SID_C* ordering"
}
```

Este JSON se pre-registra (OSF o similar) **antes de abrir el dataset del RCT**.

---

### Semana 8 — Piloto n=4

**Protocolo completo:** `protocols/pilot_protocol.md`  
**Participantes:** 4 internos/conocidos, ≥2 años experiencia, sin exposición a TCO  
**Grupos:** 2 control + 2 experimental  
**Datos:** excluidos del análisis final (flag `is_pilot=True` en DB)

**Gates de entrada:**
- [ ] DT-028 plataforma completamente funcional (Fases 1+2+3)
- [ ] DT-036 frontend React funcionando end-to-end
- [ ] DT-031 tests verdes
- [ ] `integrity_checker.py` (DT-013) operativo
- [ ] SID_C*(S1..S5) pre-registrado (DT-032)

**Criterios go/no-go del piloto** (de `pilot_protocol.md` Sección 8):

| Criterio | Umbral |
|---|---|
| Timing total | ≤ 3h30m por sesión |
| Instrumentos de datos | 0 errores de recolección |
| Ambigüedad de instrucciones | ≤ 1 participante con confusión en la misma fase |
| Desacople efectivo | ≥ 3/4 reportan útil o neutral |
| Problemas técnicos críticos | 0 sesiones abortadas |

**Informe post-piloto:** `analysis/pilot_report.py` (DT-029) genera informe con timing, go/no-go checklist, y ajustes recomendados.

---

### Semana 9 — Calibración

**Dos gates en paralelo:**

#### Gate 1: φ calibration — Spearman ρ ≥ 0.75

```bash
PYTHONPATH=src python -m experiment.phi_calibration.phi_calibration \
    --corpus src/experiment/phi_calibration/corpus/corpus.json
```

Si ρ < 0.75 en cualquier dimensión: revisar prompts del QA evaluator y re-correr. No avanzar al experimento.

#### Gate 2: PIQ LLM-Judge — κ ≥ 0.70

Dos anotadores evalúan 20% de las políticas del piloto de forma ciega. Si κ < 0.70: revisar rubrica PIQ (`protocols/piq_rubric.md`) y re-calibrar ejemplos del LLM judge (`piq_evaluation/llm_judge_prompt.py`).

---

### Semanas 10–11 — Experimento n=40

**Reclutamiento** (iniciar en Semana 7, paralelo al desarrollo):

| Canal | Target |
|---|---|
| Online (Reddit, Discord, LinkedIn, Dev.to) | n=20 |
| Local (UBA/UTN, empresas tech BA, meetups) | n=20 |
| Filtro previo | ≥2 años code review + sin TCO exposure + disponibilidad 3h |

**Asignación:** automática al registrarse en `researchlab.aural-syncro.com.ar/cal` — estratificada por experiencia (Junior 2–4 / Mid 5–9 / Senior 10+), balanceada por grupo.

**Covariables registradas al alta:**
- Años de experiencia (code review)
- Nivel educativo
- Familiaridad con herramientas IA (0–4)
- Stack tecnológico principal

**Por sesión (≈ 3h15m con pausa):**

```
Registro + consentimiento:  15 min
Desacople (puzzle espacial): 10 min
Briefing (single-blind):    20 min
Pre-test técnico:            10 min
Warm-up S0:                 15 min
T1 (S1):                    25 min
T2 (S2):                    20 min
NASA-TLX #1:                 5 min
PAUSA ACTIVA:               10 min
T3 (S3):                    15 min → requiere 4 ciclos pre-cargados
T4 (S5):                    30 min
NASA-TLX #2:                 5 min
Debriefing individual:      20 min
─────────────────────────────────────
TOTAL:                    ~3h15m
```

---

### Semana 12 — Análisis + Writing

**Secuencia de análisis:**

```
1. Verificar integridad: n=40 sesiones completas, datos NCF presentes
2. Correr ancova_all.py → ANCOVA residuals, outliers, covariable checks
3. Correr h_obs_causal.py → H_OBS: Group × CCI interaction (resultado principal)
4. Correr h1 → h5 scripts → hipótesis secundarias
5. Correr h_cross_correlation.py → r_Spearman(SID_C*, ΔPIQ) — confirmación H_cross
6. Correr effect_sizes.py → tabla unificada para el paper
7. Generar figuras (Recharts o matplotlib)
```

**Paper 2 (CHI 2027):** draft completo en `Documentacion/TCO_LaTeX/main.tex`. Submission deadline: Septiembre 2026.

**Paper 1 (SID Study / FAccT):** desarrollar en paralelo a partir de Semana 9. Incluye DT-033 (definición formal de observabilidad causal) + DT-034 (corpus S6–S8 para generalización).

---

## Riesgos y mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|
| Reclutamiento n=40 lento (incentivo no monetario) | Alta | Alto | Iniciar reclutamiento en Sem 7; tener lista de espera de 60 candidatos |
| φ gate falla (ρ < 0.75) | Media | Alto | DT-024 ya validó σ < 0.05; revisar prompt, no el pipeline |
| H_OBS no se confirma (mejora uniforme) | Media | Alto | Resultado igualmente publicable: refuta la hipótesis más fuerte, apoya H1/H2 |
| LLM deprecation (OpenRouter) | Baja | Medio | DT-035: pinear versión, archivar outputs; Anthropic direct como fallback |
| S3/S5 detectables con raw por expertos senior | Media | Alto | Estratificar por experiencia en el análisis; Senior n=4 no da potencia para sub-análisis |

---

## Artefactos de entrega por semana

| Sem | Artefacto entregable |
|---|---|
| 6 | Frontend React funcional end-to-end + tests verdes (`pytest` sin "no tests ran") |
| 7 | `analysis/sid_study/benchmark_s1s5.py` con output SID_C*(S1..S5) + pre-registro OSF |
| 7 | Todos los scripts `analysis/h*.py` ejecutables con datos de prueba |
| 8 | 4 sesiones de piloto completadas + `pilot_report_v1.md` con go/no-go |
| 9 | Calibración φ PASS + PIQ κ ≥ 0.70 documentados |
| 11 | Dataset completo n=40 en DB (anonimizado, `anonymizer.py` corrido) |
| 12 | Paper 2 draft completo + H_cross reportado |
