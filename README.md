# 🌉 SETU AI (सेतु): Schedule Execution Tracking & Unification Engine

> **Smart India Hackathon (SIH 2026) | Problem ID:** SIH26122  
> **Target Organization:** Oil India Limited (OIL)  
> **Domain:** Smart Infrastructure / Project Management Automation  
> **Asset Focus:** Duliajan Gas Compressor Station & Manifold Expansion  

---

## 📌 Executive Summary

Major upstream oil and gas infrastructure projects face chronic schedule slippage. While central project management offices (PMOs) maintain structured baselines in **Oracle Primavera P6** and **Microsoft Project**, construction sites generate fragmented progress updates via daily free-text diaries, WhatsApp messages, discipline-specific Excel logs, on-site voice memos, and inspection photos.

Because ground execution data is multimodal, unstructured, and siloed, updates rarely synchronize back to master schedules automatically. Delays compound invisibly until critical milestones are breached.

**SETU AI** acts as an intelligent, automated bridge (*Setu*) connecting unstructured, multimodal ground execution directly to enterprise schedules. Featuring **dual role-based access**, **multimodal proof ingestion (voice notes & picture proof)**, **hybrid AI matching**, **Human-in-the-Loop oversight**, and **real-time delay analytics**, SETU AI brings verifiable transparency, end-to-end traceability, and auditability to enterprise asset execution.

---

## 🔐 Dual Role-Based Access & Authentication

SETU AI enforces a strict operational separation of concerns via two specialized portals:

```text
                               +---------------------------------+
                               |   SETU AI Unified Auth Gate     |
                               +----------------+----------------+
                                                |
                 +------------------------------+-------------------------------+
                 |                                                              |
                 v                                                              v
+------------------------------------+        +--------------------------------------------------+
|  ROLE 1: Field Site Engineer       |        |  ROLE 2: PMO / Planning Engineer                 |
|  - Streamlined mobile/field entry  |        |  - Master schedule baseline upload (P6 / MSP)    |
|  - Voice notes & audio site memos  |        |  - AI matching triage & confidence review queue  |
|  - Photo proof capture + EXIF check|        |  - Human-in-the-Loop (HITL) approval / override  |
|  - Daily logs & quick text diaries |        |  - Real-time S-Curve, Gantt, and delay analytics |
+------------------------------------+        +--------------------------------------------------+

1. Field Site Engineer Portal: Optimized for rapid field data capture directly from work sites. Site engineers submit progress via free-form text, structured discipline logs, transcribed audio voice memos, and geo/timestamp-verified site photos.

2. PMO / Planning Engineer Portal: Built for project controls and schedule governance. Planners upload baseline schedules, review automated AI match proposals, inspect attached media proof, approve/reject linkages, and monitor project health analytics.

🏗️ System Architecture & Multimodal Data Pipeline
[ Field Site Updates & Evidence ]                          [ Master Schedule Baselines ]
  - Free-Text Diaries (.txt / chat)                         - Primavera P6 / MS Project (.xlsx/.csv)
  - Discipline Logs (.xlsx)                                                |
  - Audio Voice Memos (.wav/.mp3)                                                    v
  - Picture Proof (.jpg/.png)                                        +----------------------------------+
                 │                                                   | Module 1: Schedule DB Engine     |
                 ▼                                                   | - SQLite baseline storage        |
+------------------------------------------------+                   | - WBS L5/L6 activity hierarchy   |
| Module 2: Multimodal Field Extraction Pipeline |                   | - Interactive Plotly Gantt View  |
| - Audio Transcriber: Speech-to-Text conversion |                   +----------------+-----------------+
| - Photo Proof Handler: EXIF metadata validator |                                    |
| - Rule/Regex Parser: Action, Tag, Progress %   |                                 |
+-----------------------+------------------------+                                    |
                        │                                                             |
                        ▼                                                             ▼
+-----------------------------------------------------------------------------------------------+
| Module 3: Hybrid AI Semantic Matching Engine                                                  |
| - Domain Terminology Normalization (e.g., "rebar" -> "reinforcement steel")                  |
| - Dense Semantic Embeddings (Sentence-Transformers: all-MiniLM-L6-v2)                         |
| - Lexical Syntactic Alignment (RapidFuzz Token-Set Ratio)                                    |
| - Scikit-Learn Cosine Similarity & Weighted Composite Scoring (0–100%)                        |
+-----------------------------------------------+-----------------------------------------------+
                                                │
                                                ▼
+-----------------------------------------------------------------------------------------------+
| Module 4: Human-in-the-Loop (HITL) Validation & Audit Trail                                   |
| - Confidence Routing: Auto-Match (≥85%) | Review Required (65–84%) | Unmatched (<65%)         |
| - Unified Evidence Cockpit: Inspect text, audio playback, and photo proof side-by-side        |
| - Planner Verification: Approve, remap candidate task, or reject                              |
| - Immutable Audit Trail (`activity_updates_audit` table with user, role, and timestamp)       |
+-----------------------------------------------+-----------------------------------------------+
                                                │
                                                ▼
+-----------------------------------------------------------------------------------------------+
| Module 5: Schedule Synchronization & Variance Engine                                          |
| - State Transition Logic (NOT_STARTED -> IN_PROGRESS -> COMPLETED)                           |
| - Timeline Variance: (Actual Start - Planned Start) & (Actual Finish - Planned Finish)       |
| - Master Schedule Database Updates & Quantity Aggregation                                     |
+-----------------------------------------------+-----------------------------------------------+
                                                │
                                                ▼
+-----------------------------------------------------------------------------------------------+
| Module 6: Executive Delay Intelligence & Analytics Dashboard                                  |
| - Critical Path Float Erosion Alerts                                                         |
| - Discipline Hotspot Analysis (Civil vs. Mechanical vs. Piping slippage)                      |
| - Real-Time Physical S-Curves & Completion Projections                                       |
+-----------------------------------------------------------------------------------------------+

🚀 Key Modules & Capabilities
| Module                       | Simple explanation                                                           | Main output                               |
| ---------------------------- | ---------------------------------------------------------------------------- | ----------------------------------------- |
| **1. Schedule Baseline**     | Reads planned L5/L6 activities from Primavera/MS Project files               | Structured baseline activities            |
| **2. Multimodal Extraction** | Converts text, Excel, voice and photo-based field updates into usable data   | Candidate field records                   |
| **3. Hybrid AI Matcher**     | Finds which planned activity a field update belongs to                       | Activity ID + confidence                  |
| **4. HITL Validation**       | Lets a planner review and approve/reject AI suggestions                      | Verified update                           |
| **5. Progress Sync**         | Writes approved progress into the project database                           | Updated task status/progress              |
| **6. Delay Analytics**       | Compares actual execution with the baseline and identifies schedule problems | Variance, slippage and dashboard insights |

📁 Repository Structure
SETU-AI/
|-- app.py                              # Streamlit dual-role cockpit & authentication gate
|-- requirements.txt                    # Pinned project dependencies
|-- README.md                           # System architecture and technical dossier
|-- database/
|   `-- setu_ai.db                      # SQLite DB (users, baselines, updates, audit trail)
|-- data/
|   |-- schedule/
|   |   `-- project_schedule.xlsx       # Baseline Primavera P6 export (WBS L5/L6)
|   |-- daily_reports/
|   |   |-- site_diary_2026_09_07.txt   # Synthetic unstructured site diary sample
|   |   `-- discipline_daily_log.xlsx   # Multi-column discipline log sample
|   `-- evidence/
|       |-- audio/                      # Audio voice notes (.wav / .mp3)
|       `-- photos/                     # Timestamped on-site inspection photos (.jpg / .png)
|-- src/
|   |-- auth/
|   |   `-- auth_manager.py             # Role-based authentication (Field Engineer vs. PMO)
|   |-- schedule/
|   |   |-- generate_sample_schedule.py # Synthetic L5/L6 baseline schedule generator
|   |   `-- db_manager.py               # SQLite schema setup, upserts, and audit transactions
|   |-- extraction/
|   |   |-- extractor.py                # Regex and rule-based parser for text & logs
|   |   |-- audio_transcriber.py        # Speech-to-text integration (Whisper/ASR)
|   |   `-- image_verifier.py           # Photo EXIF extraction & storage handler
|   |-- matching/
|   |   `-- matcher.py                  # Hybrid semantic & lexical matching engine
|   `-- analytics/
|       `-- engine.py                   # Variance engine and critical path analytics
`-- tests/
    `-- test_pipeline.py                # Automated unit and integration test suite


⚙️ Quickstart Guide
1. Environment Setup
# Clone repository
git clone [https://github.com/your-org/SETU-AI.git](https://github.com/your-org/SETU-AI.git)
cd SETU-AI

# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

2. Initialize Database & Seed Baseline Data
python src/schedule/generate_sample_schedule.py
python src/schedule/db_manager.py

3. Run Automated Tests
Execute the test suite to verify extraction, speech transcription, EXIF parsing, AI matching, and variance computations:
python -m unittest tests/test_pipeline.py

4. Launch the SETU AI Cockpit
streamlit run app.py


🧪 SETU AI — Verification & Testing Matrix
| Test ID   | Target Component                           | Input Condition                                            | Expected Result                                                        | Status |
| --------- | ------------------------------------------ | ---------------------------------------------------------- | ---------------------------------------------------------------------- | ------ |
| `TEST-01` | **Role Authentication Gate**               | Login using `field_engineer` and `pmo_planner` credentials | Correct workspace, role-specific interface, and permissions are loaded | ✅ PASS |
| `TEST-02` | **Discipline Parser**                      | `"1. Civil Discipline: Reinforcement..."`                  | Discipline extracted as **Civil**                                      | ✅ PASS |
| `TEST-03` | **Status Parser**                          | `"Rebar fixing completed today"`                           | Lifecycle status identified as **COMPLETED**                           | ✅ PASS |
| `TEST-04` | **Audio Transcription**                    | Field voice memo in `.wav` format                          | Speech converted to text while preserving key technical entities       | ✅ PASS |
| `TEST-05` | **Image Proof Parser**                     | `.jpg` field inspection photo containing EXIF metadata     | Timestamp, camera information, and EXIF metadata successfully parsed   | ✅ PASS |
| `TEST-06` | **Hybrid AI Matcher**                      | `"Rebar fixing completed for compressor foundation"`       | Correctly matched to `CIV-FND-003` with **≥80% confidence**            | ✅ PASS |
| `TEST-07` | **Variance Calculation**                   | Planned finish: `2026-09-09`; Actual finish: `2026-09-11`  | Finish variance calculated as **+2 days**                              | ✅ PASS |
| `TEST-08` | **Idempotent Lock / Duplicate Prevention** | Duplicate approval submitted for an already reviewed event | Duplicate event rejected and audit lock preserved                      | ✅ PASS |

📊 Verification Summary
| Metric                    |                                                                       Result |
| ------------------------- | ---------------------------------------------------------------------------: |
| **Total Automated Tests** |                                                                        **8** |
| **Tests Passed**          |                                                                        **8** |
| **Tests Failed**          |                                                                        **0** |
| **Pass Rate**             |                                                                     **100%** |
| **Core Systems Covered**  | Authentication, Parsing, ASR, Photo Proof, AI Matching, Schedule Sync, Audit |
| **Overall Status**        |                                                                   **✅ PASS** |
