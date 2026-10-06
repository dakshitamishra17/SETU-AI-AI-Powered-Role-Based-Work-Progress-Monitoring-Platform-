# =========================================================================
# SETU AI: ROLE-BASED LOGIN & MULTI-MODULE WEB APPLICATION
# =========================================================================

import os
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

from src.schedule.db_manager import (
    init_db,
    fetch_all_activities,
    ingest_schedule_file,
    log_audit_record,
    sync_actual_progress,
    get_db_connection,
    get_reviewed_events_map,
    clear_audit_trail
)
from src.extraction.extractor import parse_text_diary, parse_excel_log
from src.extraction.audio_extractor import transcribe_site_audio
from src.matching.matcher import ActivityMatcher
from src.analytics.engine import compute_schedule_analytics

st.set_page_config(
    page_title="SETU AI | Role-Based Portal",
    page_icon="🌉",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- DATABASE & COLD-START SELF-INITIALIZATION ---
init_db()

df_check = fetch_all_activities()
default_sched_path = os.path.join("data", "schedule", "project_schedule.xlsx")
if df_check.empty and os.path.exists(default_sched_path):
    try:
        ingest_schedule_file(default_sched_path)
    except Exception as e:
        print(f"Warning during auto-ingest: {e}")

default_report_dir = os.path.join("data", "daily_reports")
if not os.path.exists(default_report_dir) or not os.listdir(default_report_dir):
    try:
        from src.extraction.generate_sample_reports import main as gen_reports
        gen_reports()
    except Exception as e:
        print(f"Notice: Sample reports auto-generation skipped: {e}")

@st.cache_resource
def get_matcher():
    return ActivityMatcher()

matcher = get_matcher()

# Enterprise dark styling with header removal, white partitions, table borders, and media rendering fixes
st.markdown("""
    <style>
    /* Hide Streamlit top header bar and decoration line to remove top white block */
    header[data-testid="stHeader"] {
        display: none !important;
    }
    div[data-testid="stDecoration"] {
        display: none !important;
    }
    .stApp {
        background: linear-gradient(135deg, #0a192f 0%, #1e293b 100%) !important;
        color: #f8fafc !important;
    }
    .stApp p, .stApp span, .stApp label, .stApp div, .stMarkdown, .stText {
        color: #f8fafc !important;
    }
    
    /* Expander and dropdown container dark theme overrides */
    div[data-testid="stExpander"] {
        background-color: #1e293b !important;
        border: 1px solid #334155 !important;
        border-radius: 8px !important;
    }
    div[data-testid="stExpander"] summary {
        background-color: #1e293b !important;
        color: #f8fafc !important;
    }
    div[data-testid="stExpander"] summary p, div[data-testid="stExpander"] summary span {
        color: #f8fafc !important;
    }
    div[data-testid="stExpanderDetails"] {
        background-color: #0f172a !important;
        color: #f8fafc !important;
        border-top: 1px solid #334155 !important;
        padding: 20px !important;
        border-bottom-left-radius: 8px !important;
        border-bottom-right-radius: 8px !important;
    }

    /* Force visible bright white horizontal dividers/partitions */
    hr {
        border: none !important;
        height: 2px !important;
        background-color: #ffffff !important;
        margin: 2rem 0 !important;
        opacity: 0.9 !important;
    }
    /* Force visible white table borders and headers */
    table {
        border-collapse: collapse !important;
        width: 100% !important;
        background-color: #0f172a !important;
    }
    th {
        background-color: #1e293b !important;
        color: #38bdf8 !important;
        border: 1px solid #ffffff !important;
        padding: 10px !important;
    }
    td {
        border: 1px solid rgba(255, 255, 255, 0.4) !important;
        color: #f8fafc !important;
        padding: 8px !important;
    }
    section[data-testid="stSidebar"] {
        background-color: #0f172a !important;
        border-right: 1px solid #ffffff !important;
    }
    section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] span, section[data-testid="stSidebar"] label, section[data-testid="stSidebar"] div, section[data-testid="stSidebar"] .stMarkdown {
        color: #38bdf8 !important;
    }
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #ffffff;
        border-top: 4px solid #38bdf8;
        border-radius: 12px;
        padding: 16px 20px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
    }
    div[data-testid="stMetric"] label {
        font-size: 0.82rem;
        font-weight: 600;
        text-transform: uppercase;
        color: #94a3b8 !important;
    }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        font-size: 1.8rem;
        font-weight: 700;
        color: #f8fafc !important;
    }
    .high-conf { color: #10b981 !important; font-weight: bold; }
    .med-conf  { color: #f59e0b !important; font-weight: bold; }
    .low-conf  { color: #ef4444 !important; font-weight: bold; }
    .login-card {
        background: rgba(30, 41, 59, 0.8);
        padding: 30px;
        border-radius: 16px;
        border: 1px solid rgba(56, 189, 248, 0.3);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        backdrop-filter: blur(8px);
        text-align: center;
    }
    div.stTextInput input, div.stSelectbox select, div.stTextArea textarea {
        background-color: #0f172a !important;
        color: #38bdf8 !important;
        border: 1px solid #38bdf8 !important;
        border-radius: 8px !important;
    }
    div.stTextInput input::placeholder, div.stTextArea textarea::placeholder {
        color: #38bdf8 !important;
        opacity: 0.85;
    }
    div[data-testid="stFileUploader"] {
        background-color: #0f172a !important;
        border: 2px dashed #38bdf8 !important;
        border-radius: 12px !important;
        padding: 15px !important;
    }
    div[data-testid="stFileUploader"] section {
        background-color: #0f172a !important;
    }
    div[data-testid="stFileUploader"] span, div[data-testid="stFileUploader"] small, div[data-testid="stFileUploader"] div {
        color: #38bdf8 !important;
    }
    .stButton button {
        background: linear-gradient(90deg, #0284c7 0%, #2563eb 100%);
        color: white !important;
        font-weight: 600;
        border-radius: 8px;
        border: none;
        padding: 0.5rem 1rem;
        box-shadow: 0 4px 14px rgba(37, 99, 235, 0.4);
        transition: all 0.3s ease;
    }
    .stButton button:hover {
        background: linear-gradient(90deg, #0284c7 20%, #1d4ed8 100%);
        box-shadow: 0 6px 20px rgba(56, 189, 248, 0.6);
        transform: translateY(-1px);
    }
    </style>
""", unsafe_allow_html=True)

# --- SESSION STATE INITIALIZATION FOR AUTH ---
if "authenticated_role" not in st.session_state:
    st.session_state["authenticated_role"] = None 

# --- HOMEPAGE: DUAL COMPARTMENT LOGIN PORTAL ---
if st.session_state["authenticated_role"] is None:
    st.markdown("<h2 style='color: #38bdf8; text-align: center;'>🌉 SETU AI (सेतु): Schedule Execution Tracking & Unification Engine</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #38bdf8;'>Oil India Limited (OIL) | SIH 2026 Enterprise Portal</p>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown("### 🔐 Portal Access")
    st.write("Please select your operational role and enter any PIN to access your dedicated workspace compartment.")
    
    col_sup, col_pm = st.columns(2, gap="large")
    
    with col_sup:
        st.markdown("""
            <div class="login-card">
                <h3 style="color: #38bdf8;">👷 Site Supervisor Portal</h3>
                <p style="color: #38bdf8;">Access field tools to log daily progress, record multi-modal voice notes, capture geo-tagged photo proof, and link site updates to master schedules.</p>
            </div>
        """, unsafe_allow_html=True)
        
        with st.form("supervisor_login_form"):
            sup_pass = st.text_input("Supervisor Access PIN (Any entry allowed)", type="password", key="sup_pin", placeholder="Enter any PIN...")
            sup_btn = st.form_submit_button("Login as Site Supervisor", type="primary")
            if sup_btn:
                st.session_state["authenticated_role"] = "Supervisor"
                st.rerun()

    with col_pm:
        st.markdown("""
            <div class="login-card">
                <h3 style="color: #38bdf8;">👔 Project Manager Portal</h3>
                <p style="color: #38bdf8;">Access executive dashboards, audit trails, AI match review queues, variance tracking, and baseline schedule controls to audit and approve results.</p>
            </div>
        """, unsafe_allow_html=True)
        
        with st.form("pm_login_form"):
            pm_pass = st.text_input("Project Manager Access PIN (Any entry allowed)", type="password", key="pm_pin", placeholder="Enter any PIN...")
            pm_btn = st.form_submit_button("Login as Project Manager", type="primary")
            if pm_btn:
                st.session_state["authenticated_role"] = "Project Manager"
                st.rerun()

# --- LOGGED IN APPLICATION WORKSPACE ---
else:
    role = st.session_state["authenticated_role"]
    
    # --- SIDEBAR ---
    with st.sidebar:
        st.markdown(f"### 🌉 SETU AI Console")
        st.caption(f"Logged in as: **{role}**")
        if st.button("🚪 Logout / Switch Role"):
            st.session_state["authenticated_role"] = None
            st.rerun()
            
        st.markdown("---")
        st.subheader("🌐 Field Connectivity & Settings")
        is_offline = st.checkbox("Simulate Offline Mode (Cache Local)", value=False)
        if is_offline:
            st.warning("⚠️ Offline Mode Active: Saved locally.")
        else:
            st.success("🟢 Online: Syncing to P6 server.")

        target_lang = st.selectbox(
            "Supervisor Spoken Language",
            options=["English (en)", "Hindi (hi)", "Bengali (bn)", "Tamil (ta)", "Marathi (mr)"],
            index=0
        )
        lang_code = target_lang.split("(")[-1].strip(")")

        # Role-Specific Sidebar Upload Options
        if role == "Project Manager":
            st.markdown("---")
            st.subheader("📁 Master Schedule Management")
            uploaded_master = st.file_uploader("Upload Master Schedule (.xlsx)", type=["xlsx", "xls"], key="sidebar_master_upload")
            if uploaded_master is not None:
                os.makedirs(os.path.join("data", "schedule"), exist_ok=True)
                path = os.path.join("data", "schedule", uploaded_master.name)
                with open(path, "wb") as f:
                    f.write(uploaded_master.getbuffer())
                if st.button("Ingest Master Schedule"):
                    try:
                        ingest_schedule_file(path)
                        st.success("Master schedule ingested successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

        elif role == "Supervisor":
            st.markdown("---")
            st.subheader("📤 Batch Site Report Upload")
            uploaded_site_report = st.file_uploader("Upload Report (.xlsx, .csv, .txt)", type=["xlsx", "xls", "csv", "txt"], key="sidebar_site_upload")
            if uploaded_site_report is not None:
                os.makedirs("data/daily_reports", exist_ok=True)
                report_path = os.path.join("data", "daily_reports", uploaded_site_report.name)
                with open(report_path, "wb") as f:
                    f.write(uploaded_site_report.getbuffer())
                if st.button("Process Site Report File"):
                    try:
                        ext = uploaded_site_report.name.split('.')[-1].lower()
                        events = []
                        if ext in ["xlsx", "xls", "csv"]:
                            events = parse_excel_log(report_path)
                        elif ext == "txt":
                            events = parse_text_diary(report_path)
                        
                        if "custom_field_submissions" not in st.session_state:
                            st.session_state["custom_field_submissions"] = []
                        
                        for ev in events:
                            st.session_state["custom_field_submissions"].insert(0, ev)
                        
                        st.success(f"Loaded {len(events)} site entries from file!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to parse report file: {e}")

    # --- ROLE-BASED NAVIGATION ROUTING ---
    if role == "Supervisor":
        st.markdown("## 👷 Site Supervisor Field Operations")
        st.caption("Multi-modal data collection and task linking for Duliajan Gas Compressor Station.")
        st.markdown("---")
        
        df_sched_options = fetch_all_activities()

        with st.form("field_capture_form"):
            col_input1, col_input2 = st.columns(2)
            
            with col_input1:
                st.markdown("##### 🎙️ Voice & Text Reporting")
                audio_data = st.audio_input("Record voice update from site")
                text_fallback = st.text_area("Or type site observation manually:", placeholder="e.g., Poured 50m3 concrete for Foundation Pier 3...")
                
                st.markdown("##### 🔗 Target Schedule Activity Link")
                if not df_sched_options.empty:
                    activity_choices = [
                        f"{row['activity_id']} | {row['discipline']} | {row['activity_description']}" 
                        for _, row in df_sched_options.iterrows()
                    ]
                    selected_task_str = st.selectbox("Select Target Activity ID for this Proof:", options=activity_choices)
                else:
                    selected_task_str = None
                
            with col_input2:
                st.markdown("##### 📸 Visual Proof & Location")
                photo_proof = st.camera_input("Take site progress photo")
                image_file = st.file_uploader("Or upload site image file", type=["jpg", "png", "jpeg"])
                
                current_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                simulated_gps = "26.6749° N, 94.5362° E (Duliajan Station Zone 3)"
                
                st.text_input("Captured Timestamp", value=current_timestamp, disabled=True)
                st.text_input("Auto-Tagged GPS Chainage", value=simulated_gps, disabled=True)

            submit_report = st.form_submit_button("🚀 Transmit Field Report to AI Engine", type="primary")

            if submit_report:
                processed_text = ""
                saved_image_path = None
                saved_audio_path = None
                
                target_activity_id = selected_task_str.split(" | ")[0].strip() if selected_task_str else "UNKNOWN"
                
                task_discipline = "Civil & Structural"
                if not df_sched_options.empty and target_activity_id != "UNKNOWN":
                    match_row = df_sched_options[df_sched_options["activity_id"] == target_activity_id]
                    if not match_row.empty:
                        task_discipline = match_row.iloc[0]["discipline"]

                os.makedirs("assets/uploads", exist_ok=True)
                if photo_proof is not None:
                    saved_image_path = os.path.join("assets/uploads", f"cam_photo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg")
                    with open(saved_image_path, "wb") as f:
                        f.write(photo_proof.getbuffer())
                elif image_file is not None:
                    saved_image_path = os.path.join("assets/uploads", image_file.name)
                    with open(saved_image_path, "wb") as f:
                        f.write(image_file.getbuffer())

                if audio_data is not None:
                    saved_audio_path = os.path.join("assets/uploads", f"audio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav")
                    with open(saved_audio_path, "wb") as f:
                        f.write(audio_data.getbuffer())

                # MATCHING PRIORITY: Use typed text first. If empty, fall back to voice transcription.
                if text_fallback and text_fallback.strip():
                    processed_text = text_fallback.strip()
                elif audio_data is not None:
                    with st.spinner("Processing audio transcription for matching..."):
                        processed_text = transcribe_site_audio(audio_data, language_code=lang_code)
                else:
                    processed_text = f"Progress update linked directly to activity {target_activity_id} with visual proof."

                if "custom_field_submissions" not in st.session_state:
                    st.session_state["custom_field_submissions"] = []

                st.session_state["custom_field_submissions"].insert(0, {
                    "report_date": datetime.now().strftime("%Y-%m-%d"),
                    "discipline": task_discipline,
                    "raw_text": processed_text,
                    "clean_activity": processed_text,
                    "event_type": "IN_PROGRESS",
                    "progress_pct": 50.0,
                    "preselected_activity_id": target_activity_id,
                    "language_code": lang_code,
                    "image_path": saved_image_path,
                    "audio_path": saved_audio_path
                })

                st.success(f"Successfully transmitted report and proofs to Activity `{target_activity_id}`!")
                if saved_image_path and os.path.exists(saved_image_path):
                    st.image(saved_image_path, caption="Attached Proof", width=300)
                st.balloons()

    elif role == "Project Manager":
        st.markdown("## 👔 Project Manager Audit & Executive Control Center")
        st.caption("Audit site reports, verify AI candidate matches, approve progress, and monitor project health.")
        st.markdown("---")

        nav_tab1, nav_tab2, nav_tab3, nav_tab4, nav_tab5 = st.tabs([
            "🔍 Site Review & AI Match Queue (Audit & Verify)",
            "📊 Executive Delay Analytics",
            "⚡ Live Progress & Variance Tracking",
            "📅 Baseline Master Schedule",
            "📜 Audit Verification"
        ])

        with nav_tab1:
            st.subheader("AI Match Verification & Approval Queue")
            st.write("Review incoming site reports, inspect photo/audio proofs, and approve or reject schedule synchronization.")

            raw_events = []
            if "custom_field_submissions" in st.session_state and st.session_state["custom_field_submissions"]:
                raw_events.extend(st.session_state["custom_field_submissions"])

            default_txt = os.path.join("data", "daily_reports", "site_diary_2026_09_07.txt")
            if os.path.exists(default_txt):
                raw_events.extend(parse_text_diary(default_txt))

            if not raw_events:
                st.warning("No site updates pending review.")
            else:
                df_sched = fetch_all_activities()
                reviewed_map = get_reviewed_events_map()
                st.caption(f"Total events in review queue: {len(raw_events)}")

                for i, event in enumerate(raw_events):
                    event_key = f"{event['report_date']}||{event['raw_text'].strip()}"
                    is_reviewed = event_key in reviewed_map
                    review_info = reviewed_map.get(event_key, {})

                    candidates = matcher.match_activity(
                        event["clean_activity"] if "clean_activity" in event else event["raw_text"],
                        extracted_discipline=event["discipline"],
                        top_k=10
                    )

                    top = candidates[0] if candidates else None
                    conf = top["confidence"] if top else 0.0

                    if conf >= 85:
                        conf_badge = f'<span class="high-conf">🟢 High Confidence ({conf}%)</span>'
                    elif conf >= 65:
                        conf_badge = f'<span class="med-conf">🟡 Review Recommended ({conf}%)</span>'
                    else:
                        conf_badge = f'<span class="low-conf">🔴 Low Match ({conf}%)</span>'

                    status_tag = f" — [{review_info.get('decision', 'PROCESSED')}: {review_info.get('matched_activity_id', '')}]" if is_reviewed else f" — {conf}% Match"

                    disp_title = event.get('clean_activity', event['raw_text'])
                    with st.expander(f"Event #{i+1}: [{event['discipline']}] {disp_title[:50]}...{status_tag}", expanded=(i == 0 and not is_reviewed)):
                        c1, c2 = st.columns([1.2, 1])

                        with c1:
                            st.markdown("**Site Report Observation:**")
                            st.markdown(
                                f"""<div style="background-color: #1e293b; color: #38bdf8 !important; padding: 12px; border-radius: 8px; border: 1px solid #334155; font-family: monospace; white-space: pre-wrap; font-weight: 600;">{event['raw_text']}</div>""",
                                unsafe_allow_html=True
                            )
                            st.write(f"📅 **Date:** `{event['report_date']}` | **Status:** `{event['event_type']}` | **Progress:** `{event['progress_pct']}%`")

                            # Render Voice Recording if present
                            audio_p = event.get("audio_path")
                            if audio_p and os.path.exists(audio_p):
                                st.markdown("##### 🎙️ Attached Voice Recording")
                                st.audio(audio_p)

                            # Render Photo Proof if present
                            img_p = event.get("image_path")
                            if img_p and os.path.exists(img_p):
                                st.markdown("##### 📸 Attached Field Photo Proof")
                                st.image(img_p, caption="Verified Site Capture", width=280)

                        with c2:
                            if is_reviewed:
                                decision = review_info.get("decision")
                                act_id = review_info.get("matched_activity_id")
                                if decision == "APPROVED":
                                    st.success(f"✅ **Action Taken:** Approved and linked to `{act_id}`.")
                                else:
                                    st.warning(f"🚩 **Action Taken:** Flagged as unlinked activity.")
                            else:
                                st.markdown(f"**AI Recommended Link:** {conf_badge}", unsafe_allow_html=True)
                                if top:
                                    st.write(f"**Task ID:** `{top['activity_id']}` ({top['level']})")
                                    st.write(f"**Description:** {top['activity_description']}")
                                    st.caption(f"WBS: {top['wbs_package']} | Semantic: {top['semantic_score']}% | Fuzzy: {top['fuzzy_score']}%")
                                else:
                                    st.write("No matching candidate found.")

                        st.markdown("---")

                        if is_reviewed:
                            st.info("🔒 This event has been processed. Action buttons are locked to preserve audit integrity.")
                        else:
                            act_col1, act_col2, act_col3 = st.columns([1.5, 2.5, 1])

                            with act_col2:
                                cand_choices = [f"{c['activity_id']} | {c['activity_description']} ({c['confidence']}%)" for c in candidates]
                                chosen_cand_str = st.selectbox("Target Schedule Activity:", options=cand_choices, key=f"sel_cand_{i}")
                                selected_act_id = chosen_cand_str.split(" | ")[0].strip() if chosen_cand_str else (top['activity_id'] if top else None)

                            with act_col1:
                                if st.button("✓ Approve & Verify Match", key=f"app_btn_{i}", type="primary"):
                                    final_act_id = event.get("preselected_activity_id", selected_act_id)
                                    if final_act_id and final_act_id != "UNKNOWN":
                                        try:
                                            matched_desc = top["activity_description"] if (top and top["activity_id"] == final_act_id) else chosen_cand_str
                                            
                                            log_audit_record({
                                                "report_date": event["report_date"],
                                                "discipline": event["discipline"],
                                                "raw_site_text": event["raw_text"],
                                                "matched_activity_id": final_act_id,
                                                "matched_description": matched_desc,
                                                "confidence": conf if "preselected_activity_id" not in event else 100.0,
                                                "event_type": event["event_type"],
                                                "reported_progress": event["progress_pct"],
                                                "decision": "APPROVED",
                                                "reviewer_comments": "Verified and approved by Project Manager.",
                                                "image_path": event.get("image_path"),
                                                "audio_path": event.get("audio_path")
                                            })

                                            sync_actual_progress(
                                                activity_id=final_act_id,
                                                report_date=event["report_date"],
                                                event_type=event["event_type"],
                                                progress_pct=event["progress_pct"]
                                            )

                                            st.toast(f"✅ Approved & Synced: {final_act_id}", icon="🚀")
                                            st.rerun()
                                        except Exception as err:
                                            st.error(f"Approval failed: {err}")

                            with act_col3:
                                if st.button("🚩 Reject / Flag", key=f"rej_btn_{i}"):
                                    final_act_id = event.get("preselected_activity_id", "UNLINKED")
                                    try:
                                        log_audit_record({
                                            "report_date": event["report_date"],
                                            "discipline": event["discipline"],
                                            "raw_site_text": event["raw_text"],
                                            "matched_activity_id": final_act_id if final_act_id != "UNKNOWN" else "UNLINKED",
                                            "matched_description": "None",
                                            "confidence": conf,
                                            "event_type": event["event_type"],
                                            "reported_progress": event["progress_pct"],
                                            "decision": "REJECTED",
                                            "reviewer_comments": "Flagged as unlinked by Project Manager.",
                                            "image_path": event.get("image_path"),
                                            "audio_path": event.get("audio_path")
                                        })
                                        st.toast("Flagged as unlinked", icon="⚠️")
                                        st.rerun()
                                    except Exception as err:
                                        st.error(f"Rejection failed: {err}")

        with nav_tab2:
            analytics = compute_schedule_analytics()
            if analytics:
                st.subheader("Executive Project Health & Delay Intelligence")
                ek1, ek2, ek3, ek4, ek5 = st.columns(5)
                ek1.metric("Total Activities", analytics["total_tasks"])
                ek2.metric("Completed Tasks", f"{analytics['completed_tasks']} / {analytics['total_tasks']}")
                ek3.metric("Delayed Tasks", analytics["delayed_count"], delta=f"-{analytics['total_delay_days']} days slippage", delta_color="inverse")
                ek4.metric("Critical Path Threats", analytics["critical_delayed_count"], delta="High Risk" if analytics["critical_delayed_count"] > 0 else "Normal", delta_color="inverse")
                comp_rate = round((analytics["completed_tasks"] / analytics["total_tasks"]) * 100, 1) if analytics["total_tasks"] > 0 else 0
                ek5.metric("Project Physical %", f"{comp_rate}%")

        with nav_tab3:
            st.subheader("Live Execution vs. Baseline Schedule Timeline")
            st.write("Visualizing planned timing versus execution milestones across project disciplines.")
            
            df_live = fetch_all_activities()
            if not df_live.empty and "planned_start" in df_live.columns and "planned_finish" in df_live.columns:
                fig = px.timeline(
                    df_live,
                    x_start="planned_start",
                    x_end="planned_finish",
                    y="activity_id",
                    color="discipline",
                    hover_data=["activity_description", "wbs_package", "progress_pct", "status"],
                    title="Baseline Schedule Roadmap & Timing Analysis"
                )
                fig.update_yaxes(categoryorder="total ascending")
                fig.update_layout(
                    plot_bgcolor="#0f172a",
                    paper_bgcolor="#0f172a",
                    font_color="#f8fafc",
                    height=520,
                    margin=dict(l=20, r=20, t=50, b=20)
                )
                st.plotly_chart(fig, use_container_width=True)
                
                with st.expander("View Raw Variance & Progress Table"):
                    st.dataframe(df_live, use_container_width=True)
            else:
                st.warning("Insufficient schedule data available to render timeline chart.")

        with nav_tab4:
            st.subheader("Baseline Master Schedule Viewer")
            df_activities = fetch_all_activities()
            st.dataframe(df_activities, use_container_width=True)

        with nav_tab5:
            st.subheader("Audit Verification")
            st.write("Review, audit, and manage verified site updates, logs, and visual evidence.")

            if st.button("🗑️ Clear Audit Log", type="primary"):
                try:
                    clear_audit_trail()
                    st.success("Audit verification log has been cleared successfully.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to clear audit log: {e}")

            conn = get_db_connection()
            df_audit = pd.read_sql_query("SELECT * FROM activity_updates_audit ORDER BY timestamp DESC", conn)
            conn.close()

            if not df_audit.empty:
                for idx, row in df_audit.iterrows():
                    st.divider()
                    col_img, col_txt = st.columns([1, 2])
                    with col_img:
                        img_path = row.get("image_path")
                        audio_path = row.get("audio_path")
                        
                        if img_path and os.path.exists(str(img_path)):
                            st.image(str(img_path), caption=f"Audit Entry ID: {row.get('id', idx)}", width=250)
                        if audio_path and os.path.exists(str(audio_path)):
                            st.audio(str(audio_path))
                        if not (img_path and os.path.exists(str(img_path))) and not (audio_path and os.path.exists(str(audio_path))):
                            st.info("No media attached")
                            
                    with col_txt:
                        st.markdown(f"**Activity ID:** `{row.get('matched_activity_id', 'N/A')}`")
                        st.markdown(f"**Matched Description:** {row.get('matched_description', 'N/A')}")
                        st.markdown(f"**Raw Site Text:** {row.get('raw_site_text', 'N/A')}")
                        st.markdown(f"**Decision:** `{row.get('decision', 'N/A')}` | **Confidence:** `{row.get('confidence', 0)}%`")
                        st.markdown(f"**Timestamp:** `{row.get('timestamp', 'N/A')}`")
            else:
                st.info("Audit verification log is currently empty.")