# Pilot Protocol — TCO Experiment (n=4)

Version 1.0 — May 2026

---

## 1. Objetivo y alcance

El piloto valida el protocolo experimental antes del experimento completo (n=40).  
Los datos del piloto **no se incluyen en el análisis final** ni en el paper.

**Participantes:** n=4 internos/conocidos, ≥2 años de experiencia en code review, sin exposición previa a TCO.  
**Asignación de grupos:** 2 control (ControlGroupViewer) + 2 experimental (TCO Dashboard).

**Lo que el piloto valida:**

| Ítem | Criterio go |
|---|---|
| Timing de sesión completo | Total ≤ 3h30m |
| Instrumentos de datos funcionando | NCF proxies + NASA-TLX registran sin errores |
| Scripts del facilitador claros | Sin confusión sistemática (>1 participante) en la misma fase |
| Desacople efectivo | Participante entra a la prueba sin estado predispuesto (auto-reporte, ítem en debriefing) |
| Datos técnicos limpios | integrity_checker.py pasa antes de cada sesión |
| Briefing no introduce sesgo | Ningún participante menciona intuir la hipótesis antes del experimento |

---

## 2. Pipeline de sesión

**Duración estimada total:** ~3h10m  
**Formato:** Remoto (video call + screen share) o presencial.

```
Fase 1 — Registro            (~15 min)
Fase 2 — Desacople inicial   (~10 min)
Fase 3 — Explicación         (~20 min)
Fase 4 — Prueba              (~2h20m)
Fase 5 — Debriefing          (~20 min)
─────────────────────────────────────
TOTAL estimado:               ~3h05m
```

---

## 3. Fase 1 — Registro (~15 min)

**Objetivo:** Recolectar datos del participante y verificar elegibilidad.

### Datos a recolectar

| Campo | Instrumento |
|---|---|
| Nombre completo (sólo para facilitador, no entra a DB) | Formulario papel o Google Form |
| Email (para envío de resultados post-piloto) | Ídem |
| Años de experiencia en code review | Pre-screening filter Q1 |
| Stack tecnológico principal (lenguaje / ecosistema) | Contexto para análisis cualitativo |
| Familiaridad con herramientas de IA (0–4) | 0=nunca · 1=raramente · 2=mensual · 3=semanal · 4=diario — covariable ANCOVA |
| Exposición previa a TCO o herramientas similares | Pre-screening filter Q2 — disqualifier |
| Disponibilidad de pantalla completa + audio | Checklist técnico |

### Script del facilitador

> "Antes de empezar voy a pedirte unos datos básicos. Nada de esto identifica tu
> performance — sólo necesitamos confirmar tu perfil y tener cómo contactarte
> al final del estudio."

Si el participante no cumple el mínimo (< 2 años code review, o conoce TCO):
> "En este caso tu perfil no coincide con el grupo objetivo del estudio. Muchas
> gracias de todas formas por tu tiempo."

### Checklist técnico (facilitador)

- [ ] integrity_checker.py pasa todos los escenarios
- [ ] Participant_id generado (P_PILOT_01 a P_PILOT_04)
- [ ] Grupo asignado y confirmado (control / experimental)
- [ ] Interface cargada y probada con test-click
- [ ] Interaction logger activo
- [ ] Screen recording listo (solicitar consentimiento verbal)
- [ ] Timer visible configurado por tarea

---

## 4. Fase 2 — Desacople inicial (~10 min)

**Objetivo:** Borrar el estado de trabajo previo del participante y evitar que entre a la prueba con sesgos activos (estrés, modo coding reciente, anticipación de lo que va a ver).

**Método:** Tarea distractora neutral — puzzle de razonamiento espacial.

### Instrucciones para el participante

> "Antes de arrancar, vamos a hacer una actividad de calentamiento mental que
> no tiene nada que ver con el estudio. No hay respuestas correctas ni
> incorrectas — es sólo para que llegues a la sesión con la cabeza despejada.
> Tenés 8 minutos."

### Tarea distractora estándar (5 ítems, ~8 min)

Presentar en pantalla una secuencia de 5 puzzles de razonamiento espacial no verbal:
- Rotaciones de figuras geométricas (ej. Raven's Progressive Matrices style, nivel fácil-medio)
- Sin referencias a código, software, ni IA
- El facilitador NO comenta ni da feedback durante los 8 min

Fuente recomendada: puzzles en papel o PDF — NO usar herramientas online para evitar distracción de navegación.

### Cierre del desacople

Al terminar los 8 min:
> "Perfecto. ¿Cómo te sentís? ¿Hay algo que quieras antes de seguir?"

Esperar respuesta. Si el participante menciona tensión, dar 2 min adicionales de pausa.

### Ítem de validación (para el informe del piloto)

Al final del debriefing (Fase 5), pregunta específica:
> "¿Sentiste que la actividad inicial te ayudó a entrar a la sesión más despejado,
> o no notaste diferencia?"

---

## 5. Fase 3 — Explicación (~20 min)

**Objetivo:** Orientar al participante sobre la sesión sin revelar la hipótesis del estudio.

> **Single-blind:** el participante NO sabe que está en un estudio sobre carga cognitiva
> ni que hay un grupo de comparación. Se le explica que está ayudando a evaluar
> una herramienta de supervisión de pipelines de IA. El propósito completo
> se revela en el debriefing (Fase 5).

### Script de briefing (leer textual)

> "Este estudio investiga cómo los ingenieros de software supervisan y corrigen
> outputs generados por pipelines de IA. Vas a ver outputs de un sistema de
> generación de código — código, configuraciones, logs — y tu trabajo es
> identificar problemas y hacer correcciones.
>
> Vas a trabajar con [esta interfaz / este entorno] durante aproximadamente
> dos horas. Hay 5 escenarios, cada uno con un tiempo visible. Si no terminás
> en el tiempo, el sistema captura lo que hayas hecho hasta ese momento —
> no hay penalidad por no terminar.
>
> No hay respuestas correctas en el sentido de 'sabemos lo que vas a decir'.
> Lo que nos interesa es cómo tomás decisiones, no si acertás o no.
> Vas a completar dos cuestionarios cortos durante la sesión.
>
> ¿Alguna pregunta antes de empezar?"

### Consentimiento

Leer en voz alta:
> "Esta sesión va a ser grabada sólo para revisión interna. Los datos se pseudonimizan
> y no se publican con tu nombre. Podés detener la sesión en cualquier momento
> y tus datos se eliminan si lo pedís. ¿Das tu consentimiento para continuar?"

Registrar consentimiento verbal (o firma en formulario físico si es presencial).

### Setup técnico (~5 min)

- Verificar que el participante puede ver su pantalla + la interfaz
- Hacer un test-click / test de interacción con el logger
- Confirmar que el timer es visible
- Confirmar audio bidireccional (remoto)

---

## 6. Fase 4 — Prueba (~2h15m)

Ejecutar el protocolo estándar de sesión definido en `participant_session_protocol.md`, secciones 2 y 2b.

```
Pre-test técnico     10 min   (10 preguntas de code review)
Warm-up S0           15 min   (s0_warmup.py — sin faults, sin scoring)
── Bloque A ─────────────────────────────────────────────
T1                   25 min
T2                   20 min
NASA Raw-TLX #1       5 min   Post-T2
── PAUSA ACTIVA ──   10 min   entre escenarios — no afecta datos
── Bloque B ─────────────────────────────────────────────
T3                   15 min
T4                   30 min
NASA Raw-TLX #2       5 min   Post-T4
─────────────────────────────────────────────────────────
TOTAL Fase 4:        ~2h15m
```

**Sobre la pausa activa:**  
Cae después de NASA-TLX #1 — la medición post-T2 ya está capturada, por lo que la pausa no contamina ningún dato. T2 (architectural alignment) y T3 (technical debt) son escenarios independientes.

Script del facilitador para la pausa:
> "Tomamos 10 minutos. Podés levantarte, tomar agua. No hay nada que
> preparar — cuando retomemos arrancamos directamente con la siguiente tarea."

**Validación en el piloto:** ítem en el debriefing (Fase 5):
> "¿La pausa fue suficiente, larga, o corta?"  
> → Ajustar duración antes de n=40 según respuestas del piloto.

### Registro adicional para el piloto (facilitador)

Durante la prueba, el facilitador anota en tiempo real:

| Momento | Qué registrar |
|---|---|
| Cada vez que el participante hace una pausa larga (>30s sin acción) | Timestamp + fase + contexto |
| Preguntas del participante | Texto exacto + fase |
| Confusión visible con la interfaz | Qué elemento + cuánto tiempo duró |
| Problemas técnicos | Tipo + duración + resolución |
| Timing real por tarea | Comparar con los timers del sistema |

Usar la planilla: `protocols/pilot_facilitator_log_template.md` (ver sección 9).

---

## 7. Fase 5 — Debriefing individual (~20 min)

**Objetivo:** Informar al participante sus resultados individuales y obtener feedback cualitativo sobre el protocolo.

> **Aquí se rompe el single-blind.** El participante recibe:
> - El propósito real del estudio
> - A qué grupo perteneció (control / experimental)
> - Sus resultados de detección por tarea (accuracy)
> - Sus scores NASA-TLX
> - Una explicación de qué faults había en cada escenario

### Script de apertura del debriefing

> "Gracias. Voy a contarte ahora de qué se trató realmente este estudio.
>
> Estamos investigando si una representación abstracta de los outputs de
> pipelines de IA — un tensor cognitivo — reduce la carga mental y mejora
> la calidad de supervisión comparado con revisar los artefactos directamente.
>
> Vos usaste [la interfaz TCO / el entorno de código directo]. Hay un grupo
> de comparación que usa el otro enfoque.
>
> Ahora te muestro cómo te fue."

### Resultados a mostrar al participante

| Dato | Fuente | Formato |
|---|---|---|
| Accuracy por tarea (T1–T4) | `accuracy_scorer.py` | Tabla simple: ✓/✗ por escenario |
| Faults que había en cada escenario | `GROUND_TRUTH` de cada scenario file | Descripción en lenguaje natural |
| NASA-TLX scores (mental demand, frustration, etc.) | `nasa_tlx_form.py` | 6 barras horizontales |
| Tiempo por tarea vs. tiempo del grupo (si aplica) | `interaction_timer.py` | Comparativo simple |

### Preguntas de feedback del protocolo (específicas del piloto)

1. ¿El desacople inicial te pareció útil, innecesario, o molesto?
2. ¿Las instrucciones antes de la prueba fueron claras? ¿Algo te quedó poco claro?
3. ¿El tiempo por tarea te pareció suficiente, justo, o escaso?
4. ¿El cuestionario NASA-TLX fue fácil de completar o confuso?
5. ¿Algo de la interfaz te generó confusión que no pudiste resolver solo?
6. ¿Hay algo que te hubiera ayudado saber antes de empezar?

Registrar respuestas textuales en `protocols/pilot_facilitator_log_template.md`.

---

## 8. Criterios go/no-go

El piloto se considera exitoso si **todos** los siguientes criterios se cumplen:

| Criterio | Umbral | Evaluado en |
|---|---|---|
| Timing total | ≤ 3h30m por sesión | Log del facilitador |
| Instrumentos de datos | 0 errores de recolección en los 4 participantes | NCF proxy output |
| Ambigüedad de instrucciones | ≤ 1 participante reporta confusión en la misma fase | Debriefing Q2 |
| Desacople efectivo | ≥ 3/4 reportan que ayudó o fue neutral | Debriefing Q1 |
| Problemas técnicos críticos | 0 sesiones abortadas por fallo técnico | Log del facilitador |
| Sesgo por briefing | 0 participantes mencionan intuir la hipótesis antes del debriefing | Notas del facilitador |

Si algún criterio falla → ajustar protocolo → re-correr las sesiones afectadas antes de n=40.

---

## 9. Planilla del facilitador (por sesión)

Crear un archivo por sesión: `protocols/pilot_logs/P_PILOT_0X_log.md`

```markdown
# Log Facilitador — P_PILOT_0X

Fecha:
Grupo: [control / experimental]
Timing real:
  - Registro:       __min
  - Desacople:      __min
  - Explicación:    __min
  - Pre-test:       __min
  - Warm-up S0:     __min
  - T1:             __min (estimado: 25m)
  - T2:             __min (estimado: 20m)
  - T3:             __min (estimado: 15m)
  - T4:             __min (estimado: 30m)
  - NASA-TLX ×2:    __min
  - Debriefing:     __min
  - TOTAL:          __min

## Observaciones durante la prueba

| Timestamp | Fase | Observación |
|---|---|---|
| | | |

## Respuestas debriefing protocolo

1. Desacople:
2. Instrucciones:
3. Tiempo por tarea:
4. NASA-TLX:
5. Interfaz:
6. Info previa necesaria:

## Issues técnicos

## Notas generales
```

---

## 10. Informe post-piloto

Al completar las 4 sesiones, generar un informe consolidado con:

### Secciones del informe

**A. Timing**  
Tabla de timing real vs. planificado por fase, para los 4 participantes. Identificar fases que se exceden consistentemente.

**B. Datos recolectados**  
Verificación de que todos los instrumentos produjeron output válido:
- `ncf_proxy.py` → NCFProxies para los 4 participantes
- `nasa_tlx_form.py` → 2 mediciones por participante
- `correction_log.py` → entradas por tarea por escenario
- `accuracy_scorer.py` → accuracy T1–T4 por participante
- `interaction_timer.py` → timestamps por artefacto

**C. Issues del protocolo**  
Lista consolidada de confusiones, preguntas, y ambigüedades detectadas, con frecuencia (cuántos participantes las tuvieron) y propuesta de ajuste.

**D. Validación del desacople**  
Distribución de respuestas a debriefing Q1: ¿fue útil / neutral / molesto?

**E. Análisis de timing T1–T4**  
¿Alguna tarea consistentemente se agota el tiempo? → ajuste de timers o instrucciones.

**F. Visualizaciones**  
- Heatmap timing real por fase × participante
- Barras accuracy por tarea × grupo (control vs. experimental) — n=2 c/u, sólo orientativo
- Distribución NASA-TLX por grupo — orientativo

**G. Recomendación go/no-go**  
Checklist de los 6 criterios de la sección 8 con resultado pass/fail y justificación.

### Generación del informe

Script de generación: `analysis/pilot_report.py` (por implementar — DT-029).

Hasta que esté disponible: consolidar manualmente en `protocols/pilot_report_v1.md`.
