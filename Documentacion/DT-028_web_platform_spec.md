# DT-028 — Web Platform Implementation Spec

**Plataforma del experimento TCO-L2 (y base reutilizable para L3/L4)**
URL objetivo: `researchlab.aural-syncro.com.ar/cal`
Versión 1.0 — Mayo 2026

---

## 1. Decisiones de arquitectura (cerradas)

| Decisión | Resolución |
|---|---|
| **Topología** | Servicio TCO propio en `/cal`, desplegado en la red `sspa_infra` detrás de Cloudflare. Reutiliza Postgres/Timescale y patrón de email SMTP de Research Lab, con schema y flujo propios. |
| **Frontend** | SPA única React/Vite — reutiliza `ControlGroupViewer` + componentes del dashboard (radar, heatmap, inference, policy) ya existentes. |
| **Registro** | Auto-servicio con user/pass para todos. La ejecución de la prueba la agenda el admin por email. |
| **Auth** | JWT + bcrypt, dos roles: `participant` / `admin`. Patrón tomado de `Research-Lab/app/auth.py`. |
| **Persistencia** | El TCO Engine es dueño de toda la data del experimento (participantes, sesiones, resultados). Tablas `cal_*`. |
| **Cómputo NCF/PIQ** | En el TCO Engine (Python ya implementado: 4 proxies, scoring, φ/f/I, PIQ judge). |

**Discrepancia de dominio a resolver con infra:** Research Lab corre en `researchlab.com.ar`; el path objetivo es `researchlab.aural-syncro.com.ar/cal`. Confirmar en el Cloudflare Tunnel si es el mismo deployment con hostname adicional o un subdominio nuevo apuntando al servicio TCO.

---

## 2. Flujo del participante (extremo a extremo)

```
1. Registro self-service        → datos profesionales + experiencia + consentimiento
                                   → asignación automática de grupo (estratificada)
                                   → email de bienvenida (confirma cuenta)
2. Espera                        → el admin agenda la fecha de la prueba
3. Invitación                    → email con fecha/hora + link de login
4. Día de la prueba              → login user/pass → runner del experimento
                                   (Fase 1–5 del pilot_protocol.md)
5. Post-prueba                   → resultados de debriefing visibles en /cal/results
                                   → email "resultados disponibles"
```

El **admin** controla: ver registrados, ver/ajustar grupos, ver completitud, ver resultados parciales y totales, agendar e invitar, exportar.

---

## 3. Modelo de datos — tablas `cal_*`

Nuevas tablas en la DB del TCO Engine (`src/tco_engine/db/models.py`). Migración inline al estilo Research Lab (`CREATE TABLE IF NOT EXISTS`).

### `cal_participants`
| Campo | Tipo | Nota |
|---|---|---|
| id | UUID PK | |
| email | varchar unique | login |
| hashed_password | varchar | bcrypt |
| role | enum(participant, admin) | |
| name | varchar | |
| country | varchar | |
| years_experience | int | code review ≥ 2 |
| education_level | enum(undergraduate, graduate, other) | |
| institution | varchar null | |
| languages | varchar | ecosistemas principales |
| ai_familiarity | int 0–4 | covariable ANCOVA |
| prior_tco_exposure | bool | disqualifier si true |
| experience_stratum | enum(junior, mid, senior) | derivado de years_experience |
| group | enum(control, experimental) null | asignación estratificada |
| consent_at | timestamptz null | |
| created_at | timestamptz | |

### `cal_invitations`
| Campo | Tipo |
|---|---|
| id | UUID PK |
| participant_id | FK → cal_participants |
| scheduled_at | timestamptz |
| token | varchar unique |
| sent_at | timestamptz null |
| status | enum(scheduled, sent, expired) |

### `cal_sessions`
| Campo | Tipo | Nota |
|---|---|---|
| id | UUID PK | |
| participant_id | FK | |
| status | enum(invited, in_progress, completed, aborted) | |
| current_phase | varchar | registro/desacople/.../debriefing |
| started_at | timestamptz null | |
| completed_at | timestamptz null | |
| is_pilot | bool | excluye del análisis final |

### `cal_task_results`
| Campo | Tipo | Nota |
|---|---|---|
| id | UUID PK | |
| session_id | FK | |
| task | enum(T1, T2, T3, T4) | |
| scenario | enum(S1..S5) | |
| accuracy | float | de accuracy_scorer.py |
| detected | bool | fault detectado sí/no |
| time_to_first_correction_s | float null | |
| raw_response | jsonb | corrección/decisión cruda |

### `cal_tlx_measurements`
| Campo | Tipo |
|---|---|
| id | UUID PK |
| session_id | FK |
| checkpoint | enum(post_t2, post_t4) |
| mental_demand, physical_demand, temporal_demand, performance, effort, frustration | int 0–100 |

### `cal_ncf_proxies`
| Campo | Tipo |
|---|---|
| id | UUID PK |
| session_id | FK |
| working_memory_saturation | float null |
| mean_sigma_severity | float null |
| sigma_accuracy | float null |
| iqr_attention_fragmentation_s | float null |
| ncf_at_frontier | bool null |

### `cal_policy_intents` (grupo experimental)
| Campo | Tipo |
|---|---|
| id | UUID PK |
| session_id | FK |
| scenario | enum(S1..S5) |
| raw_policy | text |
| piq_d1..d5 | int 0–2 |
| piq_score | float |

### `cal_interaction_events`
| Campo | Tipo | Nota |
|---|---|---|
| id | UUID PK | |
| session_id | FK | |
| ts | timestamptz | feed para interaction_timer.py |
| event_type | varchar | view/click/correction/policy_submit |
| artifact_id | varchar null | |

---

## 4. API — TCO Engine FastAPI

Prefijo `/cal/api`. Wire de la lógica core ya implementada.

### Auth
| Método | Ruta | Función |
|---|---|---|
| POST | `/cal/api/auth/register` | Alta self-service + randomización + email bienvenida |
| POST | `/cal/api/auth/login` | user/pass → JWT |
| POST | `/cal/api/auth/consent` | Registrar consentimiento informado (DT-014) |
| GET | `/cal/api/me` | Perfil + grupo + estado de sesión |

### Participante (runner)
| Método | Ruta | Función |
|---|---|---|
| GET | `/cal/api/session/current` | Sesión invitada/activa del participante |
| POST | `/cal/api/session/start` | Inicia sesión (registra started_at) |
| GET | `/cal/api/session/{id}/scenario/{k}` | Artefactos del escenario (control o experimental) |
| POST | `/cal/api/session/{id}/correction` | Log de corrección → cal_task_results + cal_interaction_events |
| POST | `/cal/api/session/{id}/tlx` | NASA-TLX (post_t2 / post_t4) |
| POST | `/cal/api/session/{id}/policy` | Inyección de política (experimental) → PIQ scoring |
| POST | `/cal/api/session/{id}/complete` | Cierra sesión, dispara cómputo NCF + email resultados |

### Cómputo TCO (interno, alimenta el dashboard experimental)
| Método | Ruta | Función |
|---|---|---|
| POST | `/cal/api/vector/compute` | φ: A → V (vectorizer.py) |
| GET | `/cal/api/tensor/current` | T[:,:,:,k] (aggregator.py) |
| GET | `/cal/api/inference/latest` | I: T → {Ω,Δ,Ρ,Ξ} (inference_engine.py) |

### Admin
| Método | Ruta | Función |
|---|---|---|
| GET | `/cal/api/admin/participants` | Listado + grupo + estado de completitud |
| POST | `/cal/api/admin/participant/{id}/group` | Override de asignación de grupo |
| POST | `/cal/api/admin/invite` | Agenda fecha + envía email de invitación |
| GET | `/cal/api/admin/results` | Resultados parciales/totales (accuracy, NCF, TLX, PIQ) |
| GET | `/cal/api/admin/export` | CSV/JSON anonimizado (exporter.py + anonymizer.py) |

---

## 5. Frontend — React SPA (`src/dashboard/`)

### Rutas
| Ruta | Vista | Acceso |
|---|---|---|
| `/cal` | Landing — pre-print, H1–H5, CTA registro | público |
| `/cal/register` | Formulario de registro (datos profesionales + experiencia + consentimiento) | público |
| `/cal/login` | Login user/pass | público |
| `/cal/dashboard` | Estado del participante ("tu sesión está agendada para…") | participant |
| `/cal/session/run` | **Runner del experimento** (TaskSequencer) | participant |
| `/cal/results` | Debriefing — accuracy, faults, TLX (Fase 5 pilot_protocol) | participant |
| `/cal/admin` | Dashboard admin | admin |

### Runner (`TaskSequencer.tsx`) — orquesta el pilot_protocol
```
Pre-test técnico → Warm-up S0 → T1 → T2 → NASA-TLX#1 → [pausa] → T3 → T4 → NASA-TLX#2 → fin
```
- **Control** → `ControlGroupViewer.tsx` (✅ existe)
- **Experimental** → ensambla `VectorRadar` + `TensorHeatmap` + `InferencePanel` + `PolicyInjection` (✅ existen)
- `InteractionTracker.ts` instrumenta todos los eventos → `/cal/api/session/{id}/correction` y `cal_interaction_events`
- `NASATLXForm.tsx` → `/cal/api/session/{id}/tlx`

### Admin dashboard (`/cal/admin`)
- Tabla de participantes: nombre, grupo, estrato, estado (registrado/invitado/en curso/completado)
- Acción: agendar fecha + invitar
- Acción: override de grupo
- Panel de resultados: accuracy por tarea/grupo, NCF at frontier, distribución TLX, PIQ — parciales y totales
- Botón export CSV/JSON

---

## 6. Asignación de grupo — randomización estratificada

Al registrarse:
1. `experience_stratum` = junior (2–4) · mid (5–9) · senior (10+)
2. Dentro del estrato, asignar al grupo con menos miembros (balance), desempate aleatorio
3. Persistir `group`. El admin puede sobreescribir desde `/cal/admin`.

Esto preserva el balance estratificado del `participant_session_protocol.md` (Junior 10/10 · Mid 8/8 · Senior 2/2 para n=40) y funciona también para n=4.

---

## 7. Flujo de emails (reusa patrón SMTP de Research Lab)

| Email | Disparador | Contenido |
|---|---|---|
| Bienvenida | POST register exitoso | Confirma cuenta + "te invitaremos a una fecha de sesión" |
| Invitación | Admin agenda fecha | Fecha/hora + link de login + instrucciones técnicas |
| Recordatorio (opcional) | 24h antes | Recordatorio de sesión |
| Resultados | session/complete | "Tus resultados están disponibles en /cal/results" |

Plantillas HTML+plain al estilo `Research-Lab/app/routers/register.py`.

---

## 8. Plan de construcción (3 fases, ~3 semanas)

> Reordenamiento del roadmap: DT-028 se construye **antes** del piloto. Semana 5–7 build plataforma → Semana 7 piloto n=4 → Semana 8 calibración → Semana 9–10 experimento.

### Fase 1 — Backend foundation (Semana 5) ✅ COMPLETA (2026-05-31)
- [x] Schema `cal_*` en `db/models.py` + `db/database.py` (layer-aware: sesiones con campo `layer` L2/L3/L4) — create_all en startup
- [x] Auth: register/login/JWT + roles (participant/admin) — `core/auth.py` (bcrypt directo, no passlib)
- [x] Randomización estratificada en el alta — `core/randomization.py`
- [x] API routes: `vector` (φ), `tensor` (aggregate), `inference` (Ω/Δ/Ρ/Ξ) wired al core; `policy` stub 501 (Fase 2)
- [x] Email de bienvenida + invitación — `core/email_service.py` (best-effort)
- [x] Rutas `/cal/api`: register, login, consent, me, admin/participants, admin/invite, admin/group-override — `api/routes/experiment.py`
- [x] **Fix raíz de paquete:** todo alineado a `tco_engine.*` (main.py, Dockerfile context `./src`, docker-compose)
- [x] Smoke test verificado: register→login→me→consent, balance estratificado, guard admin 403, tensor/inference/policy

**Pendiente de Fase 1 (no bloqueante):** seed de usuario admin (actualmente se promueve a mano vía DB). Agregar comando CLI de bootstrap admin al inicio de Fase 2.

### Fase 2 — Experiment runner (Semana 6)
- [ ] Shell React + routing + guardas de auth
- [ ] `TaskSequencer` (pre-test → S0 → T1–T4 → TLX + pausa)
- [ ] Wire `ControlGroupViewer` (control) + ensamble dashboard (experimental)
- [ ] `InteractionTracker` + correction logging + `NASATLXForm` → backend
- [ ] Endpoints de ciclo de vida de sesión

### Fase 3 — Admin + resultados + ops (Semana 7)
- [ ] Dashboard admin (listado, grupos, completitud, resultados)
- [ ] Agendado de invitación + email
- [ ] Vista de debriefing `/cal/results`
- [ ] `exporter.py` + `anonymizer.py` (CSV/JSON anonimizado)
- [ ] `integrity_checker.py` pre-sesión (DT-013)
- [ ] Docker Compose + routing Cloudflare `/cal` + deploy

Tras Fase 3 → **piloto n=4** (`protocols/pilot_protocol.md`).

---

## 9. Stubs a completar (mapeo directo)

| Archivo | Fase | Rol |
|---|---|---|
| `src/tco_engine/api/routes/vector.py` | 1 | φ endpoint |
| `src/tco_engine/api/routes/tensor.py` | 1 | tensor snapshot |
| `src/tco_engine/api/routes/inference.py` | 1 | {Ω,Δ,Ρ,Ξ} |
| `src/tco_engine/api/routes/policy.py` | 2 | policy inject + PIQ |
| `src/tco_engine/api/routes/experiment.py` | 1–3 | auth, sesión, admin (cal/api) |
| `src/dashboard/src/App.tsx` | 2 | routing SPA |
| `src/dashboard/src/api/tcoClient.ts` | 1–2 | cliente vector/tensor/inference |
| `src/dashboard/src/api/experimentClient.ts` | 2 | cliente sesión/auth/admin |
| `src/dashboard/src/experiment/TaskSequencer.tsx` | 2 | orquestador del runner |
| `src/dashboard/src/experiment/NASATLXForm.tsx` | 2 | formulario TLX |
| `src/dashboard/src/experiment/InteractionTracker.ts` | 2 | instrumentación |
| `src/experiment/data_pipeline/exporter.py` | 3 | export CSV/JSON |
| `src/experiment/data_pipeline/anonymizer.py` | 3 | pseudonimización |
| `src/experiment/data_pipeline/integrity_checker.py` | 3 | validación pre-sesión |

---

## 10. Reutilización para L3/L4

`cal_participants`, auth, email service y el `TaskSequencer` son agnósticos al layer. Para L3:
1. Nuevos escenarios L3 (tensor volumes, cross-session)
2. Nueva vista de presentación (otra abstracción) bajo `/cal/l3`
3. Reusar registro, randomización, persistencia y admin sin cambios
