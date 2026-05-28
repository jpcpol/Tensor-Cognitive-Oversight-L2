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
| DT-024 | Paper — Evaluator variance y rigor LLM-QA | Importante | Pendiente |
| DT-025 | Paper — Reencuadrar vector como "~orthogonal supervisory dims" | Importante | Implementado |
| DT-026 | Experimento — 4 proxies NCF operacionalizados en infra | Importante | Implementado |
| DT-027 | Paper — Reencuadre sistemático "supervisory estimators" | Importante | Pendiente |

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

*Última actualización: 20 Mayo 2026*  
*Próxima revisión: al completar Semana 3 (pipeline LangGraph + validación φ en corpus)*
