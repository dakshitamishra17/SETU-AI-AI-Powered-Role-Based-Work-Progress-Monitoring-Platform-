"""
OIL-Track AI - Module 1
generate_sample_schedule.py: Generates a realistic baseline schedule for an 
OIL infrastructure facility (Compressor Station & Pipeline Manifold).
"""

import os
import pandas as pd

SCHEDULE_DATA = [
    # --- CIVIL DISCIPLINE ---
    {
        "activity_id": "CIV-FND-001",
        "level": "L5",
        "discipline": "Civil",
        "wbs_package": "Foundation Works",
        "activity_description": "Excavation for Compressor Foundation",
        "planned_start": "2026-09-01",
        "planned_finish": "2026-09-03",
        "baseline_status": "PLANNED"
    },
    {
        "activity_id": "CIV-FND-002",
        "level": "L5",
        "discipline": "Civil",
        "wbs_package": "Foundation Works",
        "activity_description": "Plain Cement Concrete (PCC) for Compressor Foundation",
        "planned_start": "2026-09-04",
        "planned_finish": "2026-09-05",
        "baseline_status": "PLANNED"
    },
    {
        "activity_id": "CIV-FND-003",
        "level": "L5",
        "discipline": "Civil",
        "wbs_package": "Foundation Works",
        "activity_description": "Reinforcement Work for Compressor Foundation",
        "planned_start": "2026-09-06",
        "planned_finish": "2026-09-09",
        "baseline_status": "CRITICAL"
    },
    {
        "activity_id": "CIV-FND-004",
        "level": "L6",
        "discipline": "Civil",
        "wbs_package": "Foundation Works",
        "activity_description": "Foundation Concreting for Compressor Unit",
        "planned_start": "2026-09-10",
        "planned_finish": "2026-09-11",
        "baseline_status": "CRITICAL"
    },
    {
        "activity_id": "CIV-FND-005",
        "level": "L6",
        "discipline": "Civil",
        "wbs_package": "Foundation Works",
        "activity_description": "Curing and Deshuttering of Compressor Foundation",
        "planned_start": "2026-09-12",
        "planned_finish": "2026-09-16",
        "baseline_status": "PLANNED"
    },

    # --- MECHANICAL / ROTATING EQUIPMENT ---
    {
        "activity_id": "ROT-EQP-001",
        "level": "L5",
        "discipline": "Mechanical",
        "wbs_package": "Rotating Equipment",
        "activity_description": "Compressor Equipment Placement on Foundation",
        "planned_start": "2026-09-18",
        "planned_finish": "2026-09-20",
        "baseline_status": "CRITICAL"
    },
    {
        "activity_id": "ROT-EQP-002",
        "level": "L6",
        "discipline": "Mechanical",
        "wbs_package": "Rotating Equipment",
        "activity_description": "Compressor Shaft Alignment and Grouting",
        "planned_start": "2026-09-21",
        "planned_finish": "2026-09-24",
        "baseline_status": "PLANNED"
    },

    # --- PIPING DISCIPLINE ---
    {
        "activity_id": "PIP-ERE-001",
        "level": "L5",
        "discipline": "Piping",
        "wbs_package": "Pipe Rack",
        "activity_description": "Pipe Rack Structural Steel Erection",
        "planned_start": "2026-09-12",
        "planned_finish": "2026-09-16",
        "baseline_status": "PLANNED"
    },
    {
        "activity_id": "PIP-ERE-002",
        "level": "L6",
        "discipline": "Piping",
        "wbs_package": "Pipe Rack",
        "activity_description": "Piping Alignment and Joint Fit-Up",
        "planned_start": "2026-09-16",
        "planned_finish": "2026-09-19",
        "baseline_status": "PLANNED"
    },
    {
        "activity_id": "PIP-LIN-001",
        "level": "L6",
        "discipline": "Piping",
        "wbs_package": "Process Piping",
        "activity_description": "Suction and Discharge Process Line Installation",
        "planned_start": "2026-09-20",
        "planned_finish": "2026-09-25",
        "baseline_status": "CRITICAL"
    },
    {
        "activity_id": "PIP-HYD-001",
        "level": "L6",
        "discipline": "Piping",
        "wbs_package": "Process Piping",
        "activity_description": "Hydrotesting of Compressor Header Line",
        "planned_start": "2026-09-26",
        "planned_finish": "2026-09-28",
        "baseline_status": "MILESTONE"
    },

    # --- ELECTRICAL DISCIPLINE ---
    {
        "activity_id": "ELE-CAB-001",
        "level": "L5",
        "discipline": "Electrical",
        "wbs_package": "Cabling and Trays",
        "activity_description": "Main Overhead Cable Tray Installation",
        "planned_start": "2026-09-17",
        "planned_finish": "2026-09-20",
        "baseline_status": "PLANNED"
    },
    {
        "activity_id": "ELE-CAB-002",
        "level": "L6",
        "discipline": "Electrical",
        "wbs_package": "Cabling and Trays",
        "activity_description": "HT Power Cable Pulling and Termination",
        "planned_start": "2026-09-21",
        "planned_finish": "2026-09-24",
        "baseline_status": "PLANNED"
    },
    {
        "activity_id": "ELE-MOT-001",
        "level": "L6",
        "discipline": "Electrical",
        "wbs_package": "Substation Works",
        "activity_description": "Electric Motor Hookup and Insulation Resistance Test",
        "planned_start": "2026-09-25",
        "planned_finish": "2026-09-27",
        "baseline_status": "PLANNED"
    },

    # --- INSTRUMENTATION DISCIPLINE ---
    {
        "activity_id": "INS-INS-001",
        "level": "L5",
        "discipline": "Instrumentation",
        "wbs_package": "Field Instruments",
        "activity_description": "Pressure and Temperature Transmitter Installation",
        "planned_start": "2026-09-22",
        "planned_finish": "2026-09-25",
        "baseline_status": "PLANNED"
    },
    {
        "activity_id": "INS-TST-001",
        "level": "L6",
        "discipline": "Instrumentation",
        "wbs_package": "Loop Testing",
        "activity_description": "Transmitter to PLC Instrument Loop Checking",
        "planned_start": "2026-09-26",
        "planned_finish": "2026-09-29",
        "baseline_status": "CRITICAL"
    },

    # --- HSE DISCIPLINE ---
    {
        "activity_id": "HSE-SAF-001",
        "level": "L5",
        "discipline": "HSE",
        "wbs_package": "Safety Systems",
        "activity_description": "Fire Hydrant and Flame Detector Placement",
        "planned_start": "2026-09-18",
        "planned_finish": "2026-09-22",
        "baseline_status": "PLANNED"
    },
    {
        "activity_id": "HSE-INS-001",
        "level": "L6",
        "discipline": "HSE",
        "wbs_package": "Safety Systems",
        "activity_description": "Emergency Safety Shower and Eyewash Inspection",
        "planned_start": "2026-09-24",
        "planned_finish": "2026-09-25",
        "baseline_status": "PLANNED"
    }
]

def generate_schedule():
    df = pd.DataFrame(SCHEDULE_DATA)
    output_dir = os.path.join("data", "schedule")
    os.makedirs(output_dir, exist_ok=True)

    csv_path = os.path.join(output_dir, "project_schedule.csv")
    excel_path = os.path.join(output_dir, "project_schedule.xlsx")

    df.to_csv(csv_path, index=False)
    df.to_excel(excel_path, index=False, engine="openpyxl")

    print(f"[OK] Generated {len(df)} schedule activities:")
    print(f"     -> CSV:   {csv_path}")
    print(f"     -> Excel: {excel_path}")

if __name__ == "__main__":
    generate_schedule()