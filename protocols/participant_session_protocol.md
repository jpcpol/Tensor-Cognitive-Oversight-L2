# Participant Session Protocol — TCO Experiment

Version 1.0 — April 2026

---

## 1. Recruitment Strategy

**Target:** n=40 software engineers, ≥2 years code review experience, no prior TCO exposure.

**Recruitment mix (decided):**

- **n=20 online channels:**
  - Reddit: r/softwareengineering, r/experimentation, r/MachineLearning
  - Discord: LangChain community, Python Argentina, Async Python
  - LinkedIn: posts targeting SE professionals in LATAM / global
  - Dev.to / HackerNews "Who's looking for research participants" threads

- **n=20 local/direct:**
  - University contacts (UBA, UTN, or equivalent)
  - Local tech company HR contacts (voluntary, no commercial interest)
  - SE Meetup groups in Buenos Aires

**Pre-screening form (3-question filter, online):**

1. How many years of code review experience do you have? (Threshold: ≥2)
2. Have you heard of or used Tensor-Based Cognitive Oversight (TCO)? (Disqualifier: Yes)
3. Are you available for a 3-hour remote session in the next 4 weeks? (Threshold: Yes)

**Full registration form (collected after pre-screening passes):**

- Name, email, country
- Years of code review experience
- Education level (undergraduate / graduate / other) + institution (optional)
- Primary languages / ecosystems
- AI tool familiarity in daily development work (0–4 scale): 0=never · 1=rarely · 2=monthly · 3=weekly · 4=daily — *ANCOVA covariate, not used for group assignment*
- Prior TCO exposure (re-confirmed)
- Informed consent (DT-014)
- Session availability

**Incentive:** Non-monetary. Participants receive early access to the published results and are acknowledged in the paper's acknowledgments section (optional).

**Stratification:** Participants are assigned to groups in pairs, stratified by years of experience:

- Junior (2–4 years): 10 per group
- Mid (5–9 years): 8 per group
- Senior (10+ years): 2 per group

---

## 2. Session Protocol (per participant)

**Total duration:** ~2h45min  
**Format:** Remote (video call + screen share) or in-person lab

| Phase | Duration | Activity |
| ----- | -------- | -------- |
| Pre-session | 10 min | Technical pre-test (10 code review questions) |
| Orientation | 30 min | Environment setup + interface training |
| Warm-up | 15 min | Practice task (warm-up pipeline, no faults) |
| Experimental block | 90 min | T1 (25m) · T2 (20m) · T3 (15m) · T4 (30m) |
| Raw-TLX #1 | 5 min | Post-T2 cognitive load measurement |
| Raw-TLX #2 | 5 min | Post-T4 cognitive load measurement |
| Interview | 15 min | Semi-structured, recorded with consent |

**Timer policy:** Each task has a visible countdown. Automatic close at time limit.
Partial responses are captured and scored with available data (not excluded).

---

## 2b. Warm-up Pipeline — S0 (Notification Service)

**Scenario:** `S0 — Notification Service` (`src/pipeline/scenarios/s0_warmup.py`)  
**Duration:** 15 min — no timer pressure, no scoring  
**Purpose:** interface familiarization only. Results are NOT included in analysis.

### What S0 contains

A healthy async notification dispatcher (Python + Docker Compose YAML).  
Domain deliberately distinct from S1–S5 (auth / arch / deploy / debt / conflict).  
No faults injected. All quality dimensions ∈ [0.75, 0.92].

### Facilitator script — Experimental group (TCO Dashboard)

> "You'll see a radar chart with 11 quality dimensions, a system state indicator
> (Omega showing stable/warning/critical), and a trend panel. This pipeline has
> no injected faults — everything should look healthy. Explore the interface
> freely. If you want, write something in the policy injection box. There are
> no wrong answers here — this is just practice."

After 10 min:
> "Any questions about the interface? Anything unclear or unexpected?"

### Facilitator script — Control group (ControlGroupViewer)

> "You'll see the source code and configuration for a notification service.
> Review it and note any observations in the correction form. This pipeline
> is clean — there are no injected faults. Explore freely."

After 10 min:
> "Any questions? Anything about the interface you'd like clarified?"

### Transition to experimental block (both groups)

> "Good. The next 5 scenarios follow the same structure, but each has a real
> quality issue injected. You'll have a visible timer for each task. Let's begin."

### What NOT to say during warm-up

- Do not hint that S1 involves security, S3 involves debt accumulation, etc.
- Do not explain what Omega=warning looks like — let participants discover it.
- Do not correct participant assessments — warm-up is practice, not evaluation.

---

## 3. Environment Setup Checklist

Before each session:

- [ ] integrity_checker.py passes all validations (S3 pre-loaded, scenarios verified)
- [ ] Participant_id generated and confirmed as new (no prior sessions)
- [ ] Group assignment confirmed (control or experimental)
- [ ] Interface loaded and tested (ControlGroupViewer OR TCO Dashboard)
- [ ] Interaction logger active (confirmed with test click)
- [ ] Screen recording running (with participant consent)
- [ ] Consent form signed

---

## 4. Interview Guide (15 min, semi-structured)

1. How would you describe the experience of using this interface?
2. Was there any moment where you felt uncertain about what to do?
3. How confident were you in the corrections/policies you submitted?
4. Would you use this type of interface in your daily work? Why or why not?
5. Is there anything the interface showed (or didn't show) that would have been helpful?

---

## 5. Data Handling

- All participant identifiers are pseudonymous (P001, P002, ...) — never store real names in the DB
- Session recordings stored locally, not uploaded
- Anonymized data export for Open Science deposit after experiment completion
- Right to withdraw: participant may exit at any point; their data is deleted from the DB on request
