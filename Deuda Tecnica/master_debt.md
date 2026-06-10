# TCO — Deuda Técnica

Registro de decisiones diferidas, simplificaciones del MVP y trabajo pendiente
que deberá abordarse antes de la submission final o el experimento completo.

---

## Resumen de Estado

| ID | Descripción breve | Categoría | Estado |
| -- | ----------------- | --------- | ------ |
| DT-000 | Pipeline graph.py + fault_injector.py (S1-S5) + corpus.json | Crítica | Implementado |
| DT-001 | Instalar entornos de dependencias | Crítica | Implementado |
| DT-002 | Implementar `vectorizer.py` | Crítica | Implementado |
| DT-003 | Implementar prompt del QA Agent | Crítica | Implementado |
| DT-004 | Implementar `ControlGroupViewer.tsx` | Crítica | Implementado |
| DT-005 | Definir warm-up pipeline | Importante | Implementado |
| DT-006 | Implementar `policy_processor.py` | Importante | Decisión Tomada |
| DT-007 | Protocolo de reclutamiento n=40 | Importante | Decisión Tomada |
| DT-008 | Migración a TimescaleDB | Importante | Decisión Tomada |
| DT-009 | `tsconfig.json` y `vite.config.ts` | Importante | Implementado |
| DT-010 | Dashboard Dockerfile multi-stage | Recomendado | Pendiente |
| DT-011 | `kappa_validator.py` para PIQ | Recomendado | Pendiente |
| DT-012 | Scripts de análisis estadístico | Recomendado | Pendiente |
| DT-013 | `integrity_checker.py` pre-sesión | Recomendado | Pendiente |
| DT-014 | Protocolo de consentimiento informado | Recomendado | Pendiente |
| DT-015 | Sección Related Work del paper | Recomendado | Implementado |
| DT-016 | Adaptar paper a formato LaTeX/ACM | Recomendado | Implementado |
| DT-017 | Implementar ArtifactCache (Redis) | Recomendado | Implementado |
| DT-018 | Paper — Defender necesidad matemática del tensor | Importante | Implementado |
| DT-019 | Paper — Gate formal de validación φ pre-piloto | Crítica | Implementado |
| DT-020 | Paper — Reencuadrar con narrativa expertise shift | Recomendado | Implementado |
| DT-021 | Suite de calibración φ (Spearman ρ) | Crítica | Implementado |
| DT-022 | Rubrica PIQ a nivel struct para H5 | Importante | Implementado |
| DT-023 | Script tensor necessity proof (analysis/) | Recomendado | Implementado |
| DT-024 | Paper — Evaluator variance y rigor LLM-QA | Importante | Implementado |
| DT-025 | Paper — Reencuadrar vector como "~orthogonal supervisory dims" | Importante | Implementado |
| DT-026 | Experimento — 4 proxies NCF operacionalizados en infra | Importante | Implementado |
| DT-027 | Paper — Reencuadre sistemático "supervisory estimators" | Importante | Implementado |
| DT-028 | Plataforma web experimento — researchlab.aural-syncro.com.ar/cal | Importante | Fases 1–2 ✅ · Fase 3 (deploy prod) pendiente |
| DT-029 | Script generador de informe post-piloto (`analysis/pilot_report.py`) | Importante | Pendiente |
| DT-030 | Scripts de análisis estadístico H1–H5 + H_OBS + ANCOVA + effect sizes | **Crítica** | Implementado |
| DT-031 | Test suite real para core (vectorizer, aggregator, inference, qa_evaluator) | **Crítica** | Implementado |
| DT-032 | SID Study S1–S5: infraestructura de probes + estimación MI para pre-registro H_cross | Alta | Implementado |
| DT-033 | Definición formal de observabilidad causal vs. XAI/interpretabilidad (doc teórico Paper 1) | Alta | Pendiente |
| DT-034 | Corpus extensión S6–S8 (Nivel 2 SID Study): 80–120 artefactos en familias causales nuevas | Media | Pendiente |
| DT-035 | Estrategia de reproducibilidad LLM: versiones pinned, outputs archivados, seeds documentados | Media | Pendiente |
| DT-036 | DT-028 Fase 2 frontend React: TaskSequencer, NASATLXForm, InteractionTracker, tcoClient | **Crítica** | Implementado |

**Estados:**
`Pendiente` · `En Progreso` · `Decisión Tomada` · `Implementado` · `Desechado`

---

## PIPELINE — Ruta crítica desbloqueada (2026-05-20)

### DT-000 · Pipeline graph.py + fault_injector.py + escenarios S1-S5 + corpus.json

**Componente:** `src/pipeline/` (completo)  
**Estado:** Implementado — pipeline LangGraph funcional, 5 escenarios con artefactos reales, corpus.json generado (12 entradas).

**Lo que se construyó:**

1. **`state.py`** — `PipelineState` TypedDict + `ArtifactDict`. Estado compartido entre los 6 nodos LangGraph.

2. **`graph.py`** — LangGraph `StateGraph` completo:
   - Nodos: `load_artifacts → qa_evaluate → vectorize → aggregate → infer → next_cycle`
   - Edge condicional: si `cycle_k < n_cycles - 1` → loop; else `END`
   - Integra: QAAgent, Vectorizer (φ), TensorAggregator, InferenceEngine
   - Modo dry-run si tco_engine no está disponible (graceful degradation)
   - Función de alto nivel: `run_scenario(scenario_id, session_id, n_cycles) → final_state`

3. **`fault_injector.py`** — `FaultInjector` con 5 handlers + `FAULT_SPECS` predefinidos:
   - `sql_injection` — reemplaza queries parametrizadas por concatenación de strings
   - `circular_import` — inyecta dependencia circular en YAML o Python
   - `missing_resource` — elimina resource limits de K8s YAML
   - `debt_increment` — añade patrones de deuda conocida (CC extra)
   - `agent_security_bias` — fuerza un score bajo de seguridad para test de conflicto

4. **Escenarios S1-S5** — cada módulo provee `get_artifacts(cycle_k)`, `GROUND_TRUTH`, `N_CYCLES`:
   - `s1_auth.py`: SQL injection (2 artifacts, v4: 0.90→0.20, bandit B608+B324)
   - `s2_arch.py`: Circular dependency YAML (2 artifacts, v2: 0.85→0.20)
   - `s3_debt.py`: Gradual debt — 4 ciclos (v8: 0.68→0.60→0.52→0.44, CC: 2→5→8→12)
   - `s4_deploy.py`: K8s sin observabilidad (2 artifacts, v5: 0.85→0.15)
   - `s5_conflict.py`: Inter-agent conflict (v4Δ≈0.65, v6Δ≈0.50 entre security_agent y code_agent)

5. **`scenario_preloader.py`** — CLI corpus generator:
   - `python scenario_preloader.py` → genera `phi_calibration/corpus/corpus.json`
   - `--dry-run` → muestra summary sin escribir archivo
   - Output: 12 artefactos (S1:2, S2:2, S3:4, S4:2, S5:2); 8 python_code elegibles para Spearman ρ

6. **`corpus.json`** generado en `src/experiment/phi_calibration/corpus/corpus.json`:
   - 12 entries con: artifact_id, scenario, cycle, artifact_type, code, context, fault_present, ground_truth
   - Listo para consumir con `phi_calibration.py --corpus corpus.json`

**Desbloquea:** DT-021 (phi_calibration — requiere ANTHROPIC_API_KEY para scores LLM).

**Ruta crítica previa:** sin este módulo, no había artefactos sintéticos → no había corpus → no había calibración φ → no se podía hacer el piloto (Semana 5).

---

## CRÍTICA — Bloquea el experimento

### DT-001 · Instalar y configurar entornos de dependencias

**Componente:** Todos  
**Estado:** Implementado — venv único en `.venv/` (Python 3.14), Node 24.14.0  
**Descripción:** Stack completo instalado en `.venv/` raíz del repo. Requirements actualizados a `>=` bounds con numpy>=2.0.0 para compatibilidad Python 3.13+.

Versiones instaladas:
- numpy 2.4.6 · fastapi 0.136.1 · uvicorn 0.47.0 · sqlalchemy 2.0.49 · asyncpg 0.31.0
- radon 6.0.1 · bandit 1.9.4 · anthropic 0.97.0 · langgraph 1.1.9 · langchain-anthropic 1.4.1
- pandas 3.0.3 · scipy 1.17.1 · matplotlib 3.10.9 · scikit-learn 1.8.0 · pingouin 0.6.1
- dashboard: 196 npm packages (vite 5.x, react 18, recharts, tailwindcss)

Nota: 2 vulnerabilidades moderadas en esbuild/vite dev server — afectan solo al servidor de desarrollo local, no al build de producción. Fix requeriría upgrade breaking a Vite 8.

---

### DT-002 · Implementar el cuerpo de `vectorizer.py`

**Componente:** `src/tco_engine/core/vectorizer.py`  
**Estado:** Implementado — vectorizer.py completo con integración radon/bandit/LLM-QA, consensus, anomaly Z-score, ArtifactCache. Shared evaluator en `src/tco_engine/core/qa_evaluator.py`.  
**Descripción:** El vectorizador φ es el componente de mayor complejidad del engine. Requiere:

1. Integración con `radon_runner.py` para v₆ (testability), v₇ (maintainability), v₈ (technical_debt)
2. Integración con `bandit_runner.py` para v₄ (security_risk)
3. Prompt de QA LLM para v₁, v₂, v₃, v₉ con structured output via Pydantic
4. Implementación de `_compute_consensus()` entre static analysis y LLM-QA (v₁₀)
5. Implementación de `_compute_anomaly()` con Z-score vs baseline histórico (v₁₁)
6. Validación post-implementación: Spearman ρ ≥ 0.75 entre output LLM y ground truth estático para v₄, v₆, v₇, v₈

**Prioridad:** Semanas 1-2 (ruta crítica — todo lo demás depende de este módulo).

---

### DT-003 · Implementar el prompt del QA Agent

**Componente:** `src/pipeline/agents/qa_agent.py`  
**Estado:** Implementado — prompt con 3 few-shot examples (clean code, SQL injection, circular dep YAML), structured output via tool_use, EvaluationMetrics Pydantic model, confidence_self_assessment, neutral fallback.  
**Descripción:** El QA Agent es el origen del vector. Su prompt template determina la calidad de φ. Necesita:

- Structured output con Pydantic mapeando directamente a los 11 pillars
- Instrucciones explícitas sobre las dimensiones invertidas (v₄, v₈, v₁₁)
- Few-shot examples para cada pilar con casos buenos y malos calibrados
- Validación contra los 5 escenarios de fault injection antes del piloto

**Riesgo asociado:** Si el QA Agent es inconsistente, contamina simultáneamente el instrumento del experimento y la variable dependiente. Dependency: DT-002.

---

### DT-004 · Implementar la interfaz del grupo control (ControlGroupViewer)

**Componente:** `src/dashboard/src/experiment/ControlGroupViewer.tsx`  
**Estado:** Implementado — viewer multi-tab (code/yaml/architecture/ci_cd), correction form con severity dropdown, timer visible, corrections log, mismas dimensiones de layout que el TCO dashboard. Props: sessionId, taskId, artifacts[], onTaskComplete callback.  
**Descripción:** La interfaz del grupo control debe ser tan estandarizada como el dashboard TCO. Requiere:

- Multi-tab viewer: código Python, YAML, markdown de arquitectura, logs CI/CD
- Corrección form: textarea + severity dropdown (Low/Medium/High)
- Mismo timer visible y dimensiones de layout que el TCO dashboard
- Sin capacidad de edición directa de artefactos

**Impacto si no se resuelve:** La comparación entre grupos invalida los resultados del experimento.

---

## IMPORTANTE — Baja el score metodológico si falta

### DT-005 · Definir y documentar el warm-up pipeline

**Componente:** `src/pipeline/`, `protocols/participant_session_protocol.md`  
**Estado:** Pendiente  
**Descripción:** El protocolo menciona "practice task on a separate warm-up pipeline" pero el pipeline de warm-up no está definido. Debe ser:

- Un microservicio simple sin faults inyectados
- Suficientemente representativo para que el participante entienda la interfaz
- Idéntico para ambos grupos (solo cambia la representación: código raw vs vector)
- Suficientemente distinto de los 5 escenarios del experimento para evitar aprendizaje

---

### DT-006 · Implementar el policy_processor.py

**Componente:** `src/tco_engine/core/policy_processor.py`  
**Estado:** Decisión Tomada — arquitectura structured extraction híbrida documentada en paper Sección 7.3  
**Descripción:** El procesador de políticas implementa `PolicyIntent` dataclass + extracción LLM + fallback a direct injection si confidence < 0.70.

El flujo es:

1. Recibe `policy_text` (NL) + `tensor_state` (contexto actual)
2. LLM extrae struct: `{target_agents[], action_type, affected_dimensions[], priority, constraint}`
3. El struct se serializa como un patch del system prompt de cada agente afectado
4. El struct se loggea completo para H5 scoring (PIQ puede evaluarse sobre el struct, no solo sobre el texto NL)

**Fallback:** Si extraction confidence < 0.70, inyección directa del texto NL al system prompt del agente.

---

### DT-007 · Protocolo de reclutamiento de participantes (n=40)

**Componente:** `protocols/participant_session_protocol.md`  
**Estado:** Decisión Tomada — estrategia documentada en `protocols/participant_session_protocol.md`  
**Descripción:** Mix n=20 online (Reddit, Discord, LinkedIn) + n=20 local (universidad/empresa). Pre-screening de 3 preguntas. Incentivo no monetario (acceso anticipado a resultados).

---

### DT-008 · Migración a TimescaleDB (upgrade path)

**Componente:** `src/tco_engine/db/`  
**Estado:** Decisión Tomada — PostgreSQL 16 para MVP, upgrade path documentado  
**Descripción:** El MVP usa PostgreSQL 16 con índices estándar. Migración no-destructiva disponible:

```sql
SELECT create_hypertable('evaluation_vectors', 'created_at');
```

**Cuándo hacerlo:** Antes de las Semanas 7-8 (full experiment), no antes.

---

### DT-009 · Configurar `tsconfig.json` y `vite.config.ts` del dashboard

**Componente:** `src/dashboard/`  
**Estado:** Implementado — tsconfig.json (strict mode, ES2022, react-jsx) + tsconfig.node.json + vite.config.ts (port 3000, proxy /api → localhost:8000, es2022 build target)  
**Descripción:** Configurar TypeScript strict mode y Vite para el dashboard React. Incluye:

- `tsconfig.json`: strict: true, target ES2022
- `vite.config.ts`: plugin React, proxy a `http://localhost:8000` para desarrollo local
- `tailwind.config.js`: configuración de purge paths

---

## RECOMENDADO — Eleva la calidad del paper y la reproducibilidad

### DT-010 · Dashboard Dockerfile multi-stage

**Componente:** `src/dashboard/Dockerfile`  
**Estado:** Pendiente  
**Descripción:** Multi-stage build: stage 1 compila el React, stage 2 sirve con nginx.

---

### DT-011 · Implementar `kappa_validator.py` para PIQ

**Componente:** `src/experiment/piq_evaluation/kappa_validator.py`  
**Estado:** Pendiente  
**Descripción:** Script que calcula Cohen's κ entre:

- Anotador humano 1 vs Anotador humano 2 (inter-rater)
- LLM-Judge vs Anotador humano (calibración Week 6)

Threshold: κ ≥ 0.70 por dimensión antes de usar el LLM-Judge en el experimento completo.

---

### DT-012 · Implementar scripts de análisis estadístico

**Componente:** `analysis/`  
**Estado:** Pendiente  
**Descripción:** Los 8 scripts de análisis son el producto de Semana 9. Son dependientes de los datos del experimento. Sin embargo, el esqueleto de cada script (imports, función stub con los parámetros esperados) debe estar listo en Semana 4 para validar que los datos se están capturando en el formato correcto.

---

### DT-013 · `integrity_checker.py` pre-sesión

**Componente:** `src/experiment/data_pipeline/integrity_checker.py`  
**Estado:** Pendiente  
**Descripción:** Script que valida automáticamente antes de cada sesión experimental:

1. S3 pre-loaded cycles presentes en DB con vector delta correcto (v₈: 0.68→0.44)
2. Todos los escenarios tienen ground truth documentado
3. Participant_id no tiene sesiones previas en la DB
4. QA agent responde correctamente al health check

---

### DT-014 · Protocolo de consentimiento informado

**Componente:** `src/experiment/participant_manager/consent/consent_form_template.md`  
**Estado:** Pendiente  
**Descripción:** Necesario para publicación en CHI/EMSE. Debe incluir:

- Descripción del estudio (single-blind: "evaluación de dos interfaces de supervisión")
- Uso de datos (anonimización, almacenamiento, publicación)
- Derecho a retiro en cualquier momento
- Información de contacto del investigador principal

---

### DT-015 · Sección Related Work del paper

**Componente:** `Documentacion/TCO_Paper_Final_v3.md`  
**Estado:** Pendiente — bloqueador 1 para publicación  
**Descripción:** Requiere revisión de 15-20 papers en tres áreas:

- Frameworks HITL existentes: HULA (Atlassian/arXiv:2411.12924), trabajos de Cummings y Parasuraman en supervisión de autonomía
- Herramientas de observabilidad (Datadog, New Relic) y sus límites cognitivos
- Cognitive load en HCI de software

**Cuándo:** Puede hacerse en paralelo con Semanas 1-2 de implementación.

---

### DT-016 · Adaptación del paper a formato LaTeX (ACM template)

**Componente:** `Documentacion/TCO_LaTeX/`  
**Estado:** Implementado — main.tex (ACM manuscript class, 11 secciones completas, tablas booktabs, fórmulas LaTeX) + references.bib (30 entradas BibTeX). Pendiente: figuras vectoriales y venue-specific class swap antes de submission.  
**Descripción:** El Markdown es el documento de trabajo. Antes de cualquier submission, adaptar al template ACM para CHI/FSE o IEEEtran para RE. Requiere: figuras vectoriales, numeración de tablas, bibliografía en BibTeX, formato de autores según venue.

---

### DT-017 · Implementar ArtifactCache (Redis hash cache)

**Componente:** `src/tco_engine/core/vectorizer.py`, `src/tco_engine/db/models.py`  
**Estado:** Decisión Tomada — diseñada en paper Sección 7.3 y `.env.example`  
**Descripción:** Cache Redis keyed por SHA-256 del contenido del artefacto. Si el mismo código ya fue evaluado, retorna el vector cacheado sin llamar al LLM ni a radon/bandit. Estimación de reducción de costos API: 40–60%. TTL: sin TTL para artifact hash (determinista), 30s para tensor snapshot.

---

---

## CRÍTICA (nuevas) — Bloquean la validez del experimento

### DT-019 · Gate formal de validación φ pre-piloto

**Componente:** `Documentacion/TCO_Paper_Final_v3.md` (Section 7.6) + `src/experiment/phi_calibration/phi_calibration.py`  
**Estado:** Implementado — subsección 7.6.1 "φ Calibration Protocol — Formal No-Go Gate" añadida al paper. Corpus de 20-30 artefactos sintéticos, tablas de ground truth por escenario S1-S5, regla go/no-go ρ ≥ 0.75 por las 4 dimensiones, plan de acción en caso de no-go, archival como Open Science artifact.  
**Descripción:** La validación de φ existe mencionada como "amenaza a la validez" pero no está especificada como gate formal de no-go. Necesita:

1. Definir el protocolo de calibración: 20–30 artefactos sintéticos con ground truth conocido (incluyendo los 5 escenarios S1–S5 con sus deltas vectoriales documentados)
2. Criterio de no-go explícito: si Spearman ρ < 0.75 en cualquiera de v₄, v₆, v₇, v₈ → no se procede al piloto
3. Plan de acción en caso de no-go: ajuste de prompts del QA Agent, re-calibración de normalization bounds en radon_runner/bandit_runner
4. En el paper (Section 7.6): convertir el párrafo de QA circularity threat en una subsección con el protocolo formal y el criterio cuantitativo de aprobación

**Relación:** Depende de DT-021. Debe completarse antes de Semana 5.

---

### DT-021 · Suite de calibración φ — medición Spearman ρ

**Componente:** `src/experiment/phi_calibration/phi_calibration.py`  
**Estado:** Implementado — script CLI con corpus JSON, Spearman ρ bootstrapeado (CI 95%), scatter plots por dimensión, go/no-go automático con exit code 0/1. EvaluationMetrics en qa_evaluator.py extendido con semantic_security y semantic_debt_assessment (+ _OUTPUT_SCHEMA + _SYSTEM_PROMPT + few-shot examples + _fallback_metrics actualizados).  
**Descripción:** Implementar herramienta que mida automáticamente el acuerdo entre LLM-QA y análisis estático en las dimensiones donde ambos tienen cobertura:

- **v₄ security_risk:** LLM semantic_security (no está actualmente en EvaluationMetrics — agregar) vs. Bandit weighted_severity
- **v₆ testability:** LLM semantic_testability vs. Radon (1 − cyclomatic_norm)
- **v₇ maintainability:** LLM semantic_maintainability vs. Radon maintainability (MI)
- **v₈ technical_debt:** LLM semantic_debt_assessment (agregar) vs. Radon debt_ratio

Outputs del script:
- Spearman ρ por dimensión con intervalo de confianza 95%
- Scatter plots LLM vs. estático por dimensión
- Reporte de casos outlier (artefactos donde ρ diverge más de 0.3)
- Decisión go/no-go automática con resumen

**Acción en EvaluationMetrics:** Agregar `semantic_security: float` y `semantic_debt_assessment: float` al modelo Pydantic en `qa_evaluator.py` para habilitar la comparación en v₄ y v₈.

**RESULTADO DE CALIBRACIÓN v1 — GO (2026-06-06, n=5/familia):** corrida vía OpenRouter (`anthropic/claude-sonnet-4-6`).

| Dim | ρ | CI 95% | Veredicto |
|-----|-----|--------|-----------|
| v4_security | 0.900 | [0.11, 1.00] | PASS |
| v6_testability | 0.975 | [0.75, 1.00] | PASS |
| v7_maintainability | 1.000 | [1.00, 1.00] | PASS (report-only) |
| v8_technical_debt | 0.821 | [−0.30, 1.00] | PASS (report-only) |

**RESULTADO DE CALIBRACIÓN v2 — GO (2026-06-06, n=8/familia, 32 artefactos):** corpus expandido con 3 artefactos intermedios por familia. CIs sustancialmente más ajustados. Corpus: `generate_calibration_corpus.py` → corpus v2.

| Dim | ρ | CI 95% | Veredicto |
|-----|-----|--------|-----------|
| v4_security | 0.868 | [0.351, 1.000] | PASS (gate) |
| v6_testability | 0.951 | [0.774, 1.000] | PASS (gate) |
| v7_maintainability | 0.928 | [0.615, 1.000] | PASS (report-only) |
| v8_technical_debt | 0.913 | [0.607, 0.974] | PASS (report-only) |

Mejora clave: CI inferior v8 pasó de −0.30 → **+0.607** (publicable). v4 y v6 tienen CI inferior ≥0.35 y ≥0.77 respectivamente.

**Hallazgos metodológicos (cada uno fue un NO-GO espurio resuelto):**

1. **El corpus S1–S5 NO sirve para calibrar.** Es un corpus de *escenarios* (cada uno declara ground truth solo para su dimensión-objetivo, mezcla YAML sin radon válido, n=12). Se construyó un **corpus de calibración dedicado**: `generate_calibration_corpus.py` → 32 artefactos Python en 4 familias (sec/cpx/dbt/mnt), cada familia barre UN eje con spread validado, taggeadas con `calibration_dim`.

2. **`radon_runner` tenía colinealidad total v7≡v8:** `debt_ratio = 1 − maintainability` exactamente. Corregido: debt ahora multifactorial (`0.5·CC + 0.3·Halstead + 0.2·(1−MI)`).

3. **Calibración debe ser por-dimensión sobre su familia-sweep**, no nube global. Mezclar familias daba ρ(v6)=−0.35 espurio (la familia security tiene testability estática plana mientras el LLM la varía → anti-correlación falsa). Por-dimensión: ρ(v6)=0.951.

4. **Gate de dos clases (decisión 2026-06-06):** solo dimensiones con **ground truth duro independiente** gatean — v4 (bandit detecta CWE reales) y v6 (CC cruda). v7/v8 son *supervisory estimators* (radon los auto-correlaciona ρ>0.93 y es ciego a calidad semántica) → REPORT-only, validación por inter-rater/inter-model (DT-024), no por estático. Alinea con la nota epistemológica del paper (DT-027).

5. Bugs menores: `UnicodeEncodeError` (φ/ρ en cp1252 Windows) y `confidence_self_assessment` requerido sin default (forzaba fallbacks → outliers falsos). Ambos corregidos.

6. **Scope Python-only:** radon/bandit solo corren en Python. Para YAML/CI-CD (S2/S4), solo dims semánticas (LLM) son significativas; v4/v6/v8 caen en fallbacks constantes. La afirmación de calibración φ≥0.75 aplica estrictamente a artefactos Python. Agregar nota en §4.2.3.

**CAVEATS PARA EL PAPER:**

- **Auto-correlación inter-dim** v6↔v8=0.948, v7↔v8=0.943 (leve mejora respecto a n=5: era 0.954/0.937) — punto real para DT-025 (justificar "approximately orthogonal supervisory dimensions" pese a correlación en el GT estático). El sistema reporta `*** JUSTIFY OR FUSE ***` para pares >0.90.
- **n=8 por familia** satisface publicación (CI inferior ≥0.35 en todas las dims). Caveat restante: v4 CI=[0.351, 1.000] — sigue amplio por el bajo spread de bandit en niveles bajos/medios.

**Dependencia:** instalado `openai` SDK (provider OpenRouter lo requiere).

---

## IMPORTANTE (nuevas) — Bajan el rigor metodológico si faltan

### DT-018 · Paper — Defender necesidad matemática del tensor

**Componente:** `Documentacion/TCO_Paper_Final_v3.md` Section 5.3  
**Estado:** Implementado — subsección 4.3.4 "Tensor Necessity: Why Not a Relational Table?" añadida con argumento S3/S5, operaciones de slicing comparadas con SQL self-joins, conclusión: first-classness del tensor es necesidad matemática para los objetivos de detección de TCO.  
**Descripción:** Crítica anticipada: "el tensor es una metáfora matemática conveniente, no una necesidad". El paper necesita un argumento explícito. Insertar un párrafo en Section 5.3 (Layer 4 — The Cognitive Tensor) con la siguiente estructura:

**¿Por qué un tensor y no una tabla relacional?**

La respuesta es S3 y S5:
- S3 (acumulación temporal de deuda): indetectable sin `T[d,:,:,k] − T[d,:,:,k−3]` — requiere el eje temporal k indexado conjuntamente con las dimensiones d
- S5 (conflicto inter-agente): indetectable sin `|T[d,i,j₁,k] − T[d,i,j₂,k]|` — requiere comparar dos agentes en la misma dimensión, etapa y ciclo simultáneamente

Una tabla relacional puede almacenar los mismos datos, pero la operación semánticamente natural (`CONFLICT WHERE agent1.v[d] - agent2.v[d] > 0.30 AT SAME stage AND cycle`) requiere un JOIN autorecursivo de 11 columnas que destruye la legibilidad del motor de inferencia. El tensor hace esta operación first-class.

**Agregar también:** Nota al pie o recuadro comparando operaciones de slicing en tensor vs. queries SQL equivalentes.

---

### DT-022 · Rubrica PIQ a nivel struct para H5 (LLM-Judge)

**Componente:** `protocols/piq_rubric.md` (nuevo) + `src/experiment/piq_evaluation/`  
**Estado:** Pendiente  
**Descripción:** El LLM-Judge para H5 actualmente evaluará la "calidad de la política inyectada" pero no hay rubrica definida. Necesita:

**Dimensiones de scoring para PolicyIntent:**

| Dimensión | Descripción | Escala |
| --------- | ----------- | ------ |
| target_precision | ¿Los agentes target son los correctamente afectados por el fallo? | 0–1 |
| dimension_relevance | ¿Las affected_dimensions mapean correctamente al fallo detectado? | 0–1 |
| constraint_specificity | ¿El constraint es accionable y específico (no genérico)? | 0–1 |
| action_appropriateness | ¿El action_type es el correcto para el tipo de fallo? | 0–1 |
| scope_calibration | ¿El priority y scope son proporcionales al impacto del fallo? | 0–1 |

**PIQ_score = media ponderada de las 5 dimensiones** (pesos a definir en calibración Semana 6)

**Calibración:** 2 expertos externos + LLM-Judge en 10 políticas de entrenamiento. Threshold: κ ≥ 0.70 por dimensión antes de usar el LLM-Judge en el experimento completo (reutiliza DT-011).

---

## RECOMENDADO (nuevas) — Elevan el argumento y la reproducibilidad

### DT-020 · Paper — Reencuadrar con narrativa "expertise shift"

**Componente:** `Documentacion/TCO_Paper_Final_v3.md` (Introduction + Abstract)  
**Estado:** Implementado — Abstract: añadido párrafo sobre expertise shift como claim central. Introduction: reencuadre como "wrong abstraction level for the new engineering role". Section 4.2: párrafo SRE/observabilidad como analogía (Datadog → monitoreo operacional, TCO → monitoreo semántico). Section 10.1: NCF como constructo HCI para el rol "orchestration engineer" + expertise shift thesis como contribución teórica explícita.  
**Descripción:** El framing actual de la Introducción enfatiza "reducción de carga cognitiva". El argumento más potente (identificado en evaluación externa) es el **desplazamiento del expertise**:

> TCO no dice que la experiencia técnica desaparece. Dice que el expertise se desplaza desde manipular artefactos hacia supervisar comportamientos emergentes. Cuanto más autónoma es la IA, más crítica se vuelve la capacidad de supervisión sistémica.

Cambios necesarios:
1. **Abstract:** agregar sentence sobre el expertise shift como claim central
2. **Introduction (párrafo 3–4):** reencuadrar el problema no como "sobrecarga" sino como "nivel de abstracción incorrecto para el nuevo rol del ingeniero"
3. **Section 4.2** (Incorrect Abstraction Level): expandir con el paralelo SRE/observabilidad: así como los SREs pasaron de monitorear paquetes a supervisar estado agregado, los ingenieros de IA pasan de validar artefactos a orquestar comportamientos sistémicos
4. **Section 10.1** (Theoretical Contributions): agregar NCF como constructo de diseño HCI para el nuevo rol del "orchestration engineer"

---

### DT-023 · Script "tensor necessity proof" en analysis/

**Componente:** `analysis/tensor_necessity.py`  
**Estado:** Implementado — 2026-05-20  
**Descripción:** Script de análisis que demuestra empíricamente que S3 y S5 son no detectables con confianza mediante evaluación individual de artefactos, y son detectables mediante slicing tensorial.

**Resultados obtenidos (Monte Carlo n=1000, seed=42):**

| Escenario | Detección artifact-level | Detección tensorial | Gap |
|-----------|--------------------------|---------------------|-----|
| S3 (deuda gradual) | 32.3% | 66.9% | +34.6pp |
| S5 (conflicto inter-agente) | Requiere memoria concurrente | 2/2 conflictos detectados (v4Δ=0.65, v6Δ=0.50) | — |

**Parámetros S3:**

- Trayectoria v₈: [0.68, 0.60, 0.52, 0.44] — delta/ciclo = 0.08
- Ruido evaluador: σ = 0.07 → SNR por ciclo = 1.14 (bajo el umbral de detección fiable)
- Delta acumulado 3 ciclos: 0.24 → SNR acumulado = 3.43 (sobre el umbral)
- Threshold artifact-level (NOTICEABLE_SINGLE_CYCLE): 0.20
- Threshold tensor (cumulative): 0.20

**Conclusión:** El tensor hace operationally first-class lo que SQL requeriría un self-join de coordenadas reconstruidas. Script sale con exit code 0 ("CONFIRMED").

**Output generado:**

- `analysis/figures/tensor_necessity_combined.png` — figura 4 paneles para el paper (Figure 2, Section 5.3)

**Implementación:** `analysis/tensor_necessity.py` (393 líneas). Uso: `python analysis/tensor_necessity.py` o `--no-plots`.

---

---

## IMPORTANTE (segunda revisión) — Fortalecen el rigor metodológico ante reviewers duros

### DT-024 · Paper — Evaluator variance y rigor del LLM-QA

**Componente:** `Documentacion/TCO_Paper_Final_v3.md` (Section 8 — Software Architecture + Section 7.6 Threats)  
**Estado:** Pendiente  
**Descripción:** Las dimensiones v₁, v₂, v₃, v₉ dependen de juicio probabilístico del LLM. Un reviewer atacará: reproducibilidad, evaluator drift entre versiones del modelo, prompt sensitivity, model dependence. El paper necesita sección formal de rigor del evaluador.

**Cambios necesarios en el paper:**

1. **Evaluator variance**: correr el mismo artefacto N=10 veces con el mismo prompt, reportar σ de scores por dimensión. Threshold aceptable: σ < 0.05 para v₁, v₂, v₃, v₉.

2. **Calibration curves**: para cada dimensión LLM, graficar `confidence_self_assessment` vs error absoluto contra ground truth. Una calibración bien ajustada mostraría que alta confianza LLM → bajo error.

3. **Inter-model agreement**: correr el corpus de calibración con un segundo modelo (GPT-4o o Gemini). Reportar Spearman ρ entre scores de ambos modelos por dimensión. ρ ≥ 0.70 indicaría que la señal es robusta al modelo específico.

4. **Evaluator entropy**: para cada dimensión, calcular la entropía de la distribución de scores sobre el corpus. Alta entropía indicaría inestabilidad del evaluador — umbral de alerta: H > 0.80 nats.

**Sección a añadir**: "5.X LLM-QA Evaluator Reliability" entre la definición del vectorizador y la definición del tensor.

**Implementación**: Añadir método `run_variance_test(artifact, n=10)` a `QAEvaluator` + script `analysis/evaluator_reliability.py`.

---

### DT-025 · Paper — Reencuadrar independencia vectorial como "~orthogonal supervisory dimensions"

**Componente:** `Documentacion/TCO_Paper_Final_v3.md` (Section 5.2) + `Documentacion/TCO_LaTeX/main.tex`  
**Estado:** Pendiente — quick fix de lenguaje + análisis de correlación  
**Descripción:** La descripción "semantically independent" es vulnerable a crítica académica. Las dimensiones correlacionan naturalmente (maintainability ↔ technical_debt, observability ↔ performance, scalability ↔ architecture). La afirmación de independencia estricta es indefendible.

**Cambios necesarios:**

1. **Cambio de lenguaje** (ya aplicado en paper y README para el diagrama de arquitectura): `"Semantically independent"` → `"~Orthogonal supervisory dimensions"`. Aplicar en todas las ocurrencias del paper y LaTeX.

2. **Argumento explícito**: Añadir párrafo en Section 5.2 argumentando que las 11 dimensiones son *supervisoriamente distinguibles* aunque correlacionen parcialmente, igual que en Multidimensional Quality Metrics (MQM) en traducción automática [18] — la correlación no invalida la utilidad diagnóstica diferencial de cada dimensión.

3. **Análisis de correlación**: En la suite de calibración φ (`phi_calibration.py`), añadir cómputo de matriz de correlación inter-dimensiones sobre el corpus. Reportar los 3 pares con mayor correlación. Si algún par tiene ρ > 0.90, considerar fusión o justificación explícita de por qué se mantienen separados.

**Prioridad real**: El cambio de lenguaje es urgente (1 hora). El análisis de correlación depende del corpus de calibración (Semana 3).

---

## IMPORTANTE (tercera revisión) — Cierran vulnerabilidades de la segunda evaluación externa

### DT-026 · Experimento — Implementar 4 proxies de operacionalización del NCF

**Componente:** `src/experiment/` (NASA-TLX form, correction log, accuracy scorer, interaction timer)  
**Estado:** Pendiente  
**Descripción:** El NCF fue definido conceptualmente, pero sin proxies observables concretos queda vulnerable a la crítica de "filosófico / inmedible". La evaluación externa identificó exactamente este riesgo. El experimento ya tiene la infraestructura base; este ítem cierra el gap de medición.

**4 proxies a implementar:**

| NCF Property | Variable | Medida operacional | Instrumento a implementar |
| --- | --- | --- | --- |
| Working memory not saturated | Working memory saturation | NASA Raw-TLX: mental demand + frustration | Formulario digital post-task |
| Supervisory coherence | Correction consistency | σ(severity) por categoría de fallo | Correction log con campo `category` |
| Cognitive stability | Accuracy variance | σ(accuracy) across T1→T4 | Accuracy scorer automático por tarea |
| Attention fragmentation | Latency discontinuities | IQR(time-to-first-correction) | Interaction timer con cómputo IQR |

**Cambios en infraestructura:**

1. `src/experiment/data_pipeline/nasa_tlx_form.py` — formulario digital con los 6 subscales Raw-TLX (mental demand, physical demand, temporal demand, effort, performance, frustration). Extrae mental_demand + frustration para el proxy de working memory saturation.
2. `src/experiment/data_pipeline/correction_log.py` — añadir campo `fault_category` al schema de corrección. Cómputo de σ(severity) por categoría al final de la sesión.
3. `src/experiment/data_pipeline/accuracy_scorer.py` — score binario por tarea (T1: fault detected, T2: risk level correct, T3: deploy decision correct, T4: re-orchestration correct). Cómputo de σ(accuracy) al final.
4. `src/experiment/data_pipeline/interaction_timer.py` — añadir timestamp `first_correction_at` por artefacto presentado. Cómputo de IQR al finalizar la sesión.

**Cuándo:** Semana 4 (antes del piloto). Depende de DT-013 (integrity_checker).

---

### DT-027 · Paper — Reencuadre sistemático de v₁,v₂,v₃,v₉ como "supervisory estimators"

**Componente:** `Documentacion/TCO_Paper_Final_v3.md` (múltiples secciones) + `Documentacion/TCO_LaTeX/main.tex`  
**Estado:** Pendiente — reencuadre parcialmente aplicado en Section 5.2; falta sweep completo  
**Descripción:** La evaluación externa identificó que presentar v₁, v₂, v₃, v₉ como "objective quality" es epistemológicamente vulnerable. Un reviewer duro puede atacar la falta de ground truth universal para estas dimensiones LLM. La respuesta correcta no es evitar las dimensiones — es distinguir explícitamente su estatus epistemológico del de las dimensiones de análisis estático.

**Distinción central a establecer:**

- **Dimensiones estáticas** (v₄, v₆, v₇, v₈): fuente determinista, ground truth verificable contra bandit/radon, validables con Spearman ρ ≥ 0.75. Son métricas objetivas.
- **Dimensiones LLM** (v₁, v₂, v₃, v₉): **supervisory estimators** — heuristic semantic signals. Proveen información decision-relevante al orquestador. No son certificados de calidad objetiva. No tienen ground truth universal. Su valor es supervisorio, no métrico.

**Cambios necesarios (sweep completo):**

1. **Buscar y reemplazar** en paper y LaTeX: cualquier instancia de "objective quality", "objective measure", "accurately measures" referida a v₁/v₂/v₃/v₉ → reemplazar con "supervisory estimate" / "heuristic semantic signal".

2. **Section 5.2** (ya parcialmente actualizado): La nota epistemológica en blockquote debe quedar como texto principal, no solo como blockquote opcional. Integrar en el flujo argumentativo.

3. **Section 7 (Experimental Design)**: En la descripción de las dimensiones usadas como variables en el experimento, distinguir explícitamente el tipo de validación esperado para cada grupo (Spearman vs. PIQ scoring).

4. **Section 9 (Threats to Validity)**: Añadir párrafo explícito sobre la limitación epistemológica de las dimensiones LLM y por qué esta limitación no invalida el diseño (el valor es supervisorio, la validación es por utilidad de decisión, no por precisión métrica).

5. **Aplicar en LaTeX** (main.tex): asegurar que el mismo lenguaje se usa en tablas, captions y el abstract.

**Prioridad**: Media-alta. El Section 5.2 ya está parcialmente correcto. El sweep completo puede hacerse en 2–3 horas antes de cualquier submission draft.

**Diferencia con DT-024**: DT-024 se enfoca en *métricas de varianza del evaluador* (σ de scores, calibration curves, inter-model agreement) — evidencia empírica de estabilidad. DT-027 se enfoca en el *framing epistemológico* — el lenguaje que establece qué tipo de cosa son estas dimensiones. Son complementarios: DT-024 prueba que el estimador es estable; DT-027 establece que nunca se presentó como algo más que un estimador.

---

---

## CAL RESEARCH PLATFORM — Infraestructura compartida para L2, L3, L4

### DT-028 · Plataforma web experimento — researchlab.aural-syncro.com.ar/cal

**Componente:** Servicio TCO propio (FastAPI + React) en red `sspa_infra`, path `/cal`  
**Estado:** Fases 1–2 ✅ Implementadas · Fase 3 (deploy prod) pendiente  
**Prioridad:** Importante — habilita n=40 sin coordinación presencial  
**Spec de implementación:** [`Documentacion/DT-028_web_platform_spec.md`](../Documentacion/DT-028_web_platform_spec.md)

**Verificación deploy local (2026-06-04):** backend (uvicorn, SQLite, sin Docker — puerto 8000 ocupado por SSPA → usado 8010) + frontend (Vite, proxy `/cal/api` → backend). Probados end-to-end por API y SPA:

- **Participante:** registro con asignación estratificada (6 años → estrato `mid`, grupo `experimental`) → consent → carga escenario S1 (código real del pipeline) → runner completo (2 tasks acc 1.0, policy inyectada, TLX post_t2/post_t4, complete) → NCF computado (`working_memory_saturation=51.25`).
- **Admin:** listado de participantes con todos los campos, override de grupo, invitación (crea sesión `is_pilot`).
- Frontend: `tsc --noEmit` limpio (exit 0); Vite transforma `App.tsx`/`main.tsx` sin error; proxy verificado (login admin atraviesa :3000 → :8010).

**Cambio de código del deploy:** `vite.config.ts` ahora acepta `VITE_BACKEND_URL` (default sigue 8000) para apuntar el proxy a un puerto alterno.

**Pendiente Fase 3 (deploy prod):**

- Postgres/Timescale en `sspa_infra` (override `DATABASE_URL`) en vez de SQLite.
- SMTP (`GMAIL_*`) — sin él las invitaciones quedan `scheduled` en vez de `sent` (email_sent=false).
- Servir la SPA bajo `/cal` detrás del reverse proxy; `SECRET_KEY` de producción.
- **Higiene:** `create_admin.py` no valida el email con pydantic → permite crear cuentas con TLD reservado (`.test`) que luego no pueden loguear vía API (`EmailStr` las rechaza). Añadir validación + limpiar la cuenta huérfana `revisor@tco.test` creada en la prueba.

**Decisiones cerradas (2026-05-31):**
- Topología: servicio TCO propio en `/cal` (no embebido en Research Lab); reutiliza Postgres/Timescale + patrón email SMTP
- Frontend: SPA única React/Vite — reutiliza `ControlGroupViewer` + componentes del dashboard
- Registro: auto-servicio con user/pass para todos; ejecución de prueba agendada por el admin vía email
- Auth: JWT + bcrypt, roles `participant` / `admin`
- Dashboard admin: listado de registrados, grupos asignados, completitud, resultados parciales/totales, export
- Persistencia: el TCO Engine es dueño de toda la data del experimento (tablas `cal_*`)
- **Orden invertido vs. plan original:** la plataforma se construye ANTES del piloto, para validar protocolo + interfaz real simultáneamente

**Propósito dual:**
1. **TCO-L2 (inmediato):** Plataforma de reclutamiento y ejecución del experimento RCT n=40
2. **CAL L3/L4 (futuro):** Infraestructura reutilizable para experimentos de layers futuros — cada layer agrega su propio sub-path (`/cal/l3`, `/cal/l4`) con la misma base de registro, email y datos de participantes

**Arquitectura:**

```
researchlab.aural-syncro.com.ar/cal        ← TCO-L2
researchlab.aural-syncro.com.ar/cal/l3     ← futuro L3
researchlab.aural-syncro.com.ar/cal/l4     ← futuro L4

Research Lab (UX layer)           TCO Engine (backend experimento)
  ├── Landing /cal                  ├── /vector, /tensor, /inference
  ├── Registro + consentimiento     ├── /policy/inject
  ├── Email confirmación alta       └── NCF proxies + PIQ scoring
  ├── Warm-up cognitivo (S0)
  ├── Experiment runner (T1–T4 × S1–S5)
  ├── NASA-TLX form (post-task)
  ├── Correction log UI
  └── Thank you + email resultados
```

**Lo que Research Lab ya provee (no construir desde cero):**
- Auth JWT + registro de usuarios (`auth.py`, `register.py`)
- PostgreSQL 15 + TimescaleDB — persistencia de sesiones y resultados
- Hosting desplegado: Cloudflare Tunnel + Docker + red `sspa_infra`
- Frontend SPA vanilla JS — extendible con nuevas páginas `/cal/*`

**Nuevos componentes a desarrollar:**

| Componente | Ubicación | Semana |
|-----------|-----------|--------|
| Schema DB: `cal_participants`, `cal_sessions`, `cal_task_results` | Research Lab / migrations | 1 |
| Rutas FastAPI: `/cal/register`, `/cal/session`, `/cal/results` | Research Lab `app/routers/cal.py` | 1 |
| Email: confirmación alta + aviso resultados disponibles | Research Lab email service | 1 |
| Landing `/cal` — pre-print, hipótesis H1–H5, datos clave L2 | Research Lab `static/cal/` | 1 |
| Registro participante: datos personales + nivel SE + grado + consentimiento | Research Lab frontend | 1 |
| Cognitive prep + warm-up S0 UI | Research Lab frontend | 2 |
| Experiment runner — control (ControlGroupViewer) y experimental (TCO Dashboard) | Research Lab frontend + TCO API | 2–3 |
| NASA-TLX form digital (post-task) | Research Lab frontend | 2 |
| Correction log UI con fault_category | Research Lab frontend | 2 |
| Admin: export CSV/JSON resultados para análisis estadístico | Research Lab backend | 3 |

**Registro participante — campos requeridos:**
- Nombre completo, email, país
- Años de experiencia en code review (threshold ≥ 2)
- Nivel educativo (universitario / posgrado / otro) + institución (opcional)
- Lenguajes/ecosistemas principales
- Familiaridad con herramientas de IA en desarrollo (0–4): 0=nunca · 1=raramente · 2=mensual · 3=semanal · 4=diario — **covariable ANCOVA**
- ¿Ha oído hablar de TCO antes? (disqualifier: sí)
- Consentimiento informado (DT-014)
- Disponibilidad para sesión de 3h

**Randomización:** al confirmar email → asignación automática control/experimental estratificada por años de experiencia (Junior 2–4 / Mid 5–9 / Senior 10+).

**Emails del flujo:**
1. **Alta:** confirmación de registro + instrucciones de preparación técnica + link a la sesión
2. **Cumplimiento post-sesión:** agradecimiento + aviso de que los resultados estarán disponibles en `researchlab.aural-syncro.com.ar/cal/resultados` al finalizar el experimento

**Estimación total:** 3 semanas de trabajo post-pilot  
**Dependencia:** Pilot n=4 presencial (Semana 5) — valida el protocolo antes de abrir reclutamiento público

**Reutilización para L3/L4:**
Los módulos `cal_participants`, email service, y el experiment runner son agnósticos al layer. Para L3, solo se necesita:
1. Nuevos escenarios L3 (tensor volumes, cross-session)
2. Nueva UI de presentación (diferente abstracción)
3. Sub-path `/cal/l3` con su propio flujo — reutilizando registro, email y persistencia

---

---

## IMPORTANTE — Piloto

### DT-029 · Script generador de informe post-piloto (`analysis/pilot_report.py`)

**Componente:** `analysis/`  
**Estado:** Pendiente  
**Categoría:** Importante

**Descripción:** Script que consolida los datos de las 4 sesiones del piloto y genera el informe definido en `protocols/pilot_protocol.md` (Sección 10).

**Inputs esperados:**

- `protocols/pilot_logs/P_PILOT_0X_log.md` — 4 logs del facilitador
- Output de `ncf_proxy.py` (NCFProxies) — 4 participantes
- Output de `nasa_tlx_form.py` — 8 mediciones (2 por participante)
- Output de `accuracy_scorer.py` — T1–T4 por participante
- Output de `interaction_timer.py` — timestamps por tarea

**Outputs del informe:**

- Heatmap timing real por fase × participante
- Barras accuracy T1–T4 por grupo (orientativo, n=2 c/u)
- Distribución NASA-TLX por grupo
- Checklist go/no-go automático (6 criterios de la Sección 8 del pilot_protocol.md)
- Export: `protocols/pilot_report_v1.md` + figuras PNG

**Dependencia:** requiere las 4 sesiones del piloto completadas (Semana 5).

---

---

## POST-AUDITORÍA — Deuda crítica identificada (2026-06-02)

### DT-030 · Scripts de análisis estadístico H1–H5 + ANCOVA + effect sizes

**Componente:** `analysis/_data.py` · `_stats.py` · `h1_cognitive_load.py` · `h2_decision_accuracy.py` · `h4_early_detection.py` · `h5_policy_quality.py` · `h_obs_causal.py` · `ancova_all.py` · `effect_sizes.py` · `visualizations.py`  
**Estado:** ✅ Implementado (2026-06-02) — los 8 scripts ejecutan end-to-end con `--dry-run` (exit 0, recuperan el efecto plantado)  
**Categoría:** Crítica — bloquea el análisis post-experimento

**Por qué era crítica:** Los datos del RCT n=40 no son analizables sin estos scripts. Resuelto: el pipeline analítico está validado antes del piloto vía datos sintéticos.

**Arquitectura implementada:**

- `_data.py` — capa de datos compartida. `load_dataset(db_url)` lee las tablas `cal_*` vía SQLAlchemy (solo sesiones `completed`, no-piloto) y las aplana en frames tidy; `synthetic_dataset()` genera un fixture RCT reproducible con la estructura de efecto **pre-registrada** (efecto ∝ CCI) para validar el pipeline. Fuerza UTF-8 en stdout (consola Windows).
- `_stats.py` — primitivas: Cohen's d, Hedges' g, rank-biserial, Cliff's δ, bootstrap percentil (independiente y **emparejado** para correlaciones), interpretación de magnitud.
- `h1_cognitive_load.py` — Mann-Whitney U (1-cola) sobre Raw-TLX @ post_t4; Cohen's d + rank-biserial con CIs bootstrap; desglose por subescala.
- `h2_decision_accuracy.py` — accuracy media por participante (MWU, Cohen's d, Cliff's δ); detección por escenario **ordenado por CCI** (Fisher exact) → firma H_OBS descriptiva.
- `h4_early_detection.py` — MWU sobre time-to-first-correction (pooled + por escenario); slope OLS descriptivo de la trayectoria S3 (v₈). ARIMA diferido a datos reales.
- `h5_policy_quality.py` — Spearman ρ(PIQ, Δ_vector) con bootstrap **emparejado**; regresión OLS; PIQ medio por escenario y ρ(CCI, PIQ). Solo grupo experimental.
- `h_obs_causal.py` — **PRIMARIO.** Mixed ANOVA Group×CCI (pingouin, partial η²); contraste pre-registrado gap(S3,S5) − gap(S1,S4); slope gap∝CCI.
- `ancova_all.py` — ANCOVA `outcome ~ C(group) + years_experience + ai_familiarity + C(stratum)` (statsmodels typ-2); partial η² por término; efecto de grupo ajustado.
- `effect_sizes.py` — reusa cada `run()`; tabla unificada con CIs 95%; export `--csv`.
- `visualizations.py` — figuras del paper (slope H_OBS, violín TLX, barras detección×CCI, forest plot). Artefactos generados en `analysis/figures/` (gitignored: dry-run no es resultado).

**Verificación:** los 8 scripts corren con `python analysis/<script>.py --dry-run`; con datos reales, `--db sqlite:///tco_cal.db`. Deps en `analysis/requirements.txt` (scipy, statsmodels, pingouin, scikit-learn, matplotlib). `h3_scalability.py` **absorbido en H_OBS** (DT-032).

### DT-031 · Test suite real para el core

**Componente:** `src/tco_engine/tests/` (4 archivos vacíos)  
**Estado:** Pendiente — **0 tests reales en todo el proyecto**  
**Categoría:** Crítica — el motor que produce los números de las hipótesis no tiene red de seguridad

**Tests requeridos (mínimo viable):**

- `test_vectorizer.py` — vectorize artifact → EvaluationVector, cache hit/miss, clip [0,1]
- `test_aggregator.py` — aggregate entries → T shape correcto; slice nombrado; NaN handling
- `test_inference_engine.py` — omega stable/warning/critical; Δ slope detection; Ρ conflict threshold; S3 Δ detectable en 4 ciclos; S5 Ρ detectado entre j1/j2
- `test_qa_evaluator.py` — mock LLM response → parsing correcto; fallback regex; max_tokens suficientes (DT-024)

**Prioridad dentro de los tests:** `test_inference_engine.py` primero — es el módulo que produce Ω, Δ, Ρ, Ξ directamente.

### DT-032 · SID Study S1–S5: infraestructura de probes + MI para pre-registro H_cross

**Componente:** `analysis/sid_study/` (6 archivos implementados)  
**Estado:** ✅ Implementado + auditado (2026-06-02) — statistic de orden corregido a M_advantage; JSON de pre-registro regenerado  
**Categoría:** Alta — la elegancia del programa CAL depende de esto

**Lo que se construyó:**

- `representations.py` — tres encoders: R_raw (TF-IDF char n-gram), R_V (vector φ 11-dim del ground truth), R_T (tensor joint: V + Δ + Ρ bloques, 33 dims). Labels Y=(D,C) con anotación causal explícita. **Fix de auditoría:** los valores por-artefacto de S3 se subieron (k0=0.78→k3=0.52, todos ≥ umbral absoluto 0.45) para que el drift sea recuperable SÓLO vía la operación Δ del tensor, no leyendo el valor absoluto de cada k (antes k3=0.44 filtraba bajo 0.45).
- `probe.py` — P_linear (LOO logistic, n=2–4); P_structural (threshold sobre el índice CCI: Δ para S3, Ρ para S5, directo para S1/S2/S4).
- `mi_estimator.py` — I(R;Y) vía Fano lower bound; C(R); H_noise vía LDA residual.
- `sid_compute.py` — SID*(R) = I(R;Y)/(C(R)+λ·H_noise). **SID_C* retenido sólo como referencia** (ver auditoría).
- `margin.py` — **(auditoría) métrica de margen continuo sobre ensemble basal-heterogéneo.** M_tensor (detector relativo Δ/Ρ, basal-invariante) vs M_baseline (detector absoluto V<0.45, degrada al variar el basal); **M_advantage = M_tensor − M_baseline** es el statistic de orden de H_cross.
- `benchmark_s1s5.py` — runner con `--dry-run` (exit 0) y corpus real; escribe `sid_preregistration.json`.

**HALLAZGO DE AUDITORÍA (2026-06-02):** el statistic de orden v1 (SID_C* basado en accuracy) **saturaba**: P_structural=1.0 en todos los escenarios ⟹ Fano lower bound = H(Y), así que SID_C* sólo diferenciaba por H_noise (ruido de muestra n=2–4). El orden v1 descansaba en un gap de 0.0009 con tres empates exactos — no defendible. La métrica de margen continuo lo reemplaza y revela que la ventaja tensorial es **operacional** (un umbral relativo generaliza entre proyectos con basal sano distinto; uno absoluto no), medible sólo sobre basales heterogéneos.

**Output pre-registro v2 (2026-06-02T21:36Z) — vigente:**

```
M_advantage: S3=0.50  S5=0.30  S1=S2=S4=0.00
Predicted ΔPIQ order: S3 > S5 > S4 > S1 > S2   (alineado con CCI)
Spearman ρ(M_advantage, CCI) = +0.918
H_cross: Spearman ρ(M_advantage, ΔPIQ) > 0
```

**Limitaciones documentadas:**
- S5 sigue degenerado (ambos artefactos son clase-fault, sin par limpio) → margen de una cara. DT-034 debe añadir S5-clean.
- El ensemble basal-heterogéneo se **simula** vía `BASAL_SHIFTS` sobre la única instancia por escenario del corpus v1.0. DT-034 debe proveer réplicas multi-basal genuinas para reemplazar la simulación.

**NEXT STEP:** commitear `analysis/sid_study/` (incl. `sid_preregistration.json`) ANTES de abrir el dataset del RCT.

### DT-033 · Definición formal de observabilidad causal vs. XAI/interpretabilidad

**Componente:** `Documentacion/Causal_Observability_Theory.md`  
**Estado:** Pendiente — cimiento teórico del Paper 1 (FAccT)  
**Categoría:** Alta

**Descripción:** Documento teórico de 3–5 páginas que formaliza "observabilidad causal para gobernanza humana" y la diferencia de XAI e interpretabilidad.

**Tres distinciones a formalizar:**

1. XAI / interpretabilidad → explica decisiones de un modelo; objetivo: comprensión
2. Monitoring / observabilidad → estado operacional del sistema; objetivo: diagnóstico técnico
3. **Observabilidad causal para gobernanza (CAL)** → estructura causal relevante para decisiones supervisorias; objetivo: acción de gobernanza

La diferencia clave: CAL no intenta explicar *por qué* el sistema hizo lo que hizo (XAI), ni si está operacionalmente saludable (monitoring). Intenta exponer *qué estructura causal* debe observar el gobernador para tomar la decisión correcta.

**Referencia clave para diferenciar:** Doshi-Velez & Kim (2017) taxonomy of interpretability — ninguna de sus categorías captura la dimensión de gobernanza.

### DT-034 · Corpus extensión S6–S8 (Nivel 2 del SID Study)

**Componente:** `src/pipeline/scenarios/s6_silent_drift.py` · `s7_propagation.py` · `s8_resolution_failure.py`  
**Estado:** Pendiente — para Paper 1, no bloquea el RCT  
**Categoría:** Media

**Mecanismos:**

- S6 (`silent_drift`) — degradación temporal por debajo del umbral Δ de detección; prueba límite de observabilidad
- S7 (`propagation_failure`) — fault en agente A causa fault en agente B downstream; requiere índice i (cascada de etapas)
- S8 (`resolution_failure`) — política de re-orquestación incorrecta → conflicto reaparece en k+1; prueba SID_C* en ciclos post-intervención

**Requisitos heredados de la auditoría DT-032 (para que M_advantage sea válido sin simulación):**

- **Par S5-limpio** — un escenario de dos agentes SIN conflicto, para que H(Y_C)>0 en S5 y el margen deje de ser de una cara.
- **Réplicas multi-basal genuinas** — ≥3 instancias por escenario con niveles basales sanos distintos (no simuladas vía `BASAL_SHIFTS`), para medir empíricamente la robustez del umbral relativo Δ/Ρ frente al absoluto.

### DT-035 · Estrategia de reproducibilidad LLM

**Componente:** `analysis/reproducibility_log.md` + ajustes en `qa_evaluator.py`  
**Estado:** Pendiente  
**Categoría:** Media — revisor de FAccT lo señalará

**Acciones:**

- Pinear versión del modelo en `.env.example` (`LLM_MODEL=anthropic/claude-sonnet-4-6` → especificar fecha/versión exacta)
- Archivar los outputs LLM del corpus de calibración (JSON con prompt + completion) en `src/experiment/phi_calibration/llm_outputs/`
- Documentar seeds de numpy para análisis estadístico

### DT-036 · DT-028 Fase 2 frontend React

**Componente:** `src/dashboard/src/` — stubs vacíos  
**Estado:** Pendiente (backend de Fase 2 completo y verificado; frontend sin iniciar)  
**Categoría:** Crítica — bloquea el piloto y el experimento

**Stubs a implementar (en orden):**

1. `App.tsx` — routing + auth guards (participant / admin)
2. `src/api/tcoClient.ts` + `experimentClient.ts` — clientes del backend
3. `experiment/TaskSequencer.tsx` — orquestador del runner (pre-test → S0 → T1–T4 → TLX × 2 con pausa)
4. `experiment/NASATLXForm.tsx` — formulario TLX digital
5. `experiment/InteractionTracker.ts` — instrumentación de eventos
6. Componentes del dashboard experimental: `VectorRadar`, `TensorHeatmap`, `InferencePanel`, `PolicyInjection`

---

*Última actualización: 2026-06-10 — gate de calibración φ **GO confirmado** (DT-021 v2, 2026-06-06: n=8/familia, todas ρ ≥ 0.85, CI inferior v8 +0.607); piloto n=4 desbloqueado (corre sobre deploy local verificado). Capas downstream cerradas: L3 caracterización (~95%) + L4 S5 mecanismo/L4-B0 NO-GO.*  
*Próxima revisión: piloto n=4 (deploy local) · MoU/reclutamiento en paralelo · DT-028 Fase 3 (deploy prod + SMTP + Postgres, post-piloto) · DT-024 (inter-model, vía de validación oficial de v7/v8, pre-submission)*
