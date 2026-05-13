"""seed_demo_plm.py

Generates all engineering drawing files (PDF + PNG) and seeds the PLM database.

Usage:
    python scripts/create_demo_plm.py   # create empty DB first
    python scripts/seed_demo_plm.py     # generate drawings + seed DB
"""

from __future__ import annotations

import math
import random
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

# ── third-party ─────────────────────────────────────────────────────────────
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas as rl_canvas
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.plm.models import Base, Drawing, Part

# ── layout constants (all in mm, converted to pts when calling reportlab) ───
PW = 420   # A3 landscape width  mm
PH = 297   # A3 landscape height mm
BDR = 10   # border margin        mm
TB_H = 55  # title-block height   mm
ZONE_H = 8 # zone-tick height     mm

# drawing-area extents (mm)
DA_X0 = BDR
DA_Y0 = BDR + TB_H           # above title block
DA_X1 = PW - BDR
DA_Y1 = PH - BDR

FONTS = {
    "normal": "Helvetica",
    "bold": "Helvetica-Bold",
    "italic": "Helvetica-Oblique",
}


# ══════════════════════════════════════════════════════════════════════════════
#  MASTER DATA
# ══════════════════════════════════════════════════════════════════════════════

PARTS_DATA: List[Dict] = [
    # ── Product 1 : Engine Coolant Pump ─────────────────────────────────────
    dict(part_number="PUMP-ASSY-1000",        part_name="Engine Coolant Pump Assembly",
         part_type="assembly",    revision="A", lifecycle_state="released", drawing_id="DWG-1000"),
    dict(part_number="PUMP-HOUSING-SA-1100",  part_name="Pump Housing Sub-Assembly",
         part_type="sub_assembly", revision="B", lifecycle_state="released", drawing_id="DWG-1100"),
    dict(part_number="PUMP-HOUSING-1110",     part_name="Pump Housing Body",
         part_type="component",   revision="C", lifecycle_state="released", drawing_id="DWG-1110"),
    dict(part_number="COVER-PLATE-1120",      part_name="Pump Housing Cover Plate",
         part_type="component",   revision="A", lifecycle_state="released", drawing_id="DWG-1120"),
    dict(part_number="SHAFT-IMPELLER-SA-1200",part_name="Shaft and Impeller Sub-Assembly",
         part_type="sub_assembly", revision="A", lifecycle_state="released", drawing_id="DWG-1200"),
    dict(part_number="DRIVE-SHAFT-1210",      part_name="Coolant Pump Drive Shaft",
         part_type="component",   revision="B", lifecycle_state="released", drawing_id="DWG-1210"),
    dict(part_number="IMPELLER-1220",         part_name="Coolant Pump Impeller",
         part_type="component",   revision="A", lifecycle_state="in_work",  drawing_id="DWG-1220"),
    # ── Product 2 : Connecting Rod ───────────────────────────────────────────
    dict(part_number="CONROD-ASSY-2000",      part_name="Connecting Rod Assembly",
         part_type="assembly",    revision="A", lifecycle_state="released", drawing_id="DWG-2000"),
    dict(part_number="CONROD-BODY-2100",      part_name="Connecting Rod Body",
         part_type="component",   revision="D", lifecycle_state="released", drawing_id="DWG-2100"),
    dict(part_number="BIG-END-CAP-2200",      part_name="Connecting Rod Big End Cap",
         part_type="component",   revision="B", lifecycle_state="released", drawing_id="DWG-2200"),
    dict(part_number="FASTENER-KIT-SA-2300",  part_name="Rod Fastener Kit Sub-Assembly",
         part_type="sub_assembly", revision="A", lifecycle_state="released", drawing_id="DWG-2300"),
    dict(part_number="ROD-BOLT-2310",         part_name="Connecting Rod High-Strength Bolt",
         part_type="component",   revision="A", lifecycle_state="released", drawing_id="DWG-2310"),
    dict(part_number="LOCK-NUT-2320",         part_name="Connecting Rod Self-Locking Nut",
         part_type="component",   revision="A", lifecycle_state="released", drawing_id="DWG-2320"),
]

# keyed by drawing_id
DRAWINGS_SPECS: Dict[str, Dict] = {

  "DWG-1000": dict(
    drawing_id="DWG-1000", part_number="PUMP-ASSY-1000",
    drawing_number="DWG-1000", revision="A",
    drawing_title="Engine Coolant Pump Assembly",
    drawing_type="assembly", sheet_count=2,   # sheet 2 intentionally missing
    drawing_status="released", file_type="pdf",
    scale="1:2", mass="3.18 kg", tolerance="ISO 2768-m", finish="SEE PARTS",
    material="SEE PART DRAWINGS",
    drawn_by="J. SMITH", checked_by="K. JONES", approved_by="M. LEE",
    date="2024-01-15",
    bom=[
      dict(item=1, pn="PUMP-HOUSING-SA-1100",  desc="Pump Housing Sub-Assembly",       qty=1, mat="AL A356-T6"),
      dict(item=2, pn="SHAFT-IMPELLER-SA-1200", desc="Shaft & Impeller Sub-Assembly",  qty=1, mat="SEE PARTS"),
    ],
    notes=[
      "1. ALL DIMENSIONS IN MILLIMETRES UNLESS OTHERWISE STATED.",
      "2. ASSEMBLY PER WORK INSTRUCTION WI-PUMP-001 REV.C.",
      "3. APPLY THREAD SEALANT (LOCTITE 572) TO ALL HYDRAULIC FITTINGS.",
      "4. PRESSURE TEST: 5 BAR FOR 10 MIN. ZERO LEAKAGE PERMITTED.",
      "5. TIGHTEN COVER BOLTS IN CROSS PATTERN. TORQUE: 12 ±1 Nm.",
      "6. SHAFT SEAL: PRE-LUBRICATE WITH CLEAN COOLANT PRIOR TO INSTALL.",
      "7. IMPELLER INSTALLATION TORQUE: 35 ±2 Nm.",
      "8. RECORD SERIAL NO. ON TEST CERT PER QP-TEST-007.",
      "NOTE: SHEET 2 (DETAIL VIEWS) - SEE DWG-1000-SH2 (PENDING RELEASE).",
    ],
  ),

  "DWG-1100": dict(
    drawing_id="DWG-1100", part_number="PUMP-HOUSING-SA-1100",
    drawing_number="DWG-1100", revision="B",
    drawing_title="Pump Housing Sub-Assembly",
    drawing_type="sub_assembly", sheet_count=1,
    drawing_status="released", file_type="pdf",
    scale="1:1", mass="1.84 kg", tolerance="ISO 2768-m", finish="Ra 3.2",
    material="SEE PART DRAWINGS",
    drawn_by="J. SMITH", checked_by="K. JONES", approved_by="M. LEE",
    date="2024-01-10",
    bom=[
      dict(item=1, pn="PUMP-HOUSING-1110",  desc="Pump Housing Body",        qty=1, mat="AL A356-T6"),
      dict(item=2, pn="COVER-PLATE-1120",   desc="Pump Housing Cover Plate", qty=1, mat="AL A356"),
    ],
    notes=[
      "1. ALL DIMENSIONS IN mm UNLESS OTHERWISE STATED.",
      "2. ASSEMBLE COVER PLATE WITH 6× M8 BOLTS. TORQUE: 12 ±1 Nm.",
      "3. APPLY BEAD OF SEALANT (LOCTITE 510) TO MATING FACE BEFORE ASSEMBLY.",
      "4. INSPECT SEALING FACE FOR DAMAGE PRIOR TO ASSEMBLY.",
      "5. DEGREASE ALL MATING SURFACES PER OP-CLEAN-003.",
    ],
  ),

  "DWG-1110": dict(
    drawing_id="DWG-1110", part_number="PUMP-HOUSING-1110",
    drawing_number="DWG-1110", revision="C",
    drawing_title="Pump Housing Body",
    drawing_type="casting_component", sheet_count=2,
    drawing_status="released", file_type="pdf",
    scale="1:1", mass="1.42 kg", tolerance="ISO 2768-m", finish="Ra 3.2",
    material="ALUMINIUM ALLOY A356-T6 PER ASTM B108",
    drawn_by="A. KUMAR", checked_by="K. JONES", approved_by="M. LEE",
    date="2023-11-20",
    dimensions=[
      "OVERALL: 180 ±0.5 × 150 ±0.5 × 95 ±0.5",
      "Ø52.000 +0.030/-0.000 (H7) MAIN BORE",
      "Ø32.0 ±0.1 INLET PORT",
      "Ø25.0 ±0.1 OUTLET PORT",
      "6× M8-6H ON Ø140 BC ±0.2",
      "WALL THICKNESS: 2.5 MIN (SEE SECTION A-A)",
      "DRAFT ANGLE: 2° MIN ALL CAST SURFACES",
      "BORE SURFACE: Ra 1.6 µm",
    ],
    notes=[
      "1. MATERIAL: ALUMINIUM ALLOY A356-T6 PER ASTM B108.",
      "2. CASTING TOLERANCE: ISO 8062 CT9 UNLESS NOTED.",
      "3. MINIMUM WALL THICKNESS: 2.5 mm. SEE SECTION A-A.",
      "4. PRESSURE TIGHT CASTING REQUIRED. IMPREGNATION PERMITTED.",
      "5. HYDROSTATIC TEST: 3 BAR FOR 5 MIN. ZERO LEAKAGE.",
      "6. MACHINE ALL BORES AFTER CASTING.",
      "7. SURFACE FINISH: Ra 3.2 µm UNLESS SPECIFIED.",
      "8. REMOVE ALL BURRS. MAX 0.2 mm CHAMFER ON UNMACHINED EDGES.",
      "9. CHROMATE CONVERSION COATING PER MIL-DTL-5541 TYPE II.",
      "10. HARDNESS: 75-85 HRB (T6 CONDITION). VERIFY PER LOT.",
    ],
  ),

  "DWG-1120": dict(
    drawing_id="DWG-1120", part_number="COVER-PLATE-1120",
    drawing_number="DWG-1120", revision="A",
    drawing_title="Pump Housing Cover Plate",
    drawing_type="casting_component", sheet_count=1,
    drawing_status="released", file_type="pdf",
    scale="1:1", mass="0.42 kg", tolerance="ISO 2768-m", finish="Ra 1.6",
    material="ALUMINIUM ALLOY A356 PER ASTM B108",
    drawn_by="A. KUMAR", checked_by="K. JONES", approved_by="M. LEE",
    date="2023-11-22",
    # intentional imperfection: mixed units in dimensions
    dimensions=[
      "OVERALL: 175 ±0.3 × 145 ±0.3 (6.890 × 5.709 IN REF)",
      "THICKNESS: 12.0 ±0.2 mm (0.472 IN REF)",
      "6× Ø9.5 CLEARANCE HOLES ON Ø140 BC",
      "SEALING FACE FLATNESS: 0.1 mm OVER FULL SURFACE",
      "SEALING GROOVE: 2.5 × 2.0 mm WIDE × DEEP (O-RING SEAT)",
      "SURFACE FINISH SEALING FACE: Ra 0.8 µm",
    ],
    notes=[
      "1. MATERIAL: AL ALLOY A356 PER ASTM B108.",
      "2. Sealing face Ra 0.8 um - machine after casting.",  # inconsistent formatting
      "3. FLATNESS OF SEALING FACE: 0.1 mm TOTAL.",
      "4. ALL THREAD FORMS METRIC COARSE UNLESS NOTED.",
      "5. DIMENSIONS IN mm - inches shown for reference only.",
      "6. CASTING PER ISO 8062 CT9.",
      "7. Remove all burrs; 0.2 max chamfer on cast edges.",  # inconsistent
      "8. ANODISE PER MIL-A-8625 TYPE II, CLASS 1, CLEAR.",
    ],
  ),

  "DWG-1200": dict(
    drawing_id="DWG-1200", part_number="SHAFT-IMPELLER-SA-1200",
    drawing_number="DWG-1200", revision="A",
    drawing_title="Shaft and Impeller Sub-Assembly",
    drawing_type="sub_assembly", sheet_count=1,
    drawing_status="released", file_type="pdf",
    scale="1:1", mass="0.68 kg", tolerance="ISO 2768-f", finish="Ra 1.6",
    material="SEE PART DRAWINGS",
    drawn_by="B. CHEN", checked_by="K. JONES", approved_by="M. LEE",
    date="2024-01-08",
    bom=[
      dict(item=1, pn="DRIVE-SHAFT-1210", desc="Coolant Pump Drive Shaft", qty=1, mat="EN8 STEEL"),
      dict(item=2, pn="IMPELLER-1220",    desc="Coolant Pump Impeller",    qty=1, mat="AL A356-T6"),
    ],
    notes=[
      "1. ALL DIMENSIONS IN mm UNLESS OTHERWISE STATED.",
      "2. PRESS FIT IMPELLER ONTO SHAFT. INTERFERENCE: 0.010-0.025 mm.",
      "3. HEAT IMPELLER TO 80°C MAX FOR ASSEMBLY. DO NOT EXCEED.",
      "4. CHECK IMPELLER RUNOUT AFTER PRESS FIT: MAX 0.05 mm TIR.",
      "5. BALANCE ASSEMBLY TO GRADE G2.5 PER ISO 1940.",
    ],
  ),

  "DWG-1210": dict(
    drawing_id="DWG-1210", part_number="DRIVE-SHAFT-1210",
    drawing_number="DWG-1210", revision="B",
    drawing_title="Coolant Pump Drive Shaft",
    drawing_type="component", sheet_count=1,
    drawing_status="released", file_type="pdf",
    scale="1:1", mass="0.31 kg", tolerance="ISO 2768-f", finish="Ra 0.8",
    material="EN8 STEEL (080M40) PER BS 970",
    drawn_by="B. CHEN", checked_by="K. JONES", approved_by="M. LEE",
    date="2023-12-05",
    dimensions=[
      "OVERALL LENGTH: 125 ±0.1",
      "Ø22.00 h6 (-0.013/0.000) DRIVE END (KEYWAY 6×6×50 PER DIN 6885)",
      "Ø25.00 k5 (+0.009/+0.001) BEARING JOURNAL (BOTH)",
      "Ø18.00 k6 (+0.015/+0.002) IMPELLER SEAT",
      "JOURNAL SURFACE: Ra 0.4 µm",
      "RUNOUT: Ø0.025 mm TIR BETWEEN JOURNALS",
      "SHAFT STRAIGHTNESS: 0.02 mm OVER FULL LENGTH",
    ],
    notes=[
      "1. MATERIAL: EN8 STEEL (080M40) PER BS 970.",
      "2. NORMALISE BEFORE MACHINING.",
      "3. INDUCTION HARDEN BEARING JOURNALS: 52-58 HRC, DEPTH 1.5 mm MIN.",
      "4. GRIND JOURNALS AFTER HEAT TREATMENT.",
      "5. SURFACE FINISH: Ra 0.4 µm ON BEARING SURFACES.",
      "6. ALL RADII: 0.5 mm MIN UNLESS NOTED.",
      "7. THREADS: METRIC COARSE 6g UNLESS NOTED.",
      "8. MAGNETIC PARTICLE INSPECT PER ASTM E1444 AFTER INDUCTION HARDEN.",
      "9. PROTECT MACHINED SURFACES FROM CORROSION.",
    ],
  ),

  "DWG-1220": dict(
    drawing_id="DWG-1220", part_number="IMPELLER-1220",
    drawing_number="DWG-1220", revision="A",
    drawing_title="Coolant Pump Impeller",
    drawing_type="casting_component", sheet_count=1,
    drawing_status="in_work", file_type="png",   # PNG-only: in-work scan
    scale="1:1", mass="0.37 kg", tolerance="ISO 2768-m", finish="Ra 3.2",
    material="ALUMINIUM ALLOY A356-T6 PER ASTM B108",
    drawn_by="A. KUMAR", checked_by="PENDING", approved_by="PENDING",
    date="2024-02-01",
    dimensions=[
      "HUB BORE: Ø18.00 K7 (+0.002/-0.015)",
      "OVERALL DIAMETER: Ø120 ±0.3",
      "OVERALL HEIGHT: 35 ±0.3",
      "NUMBER OF BLADES: 6 EQU. SPACED",
      "BLADE THICKNESS (TIP): 2.0 ±0.2",
    ],
    notes=[
      "1. MATERIAL: AL ALLOY A356-T6 PER ASTM B108.",
      "2. CASTING TOLERANCE ISO 8062 CT9.",
      "3. 6 BLADES EQUALLY SPACED AT 60°.",
      "4. DYNAMIC BALANCE TO G2.5 AFTER MACHINING.",
      "5. HUB BORE MACHINE AFTER CASTING.",
      "*** DRAWING IN WORK - NOT FOR PRODUCTION USE ***",
    ],
    blur=True,   # simulate poor-quality preview
  ),

  "DWG-2000": dict(
    drawing_id="DWG-2000", part_number="CONROD-ASSY-2000",
    drawing_number="DWG-2000", revision="A",
    drawing_title="Connecting Rod Assembly",
    drawing_type="assembly", sheet_count=2,   # sheet 2 missing
    drawing_status="released", file_type="pdf",
    scale="1:1", mass="0.92 kg", tolerance="ISO 2768-f", finish="SEE PARTS",
    material="SEE PART DRAWINGS",
    drawn_by="P. NOVAK", checked_by="T. WALSH", approved_by="M. LEE",
    date="2024-03-01",
    bom=[
      dict(item=1, pn="CONROD-BODY-2100",      desc="Connecting Rod Body",           qty=1, mat="42CrMo4 V"),
      dict(item=2, pn="BIG-END-CAP-2200",      desc="Connecting Rod Big End Cap",    qty=1, mat="42CrMo4 V"),
      dict(item=3, pn="FASTENER-KIT-SA-2300",  desc="Rod Fastener Kit Sub-Assembly", qty=1, mat="SEE PARTS"),
    ],
    notes=[
      "1. ALL DIMENSIONS IN mm UNLESS OTHERWISE STATED.",
      "2. ASSEMBLE PER WORK INSTRUCTION WI-CONROD-005 REV.B.",
      "3. ALIGN MATCH-MARKS ON ROD AND CAP. DO NOT INTERCHANGE.",
      "4. INSTALL ROD BOLTS: TORQUE TO 60 Nm THEN +90° ANGLE.",
      "5. VERIFY BIG END BORE AFTER ASSEMBLY: Ø48.000-48.019 mm.",
      "6. FATIGUE CRITICAL ASSEMBLY. HANDLE WITH CARE.",
      "7. MARK PART NUMBER AND SERIAL NO. ON NON-CRITICAL FACE.",
      "NOTE: SHEET 2 (CLEARANCE CHECK) PENDING - SEE ECR-2024-0317.",
    ],
  ),

  "DWG-2100": dict(
    drawing_id="DWG-2100", part_number="CONROD-BODY-2100",
    drawing_number="DWG-2100", revision="D",
    drawing_title="Connecting Rod Body",
    drawing_type="forging_component", sheet_count=1,
    drawing_status="released", file_type="pdf",
    scale="1:1", mass="0.61 kg", tolerance="ISO 2768-f", finish="Ra 1.6",
    material="STEEL 42CrMo4 (EN 1.7225) PER EN 10083-3",
    drawn_by="P. NOVAK", checked_by="T. WALSH", approved_by="M. LEE",
    date="2023-09-15",
    dimensions=[
      "CENTRE DISTANCE: 145.00 ±0.05",
      "BIG END BORE: Ø48.000 +0.019/0.000 (H6)",
      "SMALL END BORE: Ø22.00 +0.021/0.000 (H7)",
      "ROD WIDTH (BEAM): 28.0 ±0.1",
      "I-SECTION HEIGHT: 18.0 ±0.1",
      "I-SECTION FLANGE WIDTH: 22.0 ±0.1",
      "SECTION A-A WEB THICKNESS: 6.0 ±0.1",
    ],
    notes=[
      "1. MATERIAL: STEEL 42CrMo4 (EN 1.7225) PER EN 10083-3.",
      "2. FORGE BLANK, THEN MACHINE ALL DIMENSIONS SHOWN.",
      "3. QUENCH AND TEMPER: 900-950°C OIL QUENCH, 550-600°C TEMPER.",
      "4. HARDNESS AFTER HT: 280-330 HB. VERIFY PER BATCH.",
      "5. GRAIN FLOW TO FOLLOW ROD AXIS. MACRO ETCH VERIFY ON 1ST OFF.",
      "6. SHOT PEEN ALL SURFACES AFTER MACHINING: INTENSITY 0.20-0.25 mmA.",
      "7. FATIGUE CRITICAL COMPONENT. 100% MAGNETIC PARTICLE INSPECT.",
      "8. BIG END BORE: HONE AFTER ASSEMBLY WITH CAP (SEE DWG-2000).",
      "9. SURFACE FINISH BORES: Ra 0.8 µm.",
      "10. DO NOT GRIND BIG END BORE - HONE ONLY.",
      "11. Match-mark rod and cap before splitting for machining.",  # inconsistent case
    ],
  ),

  "DWG-2200": dict(
    drawing_id="DWG-2200", part_number="BIG-END-CAP-2200",
    drawing_number="DWG-2200", revision="B",
    drawing_title="Connecting Rod Big End Cap",
    drawing_type="forging_component", sheet_count=1,
    drawing_status="released", file_type="pdf",
    scale="1:1", mass="0.18 kg", tolerance="ISO 2768-f", finish="Ra 1.6",
    material="STEEL 42CrMo4 (EN 1.7225) PER EN 10083-3",
    drawn_by="P. NOVAK", checked_by="T. WALSH", approved_by="M. LEE",
    date="2023-09-20",
    dimensions=[
      "BOLT HOLE CENTRES: 45.0 ±0.05",
      "BOLT HOLES: 2× Ø13.5 H7 +0.018/0.000",
      "CAP WIDTH: 28.0 ±0.1",
      "MATING FACE FLATNESS: 0.02 mm",
      "MATING FACE ROUGHNESS: Ra 0.8 µm",
    ],
    notes=[
      "1. MATERIAL: STEEL 42CrMo4 (EN 1.7225) PER EN 10083-3.",
      "2. FORGE BLANK. MACHINE ALL SHOWN DIMS.",
      "3. Q&T SAME BATCH AS MATING ROD BODY DWG-2100.",
      "4. HARDNESS: 280-330 HB.",
      "5. MPI 100% AFTER HEAT TREATMENT.",
      "6. SHOT PEEN ALL SURFACES: 0.20-0.25 mmA.",
      "7. MATCH-MARK WITH MATING ROD BEFORE SEPARATION.",
      "8. HONE BIG END BORE IN ASSEMBLY WITH ROD BODY.",
    ],
    alt_bom_layout=True,  # flag: use non-standard BOM table proportions
  ),

  "DWG-2300": dict(
    drawing_id="DWG-2300", part_number="FASTENER-KIT-SA-2300",
    drawing_number="DWG-2300", revision="A",
    drawing_title="Rod Fastener Kit Sub-Assembly",
    drawing_type="sub_assembly", sheet_count=1,
    drawing_status="released", file_type="pdf",
    scale="2:1", mass="0.08 kg", tolerance="ISO 2768-m", finish="SEE PARTS",
    material="SEE PART DRAWINGS",
    drawn_by="P. NOVAK", checked_by="T. WALSH", approved_by="M. LEE",
    date="2024-03-05",
    bom=[
      dict(item=1, pn="ROD-BOLT-2310", desc="Connecting Rod H/S Bolt M12×1.25", qty=2, mat="GR 12.9 STEEL"),
      dict(item=2, pn="LOCK-NUT-2320", desc="Self-Locking Nut M12×1.25",        qty=2, mat="GR 10 STEEL"),
    ],
    notes=[
      "1. FASTENERS ARE FATIGUE CRITICAL SINGLE-USE ITEMS.",
      "2. DO NOT REUSE ROD BOLTS OR NUTS AFTER REMOVAL.",
      "3. INSTALL BOLTS DRY - NO LUBRICANT UNLESS SPECIFIED.",
      "4. TORQUE SEQUENCE: 60 Nm THEN +90° ANGLE (PER DWG-2000).",
      "5. REPLACE COMPLETE KIT AT EACH ENGINE OVERHAUL.",
    ],
  ),

  "DWG-2310": dict(
    drawing_id="DWG-2310", part_number="ROD-BOLT-2310",
    drawing_number="DWG-2310", revision="A",
    drawing_title="Connecting Rod High-Strength Bolt M12x1.25",
    drawing_type="component", sheet_count=1,
    drawing_status="released", file_type="pdf",
    scale="2:1", mass="0.038 kg", tolerance="ISO 2768-m", finish="Zinc-Ni Plate",
    material="ALLOY STEEL GR 12.9 PER ISO 898-1",
    drawn_by="P. NOVAK", checked_by="T. WALSH", approved_by="M. LEE",
    date="2024-02-10",
    dimensions=[
      "THREAD: M12 × 1.25-6g (FINE PITCH)",
      "SHANK LENGTH: 55.0 +0.0/-0.5",
      "GRIP LENGTH: 36.0 ±0.2",
      "HEAD HEIGHT: 8.0 ±0.2",
      "HEAD WIDTH A/F: 19.0 ±0.1",
      "UNDERHEAD RADIUS: 0.8 ±0.2",
      "THREAD ENGAGEMENT MIN: 18 mm",
    ],
    notes=[
      "1. MATERIAL: ALLOY STEEL GR 12.9 PER ISO 898-1.",
      "2. TENSILE STRENGTH: 1220 MPa MIN.",
      "3. PROOF LOAD: 970 MPa MIN.",
      "4. ZINC-NICKEL PLATE 8-12 µm PER ISO 4042.",
      "5. SINGLE-USE FASTENER. DO NOT REUSE.",
      "6. TIGHTEN PER DWG-2000 ASSEMBLY NOTES.",
      "7. 100% PROOF LOAD TEST BEFORE DISPATCH.",
    ],
  ),

  "DWG-2320": dict(
    drawing_id="DWG-2320", part_number="LOCK-NUT-2320",
    drawing_number="DWG-2320", revision="A",
    drawing_title="Connecting Rod Self-Locking Nut M12x1.25",
    drawing_type="component", sheet_count=1,
    drawing_status="released", file_type="png",   # PNG-only: supplier spec scan
    scale="2:1", mass="0.018 kg", tolerance="ISO 2768-m", finish="Zinc-Ni Plate",
    material="ALLOY STEEL GR 10 PER ISO 7042",
    drawn_by="P. NOVAK", checked_by="T. WALSH", approved_by="M. LEE",
    date="2024-02-10",
    dimensions=[
      "THREAD: M12 × 1.25-6H (FINE PITCH)",
      "WIDTH ACROSS FLATS A/F: 19.0",
      "NUT HEIGHT: 12.0 ±0.2",
      "PREVAILING TORQUE TYPE: ALL-METAL (DEFORMED THREAD)",
      "PREVAILING TORQUE: 8-20 Nm (MIN)",
    ],
    notes=[
      "1. SELF-LOCKING NUT PER ISO 7042 GR 10.",
      "2. PREVAILING TORQUE ALL-METAL TYPE.",
      "3. ZINC-NICKEL PLATE 8-12 µm.",
      "4. SINGLE-USE. DO NOT REUSE.",
      "5. TIGHTEN PER DWG-2000.",
    ],
  ),
}


# ══════════════════════════════════════════════════════════════════════════════
#  HELPER DRAWING PRIMITIVES
# ══════════════════════════════════════════════════════════════════════════════

def p(v: float) -> float:
    """Convert mm → reportlab points."""
    return v * mm


def arrow_head(c: rl_canvas.Canvas, x: float, y: float, angle_deg: float, size_mm: float = 2.0):
    """Draw a filled triangular arrowhead."""
    angle = math.radians(angle_deg)
    s = p(size_mm)
    # tip at (x, y)
    x1 = x - s * math.cos(angle) + (s / 2.5) * math.sin(angle)
    y1 = y - s * math.sin(angle) - (s / 2.5) * math.cos(angle)
    x2 = x - s * math.cos(angle) - (s / 2.5) * math.sin(angle)
    y2 = y - s * math.sin(angle) + (s / 2.5) * math.cos(angle)
    pth = c.beginPath()
    pth.moveTo(x, y)
    pth.lineTo(x1, y1)
    pth.lineTo(x2, y2)
    pth.close()
    c.drawPath(pth, fill=1, stroke=0)


def dim_line_h(c: rl_canvas.Canvas, x1_mm: float, x2_mm: float, y_mm: float,
               text: str, offset_mm: float = 6.0):
    """Horizontal dimension line between two x positions at height y."""
    x1, x2, y = p(x1_mm), p(x2_mm), p(y_mm)
    yo = p(y_mm + offset_mm)
    c.setLineWidth(0.3)
    # extension lines
    c.line(x1, y, x1, yo + p(1))
    c.line(x2, y, x2, yo + p(1))
    # dimension line
    c.line(x1, yo, x2, yo)
    arrow_head(c, x1, yo, 0)
    arrow_head(c, x2, yo, 180)
    # text
    c.setFont(FONTS["normal"], 5.5)
    cx = (x1 + x2) / 2
    c.drawCentredString(cx, yo + p(1.2), text)


def dim_line_v(c: rl_canvas.Canvas, y1_mm: float, y2_mm: float, x_mm: float,
               text: str, offset_mm: float = 6.0):
    """Vertical dimension line."""
    y1, y2, x = p(y1_mm), p(y2_mm), p(x_mm)
    xo = p(x_mm - offset_mm)
    c.setLineWidth(0.3)
    c.line(x, y1, xo - p(1), y1)
    c.line(x, y2, xo - p(1), y2)
    c.line(xo, y1, xo, y2)
    arrow_head(c, xo, y1, 270)
    arrow_head(c, xo, y2, 90)
    c.setFont(FONTS["normal"], 5.5)
    cy = (y1 + y2) / 2
    c.saveState()
    c.translate(xo - p(2.5), cy)
    c.rotate(90)
    c.drawCentredString(0, 0, text)
    c.restoreState()


def centerline_h(c: rl_canvas.Canvas, x1_mm: float, x2_mm: float, y_mm: float):
    """Horizontal centerline (long-dash-dot pattern)."""
    c.setLineWidth(0.25)
    c.setDash([p(6), p(1.5), p(1.5), p(1.5)], 0)
    c.setStrokeColorRGB(0, 0, 0.6)
    c.line(p(x1_mm), p(y_mm), p(x2_mm), p(y_mm))
    c.setDash([])
    c.setStrokeColorRGB(0, 0, 0)


def centerline_v(c: rl_canvas.Canvas, x_mm: float, y1_mm: float, y2_mm: float):
    """Vertical centerline."""
    c.setLineWidth(0.25)
    c.setDash([p(6), p(1.5), p(1.5), p(1.5)], 0)
    c.setStrokeColorRGB(0, 0, 0.6)
    c.line(p(x_mm), p(y1_mm), p(x_mm), p(y2_mm))
    c.setDash([])
    c.setStrokeColorRGB(0, 0, 0)


def hidden_line_h(c: rl_canvas.Canvas, x1_mm: float, x2_mm: float, y_mm: float):
    c.setLineWidth(0.3)
    c.setDash([p(3), p(1.5)], 0)
    c.line(p(x1_mm), p(y_mm), p(x2_mm), p(y_mm))
    c.setDash([])


def section_hatch(c: rl_canvas.Canvas, x_mm: float, y_mm: float,
                  w_mm: float, h_mm: float, spacing_mm: float = 3.5, angle: int = 45):
    """Fill a rectangle with section-hatch lines."""
    c.setLineWidth(0.25)
    c.setStrokeColorRGB(0.3, 0.3, 0.3)
    x0, y0 = p(x_mm), p(y_mm)
    x1b, y1b = p(x_mm + w_mm), p(y_mm + h_mm)
    sp = p(spacing_mm)
    diag = math.hypot(x1b - x0, y1b - y0)
    start = -diag
    while start <= diag + (y1b - y0):
        xa, ya = x0, y0 + start
        xb, yb = x0 + (y1b - y0 - start), y1b
        # clip to rectangle
        c.saveState()
        pth = c.beginPath()
        pth.rect(x0, y0, x1b - x0, y1b - y0)
        c.clipPath(pth, stroke=0, fill=0)
        c.line(xa, ya, xb, yb)
        c.restoreState()
        start += sp
    c.setStrokeColorRGB(0, 0, 0)


def balloon(c: rl_canvas.Canvas, cx_mm: float, cy_mm: float, r_mm: float,
            text: str, leader_to: Optional[tuple] = None):
    """Draw a round assembly balloon with item number."""
    cx, cy, r = p(cx_mm), p(cy_mm), p(r_mm)
    c.setLineWidth(0.4)
    c.circle(cx, cy, r, fill=1)
    c.setFillColorRGB(1, 1, 1)
    c.circle(cx, cy, r, fill=1)
    c.setFillColorRGB(0, 0, 0)
    c.setStrokeColorRGB(0, 0, 0)
    c.circle(cx, cy, r, fill=0)
    c.setFont(FONTS["bold"], 7)
    c.drawCentredString(cx, cy - p(1.8), text)
    if leader_to:
        tx, ty = p(leader_to[0]), p(leader_to[1])
        # line from balloon edge to target
        angle = math.atan2(ty - cy, tx - cx)
        ex = cx + r * math.cos(angle)
        ey = cy + r * math.sin(angle)
        c.setLineWidth(0.3)
        c.line(ex, ey, tx, ty)


# ══════════════════════════════════════════════════════════════════════════════
#  PDF GENERATOR
# ══════════════════════════════════════════════════════════════════════════════

class PDFGenerator:
    """Generates A3-landscape engineering drawing PDFs using reportlab."""

    def generate(self, spec: Dict, pdf_path: Path):
        c = rl_canvas.Canvas(str(pdf_path), pagesize=(p(PW), p(PH)))
        self._page(c, spec, page_num=1)
        c.showPage()
        c.save()

    # ── page skeleton ────────────────────────────────────────────────────────

    def _page(self, c, spec, page_num=1):
        self._border_and_zones(c)
        self._title_block(c, spec, page_num)
        dtype = spec.get("drawing_type", "component")
        if dtype in ("assembly", "sub_assembly"):
            self._assembly_view(c, spec)
            self._bom_table(c, spec)
            self._notes_block(c, spec, x0=DA_X0, y_top=DA_Y0 + 30,
                              x1=DA_X0 + 80, max_lines=12)
        else:
            self._component_view(c, spec)
            self._notes_block(c, spec, x0=290, y_top=DA_Y1 - 2,
                              x1=DA_X1, max_lines=14)
            self._dim_block(c, spec)

    # ── border + zones ───────────────────────────────────────────────────────

    def _border_and_zones(self, c):
        c.setLineWidth(0.5)
        c.setStrokeColorRGB(0, 0, 0)
        # outer border
        c.rect(p(BDR), p(BDR), p(PW - 2 * BDR), p(PH - 2 * BDR))
        # inner border (2 mm inside)
        c.setLineWidth(0.8)
        c.rect(p(BDR + 2), p(BDR + 2), p(PW - 2 * (BDR + 2)), p(PH - 2 * (BDR + 2)))

        c.setLineWidth(0.25)
        # horizontal zone ticks (A-D rows, 4 equal bands)
        band_h = (PH - 2 * BDR) / 4
        for i in range(1, 4):
            yy = p(BDR + i * band_h)
            c.line(p(BDR), yy, p(BDR + 3), yy)
            c.line(p(PW - BDR - 3), yy, p(PW - BDR), yy)
        labels_row = ["D", "C", "B", "A"]
        c.setFont(FONTS["normal"], 5)
        for i, lbl in enumerate(labels_row):
            yy = p(BDR + (i + 0.5) * band_h)
            c.drawCentredString(p(BDR + 1.5), yy, lbl)
            c.drawCentredString(p(PW - BDR - 1.5), yy, lbl)

        # vertical zone ticks (1-8 cols)
        band_w = (PW - 2 * BDR) / 8
        for i in range(1, 8):
            xx = p(BDR + i * band_w)
            c.line(xx, p(BDR), xx, p(BDR + 3))
            c.line(xx, p(PH - BDR - 3), xx, p(PH - BDR))
        c.setFont(FONTS["normal"], 5)
        for i in range(8):
            xx = p(BDR + (i + 0.5) * band_w)
            c.drawCentredString(xx, p(PH - BDR - 1.5), str(i + 1))
            c.drawCentredString(xx, p(BDR + 0.8), str(i + 1))

    # ── title block ──────────────────────────────────────────────────────────

    def _title_block(self, c, spec, page_num):
        x0, y0 = p(BDR + 2), p(BDR + 2)
        w = p(PW - 2 * (BDR + 2))
        h = p(TB_H - 4)

        c.setLineWidth(0.4)
        c.rect(x0, y0, w, h)

        # vertical split: left 60% | right 40%
        split = 0.60
        xs = x0 + w * split

        # ── left block ──────────────────────────────────────────────────────
        row_h = h / 4
        # row borders
        for i in range(1, 4):
            yy = y0 + i * row_h
            c.line(x0, yy, xs, yy)

        # Company
        c.setFont(FONTS["bold"], 9)
        c.drawString(x0 + p(2), y0 + 3 * row_h + p(3), "AutoPLM DEMO  |  Edify-AI")
        c.setFont(FONTS["normal"], 6)
        c.drawString(x0 + p(2), y0 + 3 * row_h + p(0.2), "ENGINEERING DRAWING — FOR DEMONSTRATION ONLY")

        # Title
        title = spec.get("drawing_title", "")
        c.setFont(FONTS["bold"], 8)
        c.drawString(x0 + p(2), y0 + 2 * row_h + p(3.5), title[:55])
        c.setFont(FONTS["normal"], 6)
        c.drawString(x0 + p(2), y0 + 2 * row_h + p(0.5), f"PART NO: {spec['part_number']}")

        # Material / tolerance
        c.setFont(FONTS["normal"], 5.5)
        c.drawString(x0 + p(2), y0 + row_h + p(3.5), f"MATERIAL: {spec.get('material','SEE NOTES')[:50]}")
        c.drawString(x0 + p(2), y0 + row_h + p(0.5), f"TOLERANCE: {spec.get('tolerance','ISO 2768-m')}")

        # Finish / mass
        c.drawString(x0 + p(2), y0 + p(3.5), f"SURFACE FINISH: {spec.get('finish','Ra 3.2')}  |  MASS: {spec.get('mass','—')}")
        c.drawString(x0 + p(2), y0 + p(0.5), "ALL DIMENSIONS IN MILLIMETRES UNLESS STATED")

        # ── right block ─────────────────────────────────────────────────────
        right_w = w - w * split
        col_w = right_w / 3
        c.line(xs, y0, xs, y0 + h)

        headers = ["DRAWN", "CHECKED", "APPROVED"]
        persons = [spec.get("drawn_by","—"), spec.get("checked_by","—"), spec.get("approved_by","—")]
        date_val = spec.get("date", "—")

        sub_row = h / 3
        for i, (hdr, per) in enumerate(zip(headers, persons)):
            yy = y0 + (2 - i) * sub_row
            # vertical divider between person+date columns
            c.line(xs + col_w, yy, xs + col_w, yy + sub_row)
            c.line(xs + 2 * col_w, yy, xs + 2 * col_w, yy + sub_row)
            c.line(xs, yy, xs + right_w, yy)
            c.setFont(FONTS["bold"], 5.5)
            c.drawString(xs + p(1), yy + sub_row - p(3), hdr)
            c.setFont(FONTS["normal"], 6)
            c.drawString(xs + col_w + p(1), yy + sub_row - p(3.5), per[:12])
            c.drawString(xs + 2 * col_w + p(1), yy + sub_row - p(3.5), date_val)

        # DWG NO + REV box below
        box_h = h / 4
        c.line(xs, y0 + h - box_h, xs + right_w, y0 + h - box_h)
        c.line(xs + right_w / 2, y0 + h - box_h, xs + right_w / 2, y0 + h)
        c.setFont(FONTS["bold"], 6)
        c.drawString(xs + p(1), y0 + h - p(4), f"DWG: {spec['drawing_number']}")
        c.drawString(xs + right_w / 2 + p(1), y0 + h - p(4),
                     f"REV: {spec['revision']}   SHT: {page_num}/{spec.get('sheet_count',1)}")
        c.setFont(FONTS["bold"], 5)
        c.drawString(xs + p(1), y0 + h - p(8), f"SCALE: {spec.get('scale','1:1')}")
        c.drawString(xs + right_w / 2 + p(1), y0 + h - p(8),
                     f"STATUS: {spec.get('drawing_status','—').upper()}")

    # ── BOM table (assemblies) ───────────────────────────────────────────────

    def _bom_table(self, c, spec, alt_layout=False):
        bom = spec.get("bom", [])
        if not bom:
            return

        alt = spec.get("alt_bom_layout", False)
        # column widths vary for alt_layout (realistic imperfection)
        if alt:
            cols = [10, 52, 68, 10]
        else:
            cols = [10, 60, 60, 10]
        total_w = sum(cols)

        x0 = DA_X1 - total_w
        row_h = 7.5
        header_h = 8.0
        n_rows = len(bom)
        table_h = header_h + n_rows * row_h + row_h  # +1 for title row

        y_top = DA_Y1 - 2
        y0 = y_top - table_h

        c.setLineWidth(0.35)

        # outer box
        c.rect(p(x0), p(y0), p(total_w), p(table_h))

        # title row
        c.setFillColorRGB(0.85, 0.85, 0.85)
        c.rect(p(x0), p(y0 + n_rows * row_h + header_h), p(total_w), p(row_h), fill=1)
        c.setFillColorRGB(0, 0, 0)
        c.setFont(FONTS["bold"], 6.5)
        c.drawCentredString(p(x0 + total_w / 2),
                            p(y0 + n_rows * row_h + header_h + 1.8),
                            "BILL OF MATERIALS")

        # header row
        c.setFillColorRGB(0.92, 0.92, 0.92)
        c.rect(p(x0), p(y0 + n_rows * row_h), p(total_w), p(header_h), fill=1)
        c.setFillColorRGB(0, 0, 0)
        hdrs = ["ITEM", "PART NUMBER", "DESCRIPTION", "QTY"]
        xc = x0
        for col_w, hdr in zip(cols, hdrs):
            c.setFont(FONTS["bold"], 5.5)
            c.drawCentredString(p(xc + col_w / 2), p(y0 + n_rows * row_h + 2), hdr)
            xc += col_w

        # column lines
        xc = x0
        for col_w in cols[:-1]:
            xc += col_w
            c.line(p(xc), p(y0), p(xc), p(y0 + n_rows * row_h + header_h + row_h))

        # data rows
        for idx, row in enumerate(reversed(bom)):
            ry = y0 + idx * row_h
            # zebra stripe
            if idx % 2 == 0:
                c.setFillColorRGB(0.97, 0.97, 0.97)
                c.rect(p(x0), p(ry), p(total_w), p(row_h), fill=1)
                c.setFillColorRGB(0, 0, 0)
            c.line(p(x0), p(ry), p(x0 + total_w), p(ry))

            vals = [str(row["item"]), row["pn"], row["desc"][:30], str(row["qty"])]
            xc = x0
            for col_w, val in zip(cols, vals):
                c.setFont(FONTS["normal"], 5.5)
                c.drawString(p(xc + 1), p(ry + 2), val)
                xc += col_w

    # ── notes block ─────────────────────────────────────────────────────────

    def _notes_block(self, c, spec, x0, y_top, x1, max_lines=12):
        notes = spec.get("notes", [])
        if not notes:
            return
        w = x1 - x0
        c.setLineWidth(0.35)
        c.setFont(FONTS["bold"], 6.5)
        c.drawString(p(x0 + 1), p(y_top - 6), "NOTES:")
        c.line(p(x0), p(y_top - 7), p(x1), p(y_top - 7))

        c.setFont(FONTS["normal"], 5.0)
        line_h = 5.2
        y = y_top - 7 - line_h
        for note in notes[:max_lines]:
            # wrap long notes
            words = note.split()
            line = ""
            for w_word in words:
                test = (line + " " + w_word).strip()
                if len(test) * 2.8 > p(w):  # rough char width
                    c.drawString(p(x0 + 1), p(y), line)
                    y -= line_h
                    line = w_word
                else:
                    line = test
            if line:
                c.drawString(p(x0 + 1), p(y), line)
                y -= line_h

        # box around notes
        c.rect(p(x0), p(y - 1), p(x1 - x0), p(y_top - 6 - (y - 1)))

    # ── dim block (components) ───────────────────────────────────────────────

    def _dim_block(self, c, spec):
        dims = spec.get("dimensions", [])
        if not dims:
            return
        x0, x1 = 290, DA_X1
        y_top = DA_Y0 + len(spec.get("notes", [])) * 5.5 + 20
        if y_top > DA_Y1 - 55:
            y_top = DA_Y1 - 55

        c.setFont(FONTS["bold"], 6.5)
        c.drawString(p(x0 + 1), p(y_top - 4), "KEY DIMENSIONS:")
        c.line(p(x0), p(y_top - 5), p(x1), p(y_top - 5))
        c.setFont(FONTS["normal"], 5.0)
        y = y_top - 10
        for dim in dims:
            c.drawString(p(x0 + 1), p(y), dim[:42])
            y -= 5.2

    # ── assembly schematic ───────────────────────────────────────────────────

    def _assembly_view(self, c, spec):
        pn = spec["part_number"]
        # determine which assembly view to draw
        if "PUMP-ASSY" in pn:
            self._view_pump_assembly(c, spec)
        elif "PUMP-HOUSING-SA" in pn:
            self._view_housing_sa(c, spec)
        elif "SHAFT-IMPELLER-SA" in pn:
            self._view_shaft_sa(c, spec)
        elif "CONROD-ASSY" in pn:
            self._view_conrod_assembly(c, spec)
        elif "FASTENER-KIT-SA" in pn:
            self._view_fastener_sa(c, spec)
        else:
            self._view_generic_assembly(c, spec)

    # ── component view dispatcher ────────────────────────────────────────────

    def _component_view(self, c, spec):
        pn = spec["part_number"]
        dispatch = {
            "PUMP-HOUSING-1110":  self._view_pump_housing,
            "COVER-PLATE-1120":   self._view_cover_plate,
            "DRIVE-SHAFT-1210":   self._view_drive_shaft,
            "IMPELLER-1220":      self._view_impeller,
            "CONROD-BODY-2100":   self._view_conrod_body,
            "BIG-END-CAP-2200":   self._view_big_end_cap,
            "ROD-BOLT-2310":      self._view_rod_bolt,
            "LOCK-NUT-2320":      self._view_lock_nut,
        }
        fn = dispatch.get(pn, self._view_generic_component)
        fn(c, spec)

    # ════════════════════════════════════════════════════════════════════════
    #  ASSEMBLY VIEW IMPLEMENTATIONS
    # ════════════════════════════════════════════════════════════════════════

    def _view_pump_assembly(self, c, spec):
        """Simplified pump assembly schematic with balloons."""
        # area: x=[12,200] y=[DA_Y0+2, DA_Y1-4]
        cx, cy = 110, (DA_Y0 + DA_Y1) / 2

        # housing body outline
        c.setLineWidth(0.7)
        c.rect(p(40), p(cy - 35), p(140), p(70))

        # main bore circle
        c.setLineWidth(0.5)
        c.circle(p(110), p(cy), p(26))

        # inlet port (left)
        c.rect(p(12), p(cy - 8), p(28), p(16))
        c.setFont(FONTS["normal"], 5)
        c.drawCentredString(p(26), p(cy + 10), "Ø32 INLET")

        # outlet port (top)
        c.rect(p(97), p(cy + 35), p(26), p(22))
        c.setFont(FONTS["normal"], 5)
        c.drawString(p(124), p(cy + 43), "Ø25 OUTLET")

        # impeller inside
        c.setLineWidth(0.3)
        c.setDash([p(2), p(1)], 0)
        c.circle(p(110), p(cy), p(20))
        c.setDash([])

        # centerlines
        centerline_h(c, 10, 200, cy)
        centerline_v(c, cx, DA_Y0 + 5, DA_Y1 - 5)

        # shaft (right side)
        c.setLineWidth(0.6)
        c.rect(p(180), p(cy - 5), p(25), p(10))
        c.drawString(p(185), p(cy + 7), "SHAFT")

        # overall dimension
        dim_line_h(c, 40, 180, DA_Y0 + 10, "180", offset_mm=5)
        dim_line_v(c, cy - 35, cy + 35, 38, "70", offset_mm=5)

        # balloons
        bom = spec.get("bom", [])
        positions = [(75, cy + 42), (165, cy - 30)]
        for i, (bx, by) in enumerate(positions[:len(bom)]):
            balloon(c, bx, by, 5, str(i + 1), leader_to=(bx + 10, by - 5))

        # section reference
        c.setFont(FONTS["bold"], 6)
        c.drawString(p(12), p(DA_Y1 - 10), "SCALE: 1:2   VIEW FROM DRIVE-END")
        c.setFont(FONTS["italic"], 5.5)
        c.drawString(p(12), p(DA_Y1 - 16),
                     "(Assembly shown schematically — refer to part drawings for detailed geometry)")

    def _view_housing_sa(self, c, spec):
        cx, cy = 110, (DA_Y0 + DA_Y1) / 2
        c.setLineWidth(0.7)
        c.rect(p(35), p(cy - 30), p(120), p(60))
        c.setLineWidth(0.5)
        c.circle(p(cx), p(cy), p(22))
        # cover plate (right side, thin)
        c.rect(p(155), p(cy - 30), p(12), p(60))
        c.setFont(FONTS["normal"], 5.5)
        c.drawString(p(40), p(cy + 32), "HOUSING BODY (ITEM 1)")
        c.drawString(p(157), p(cy + 32), "COVER\nPLATE")
        centerline_h(c, 30, 180, cy)
        dim_line_h(c, 35, 167, DA_Y0 + 10, "175  REF", offset_mm=4)
        balloon(c, 80, cy + 38, 5, "1", leader_to=(95, cy + 26))
        balloon(c, 163, cy + 38, 5, "2", leader_to=(161, cy + 25))

    def _view_shaft_sa(self, c, spec):
        cx, cy = 120, (DA_Y0 + DA_Y1) / 2
        # shaft
        c.setLineWidth(0.7)
        c.rect(p(30), p(cy - 5), p(90), p(10))
        # impeller disc
        c.circle(p(30), p(cy), p(30))
        c.setLineWidth(0.4)
        # blades
        for angle_deg in range(0, 360, 60):
            angle = math.radians(angle_deg)
            ix = 30 + 28 * math.cos(angle)
            iy = cy + 28 * math.sin(angle)
            c.line(p(30), p(cy), p(ix), p(iy))
        c.setFont(FONTS["normal"], 5.5)
        c.drawString(p(28), p(cy + 33), "IMPELLER (ITEM 2)")
        c.drawString(p(80), p(cy + 12), "DRIVE SHAFT (ITEM 1)")
        centerline_h(c, 0, 130, cy)
        balloon(c, 55, cy + 38, 5, "1", leader_to=(70, cy + 6))
        balloon(c, 30, cy - 38, 5, "2", leader_to=(30, cy - 30))

    def _view_conrod_assembly(self, c, spec):
        # simplified conrod side view
        cx, cy = 120, (DA_Y0 + DA_Y1) / 2
        c.setLineWidth(0.7)
        # rod body (I-section in side view looks like rectangle with circles)
        # big end
        c.circle(p(50), p(cy), p(24))
        c.circle(p(50), p(cy), p(18))  # bore
        # rod shank
        c.rect(p(72), p(cy - 8), p(80), p(16))
        # small end
        c.circle(p(170), p(cy), p(11))
        c.circle(p(170), p(cy), p(7))  # bore
        # bolt holes in big end cap
        c.setLineWidth(0.3)
        c.circle(p(35), p(cy + 22), p(4))
        c.circle(p(35), p(cy - 22), p(4))
        c.setFont(FONTS["normal"], 5.5)
        c.drawString(p(30), p(cy - 38), "BIG END BORE Ø48 H6")
        c.drawString(p(155), p(cy + 15), "SMALL ENDØ22 H7")
        dim_line_h(c, 26, 179, DA_Y0 + 8, "145 CTR-CTR", offset_mm=5)
        centerline_h(c, 15, 200, cy)
        balloon(c, 50, cy + 40, 5, "1", leader_to=(50, cy + 24))
        balloon(c, 50, cy - 40, 5, "2", leader_to=(42, cy - 24))
        balloon(c, 35, cy - 52, 5, "3", leader_to=(35, cy - 26))

    def _view_fastener_sa(self, c, spec):
        cy = (DA_Y0 + DA_Y1) / 2
        # bolt
        c.setLineWidth(0.7)
        c.rect(p(30), p(cy + 5), p(70), p(10))  # shank
        c.rect(p(18), p(cy + 5), p(12), p(15))  # head
        # thread lines
        c.setLineWidth(0.3)
        c.setDash([p(1.5), p(1)], 0)
        c.line(p(30), p(cy + 5), p(100), p(cy + 5))
        c.line(p(30), p(cy + 15), p(100), p(cy + 15))
        c.setDash([])
        # nut
        c.setLineWidth(0.7)
        c.rect(p(78), p(cy - 20), p(15), p(12))
        c.setFont(FONTS["normal"], 6)
        c.drawString(p(105), p(cy + 10), "ROD BOLT M12×1.25 GR 12.9 (ITEM 1, QTY 2)")
        c.drawString(p(100), p(cy - 15), "LOCK NUT M12×1.25 (ITEM 2, QTY 2)")
        balloon(c, 58, cy + 30, 5, "1", leader_to=(58, cy + 15))
        balloon(c, 85, cy - 30, 5, "2", leader_to=(85, cy - 20))

    def _view_generic_assembly(self, c, spec):
        cx, cy = 120, (DA_Y0 + DA_Y1) / 2
        c.setLineWidth(0.6)
        c.rect(p(40), p(cy - 30), p(160), p(60))
        c.setFont(FONTS["normal"], 7)
        c.drawCentredString(p(cx), p(cy), spec.get("drawing_title", "ASSEMBLY"))
        bom = spec.get("bom", [])
        for i, item in enumerate(bom):
            bx, by = 80 + i * 40, cy + 35
            balloon(c, bx, by, 5, str(i + 1), leader_to=(bx, cy + 30))

    # ════════════════════════════════════════════════════════════════════════
    #  COMPONENT VIEW IMPLEMENTATIONS
    # ════════════════════════════════════════════════════════════════════════

    def _view_pump_housing(self, c, spec):
        """Pump housing: front view + section A-A."""
        cx, cy = 95, (DA_Y0 + DA_Y1) / 2 + 10

        # ── FRONT VIEW ──────────────────────────────────────────────────────
        c.setFont(FONTS["bold"], 6)
        c.drawCentredString(p(cx), p(DA_Y1 - 6), "FRONT VIEW")

        c.setLineWidth(0.7)
        c.rect(p(35), p(cy - 35), p(120), p(70))  # outer housing

        # main bore
        c.setLineWidth(0.5)
        c.circle(p(cx), p(cy), p(26))

        # inlet boss (left)
        c.rect(p(12), p(cy - 9), p(23), p(18))

        # outlet boss (top)
        c.rect(p(cx - 9), p(cy + 35), p(18), p(18))

        # 6× bolt holes on PCD
        for i in range(6):
            angle = math.radians(i * 60 + 30)
            bx = cx + 40 * math.cos(angle)
            by = cy + 40 * math.sin(angle)
            c.setLineWidth(0.4)
            c.circle(p(bx), p(by), p(3))

        # bolt PCD circle (hidden)
        c.setLineWidth(0.3)
        c.setDash([p(3), p(1.5)], 0)
        c.circle(p(cx), p(cy), p(40))
        c.setDash([])

        # centerlines
        centerline_h(c, 10, 175, cy)
        centerline_v(c, cx, DA_Y0 + 5, DA_Y1 - 10)

        # section arrows
        c.setFont(FONTS["bold"], 7)
        c.drawString(p(36), p(cy - 50), "A")
        c.drawString(p(153), p(cy - 50), "A")
        c.setLineWidth(0.5)
        c.line(p(37), p(cy - 47), p(153), p(cy - 47))
        arrow_head(c, p(40), p(cy - 47), 0)
        arrow_head(c, p(150), p(cy - 47), 180)

        # dimensions
        c.setLineWidth(0.3)
        dim_line_h(c, 35, 155, DA_Y0 + 5, "180 ±0.5", offset_mm=4)
        dim_line_v(c, cy - 35, cy + 35, 33, "70 ±0.5", offset_mm=4)
        dim_line_h(c, cx - 26, cx + 26, cy + 40, "Ø52 H7", offset_mm=3)
        dim_line_h(c, 12, 35, cy + 5, "Ø32", offset_mm=3)

        # ── SECTION A-A ──────────────────────────────────────────────────────
        sx = 195
        c.setFont(FONTS["bold"], 6)
        c.drawCentredString(p(sx + 20), p(DA_Y1 - 6), "SECTION A-A")

        c.setLineWidth(0.7)
        # outer wall
        c.rect(p(sx), p(cy - 35), p(40), p(70))
        # inner cavity (section hatch on walls)
        section_hatch(c, sx, cy - 35, 6, 70)            # left wall
        section_hatch(c, sx + 34, cy - 35, 6, 70)       # right wall
        section_hatch(c, sx, cy - 35, 40, 5)            # bottom wall
        section_hatch(c, sx, cy + 30, 40, 5)            # top wall

        # wall thickness annotation
        c.setFont(FONTS["normal"], 5)
        c.drawString(p(sx + 42), p(cy + 5), "2.5 MIN")
        c.line(p(sx + 41), p(cy + 6), p(sx + 34), p(cy + 6))

        # bore detail
        c.setLineWidth(0.4)
        hidden_line_h(c, sx + 6, sx + 34, cy - 26)
        hidden_line_h(c, sx + 6, sx + 34, cy + 26)
        c.drawString(p(sx + 42), p(cy + 22), "Ø52.000")
        c.drawString(p(sx + 42), p(cy + 17), "+0.030")
        c.drawString(p(sx + 42), p(cy + 12), "-0.000 (H7)")

        # section A-A label
        c.setFont(FONTS["italic"], 6)
        c.drawCentredString(p(sx + 20), p(DA_Y0 + 8), "SECTION A-A")

    def _view_cover_plate(self, c, spec):
        cx, cy = 100, (DA_Y0 + DA_Y1) / 2 + 15

        # FRONT VIEW
        c.setFont(FONTS["bold"], 6)
        c.drawCentredString(p(cx), p(DA_Y1 - 6), "FRONT VIEW")
        c.setLineWidth(0.7)
        c.rect(p(25), p(cy - 38), p(150), p(76))  # plate outline

        # sealing groove (dashed)
        c.setLineWidth(0.4)
        c.setDash([p(2.5), p(1.5)], 0)
        c.rect(p(35), p(cy - 28), p(130), p(56))
        c.setDash([])

        # 6× clearance holes
        for i in range(6):
            angle = math.radians(i * 60 + 30)
            bx = cx + 46 * math.cos(angle)
            by = cy + 46 * math.sin(angle)
            c.setLineWidth(0.4)
            c.circle(p(bx), p(by), p(4.75))

        centerline_h(c, 20, 185, cy)
        centerline_v(c, cx, DA_Y0 + 5, DA_Y1 - 10)

        # SIDE VIEW (edge view)
        sx = 215
        c.setFont(FONTS["bold"], 6)
        c.drawCentredString(p(sx + 10), p(DA_Y1 - 6), "SIDE VIEW")
        c.setLineWidth(0.7)
        c.rect(p(sx), p(cy - 38), p(20), p(76))
        section_hatch(c, sx, cy - 38, 20, 76, spacing_mm=3)

        # mixed units note box
        c.setFillColorRGB(1.0, 0.95, 0.8)
        c.rect(p(sx + 28), p(cy + 10), p(55), p(22), fill=1)
        c.setFillColorRGB(0, 0, 0)
        c.setFont(FONTS["bold"], 5.5)
        c.drawString(p(sx + 30), p(cy + 29), "NOTE: DUAL DIMS")
        c.setFont(FONTS["normal"], 5)
        c.drawString(p(sx + 30), p(cy + 23), "175 mm / 6.890\"")
        c.drawString(p(sx + 30), p(cy + 17), "mm PRIMARY - in REF")

        # dimensions
        dim_line_h(c, 25, 175, DA_Y0 + 5, "175 (6.890 REF)", offset_mm=4)
        dim_line_v(c, cy - 38, cy + 38, 23, "76 ±0.3", offset_mm=5)
        dim_line_h(c, sx, sx + 20, DA_Y0 + 5, "12.0 ±0.2", offset_mm=4)

    def _view_drive_shaft(self, c, spec):
        cy = (DA_Y0 + DA_Y1) / 2 + 15
        x0 = 25

        c.setFont(FONTS["bold"], 6)
        c.drawCentredString(p(x0 + 100), p(DA_Y1 - 6), "FRONT VIEW (FULL SECTION)")

        # shaft profile — stepped diameters
        segments = [
            (x0,      20,  "DRIVE END\nØ22 h6"),
            (x0+20,   25,  "BRGØ25 k5"),
            (x0+45,   70,  "SHAFT BODY Ø22"),
            (x0+115,  25,  "BRGØ25 k5"),
            (x0+140,  20,  "IMPØ18 k6"),
        ]
        c.setLineWidth(0.7)
        xp = x0
        for seg_x, seg_len, label in segments:
            d_half = {"DRIVE END\nØ22 h6": 11, "BRGØ25 k5": 12.5,
                      "SHAFT BODY Ø22": 11, "IMPØ18 k6": 9}.get(label, 12.5)
            c.rect(p(xp), p(cy - d_half), p(seg_len), p(d_half * 2))
            xp += seg_len

        # keyway (drive end)
        c.setLineWidth(0.4)
        c.rect(p(x0 + 5), p(cy + 8), p(14), p(4))  # keyway slot

        # centerline
        centerline_h(c, x0 - 3, x0 + 163, cy)

        # section hatch (solid shaft)
        for seg_x, seg_len, label in segments:
            section_hatch(c, seg_x, cy - 12, seg_len, 24, spacing_mm=2.5)

        # dimension lines
        dim_line_h(c, x0, x0 + 160, DA_Y0 + 5, "125 ±0.1 OVERALL", offset_mm=4)
        dim_line_h(c, x0, x0 + 20, cy + 20, "Ø22 h6", offset_mm=3)
        dim_line_h(c, x0 + 20, x0 + 45, cy + 18, "Ø25 k5", offset_mm=3)
        dim_line_h(c, x0 + 140, x0 + 160, cy + 18, "Ø18 k6", offset_mm=3)

        # END VIEW
        ex = 230
        c.setFont(FONTS["bold"], 6)
        c.drawCentredString(p(ex), p(DA_Y1 - 6), "END VIEW")
        c.setLineWidth(0.6)
        c.circle(p(ex), p(cy), p(11))   # shaft circle
        c.circle(p(ex), p(cy), p(3))    # inner
        # keyway slot
        c.rect(p(ex - 3), p(cy + 8), p(6), p(5))
        centerline_h(c, ex - 15, ex + 15, cy)
        centerline_v(c, ex, cy - 15, cy + 15)
        c.setFont(FONTS["normal"], 5)
        c.drawString(p(ex + 12), p(cy + 5), "KEYWAY")
        c.drawString(p(ex + 12), p(cy + 1), "6×6×50")

    def _view_impeller(self, c, spec):
        cx, cy = 110, (DA_Y0 + DA_Y1) / 2 + 10

        c.setFont(FONTS["bold"], 6)
        c.drawCentredString(p(cx), p(DA_Y1 - 6), "FRONT VIEW")

        # outer circle
        c.setLineWidth(0.7)
        c.circle(p(cx), p(cy), p(60))

        # hub circle
        c.circle(p(cx), p(cy), p(12))

        # 6 blades
        c.setLineWidth(0.5)
        for i in range(6):
            angle = math.radians(i * 60)
            bx1 = cx + 12 * math.cos(angle)
            by1 = cy + 12 * math.sin(angle)
            # blade sweeps outward with backward curve
            blade_angle = angle + math.radians(15)
            bx2 = cx + 55 * math.cos(blade_angle)
            by2 = cy + 55 * math.sin(blade_angle)
            c.line(p(bx1), p(by1), p(bx2), p(by2))

        # bore hole
        c.setLineWidth(0.6)
        c.circle(p(cx), p(cy), p(9))

        centerline_h(c, cx - 65, cx + 65, cy)
        centerline_v(c, cx, cy - 65, cy + 65)

        # in-work watermark
        c.setFont(FONTS["bold"], 14)
        c.setFillColorRGB(0.8, 0.2, 0.2)
        c.saveState()
        c.translate(p(cx), p(cy))
        c.rotate(30)
        c.drawCentredString(0, 0, "PRELIMINARY — DO NOT USE FOR PRODUCTION")
        c.restoreState()
        c.setFillColorRGB(0, 0, 0)

        dim_line_h(c, cx - 60, cx + 60, DA_Y0 + 5, "Ø120 ±0.3", offset_mm=4)
        dim_line_h(c, cx - 9, cx + 9, cy + 18, "Ø18 K7", offset_mm=3)
        c.setFont(FONTS["normal"], 5)
        c.drawString(p(cx + 63), p(cy), "6 BLADES")
        c.drawString(p(cx + 63), p(cy - 5), "EQU.SPACED")

    def _view_conrod_body(self, c, spec):
        cy = (DA_Y0 + DA_Y1) / 2 + 10
        bx, sx = 60, 190  # big-end x, small-end x

        c.setFont(FONTS["bold"], 6)
        c.drawCentredString(p(125), p(DA_Y1 - 6), "FRONT VIEW")

        # big end bore
        c.setLineWidth(0.7)
        c.circle(p(bx), p(cy), p(24))
        c.setLineWidth(0.5)
        c.circle(p(bx), p(cy), p(18))  # H6 bore

        # small end bore
        c.setLineWidth(0.7)
        c.circle(p(sx), p(cy), p(11))
        c.setLineWidth(0.5)
        c.circle(p(sx), p(cy), p(7))  # H7 bore

        # shank (I-section side view = rectangle with taper)
        c.setLineWidth(0.7)
        c.rect(p(bx + 22), p(cy - 8), p(sx - bx - 33), p(16))

        # bolt holes in big end (for cap split)
        c.setLineWidth(0.4)
        c.circle(p(bx + 13), p(cy + 22), p(4))
        c.circle(p(bx + 13), p(cy - 22), p(4))
        c.setFont(FONTS["normal"], 5)
        c.drawString(p(bx + 16), p(cy + 24), "M12×1.25")

        # split line (horizontal)
        c.setLineWidth(0.5)
        c.setDash([p(4), p(2)], 0)
        c.line(p(bx - 24), p(cy), p(bx + 24), p(cy))
        c.setDash([])
        c.setFont(FONTS["bold"], 5.5)
        c.drawString(p(bx - 24), p(cy + 2), "SPLIT LINE")

        centerline_h(c, 30, 210, cy)
        centerline_v(c, bx, cy - 28, cy + 28)
        centerline_v(c, sx, cy - 15, cy + 15)

        # section arrow
        c.setFont(FONTS["bold"], 7)
        c.drawString(p(125), p(cy - 30), "A")
        c.drawString(p(135), p(cy - 30), "A")
        c.line(p(125), p(cy - 28), p(135), p(cy - 28))

        # dimensions
        dim_line_h(c, bx, sx, DA_Y0 + 5, "145.00 ±0.05 CTR-CTR", offset_mm=4)
        dim_line_h(c, bx - 18, bx + 18, cy + 30, "Ø48.000 H6", offset_mm=3)
        dim_line_h(c, sx - 7, sx + 7, cy + 18, "Ø22 H7", offset_mm=3)

        # SECTION A-A (I-section)
        sx2 = 220
        c.setFont(FONTS["bold"], 6)
        c.drawCentredString(p(sx2 + 15), p(DA_Y1 - 6), "SECTION A-A")
        c.setLineWidth(0.7)
        # I-section: flanges + web
        c.rect(p(sx2), p(cy - 9), p(30), p(4))    # bottom flange
        c.rect(p(sx2), p(cy + 5), p(30), p(4))    # top flange
        c.rect(p(sx2 + 12), p(cy - 9), p(6), p(18))  # web
        section_hatch(c, sx2, cy - 9, 30, 4)
        section_hatch(c, sx2, cy + 5, 30, 4)
        section_hatch(c, sx2 + 12, cy - 9, 6, 18)
        dim_line_h(c, sx2, sx2 + 30, DA_Y0 + 10, "22.0", offset_mm=3)
        dim_line_v(c, cy - 9, cy + 9, sx2 - 2, "18.0", offset_mm=5)

    def _view_big_end_cap(self, c, spec):
        cx, cy = 110, (DA_Y0 + DA_Y1) / 2 + 20

        c.setFont(FONTS["bold"], 6)
        c.drawCentredString(p(cx), p(DA_Y1 - 6), "FRONT VIEW")

        # semi-circular cap
        pth = c._canvas.beginPath() if hasattr(c, '_canvas') else c.beginPath()
        pth.arc(p(cx - 24), p(cy - 24), p(cx + 24), p(cy + 24), startAng=0, extent=180)
        pth.lineTo(p(cx - 24), p(cy))
        pth.close()
        c.setLineWidth(0.7)
        c.drawPath(pth, fill=0, stroke=1)

        # bore (half circle)
        pth2 = c.beginPath()
        pth2.arc(p(cx - 18), p(cy - 18), p(cx + 18), p(cy + 18), startAng=0, extent=180)
        pth2.lineTo(p(cx - 18), p(cy))
        pth2.close()
        c.setLineWidth(0.5)
        c.drawPath(pth2, fill=0, stroke=1)

        # mating face line
        c.setLineWidth(0.8)
        c.line(p(cx - 28), p(cy), p(cx + 28), p(cy))

        # bolt holes
        c.setLineWidth(0.4)
        c.circle(p(cx - 22.5), p(cy + 15), p(4.25))
        c.circle(p(cx + 22.5), p(cy + 15), p(4.25))

        centerline_h(c, cx - 32, cx + 32, cy)
        centerline_v(c, cx, cy, cy + 26)
        centerline_v(c, cx - 22.5, cy, cy + 25)
        centerline_v(c, cx + 22.5, cy, cy + 25)

        # SECTION
        sx = 185
        c.setFont(FONTS["bold"], 6)
        c.drawCentredString(p(sx + 15), p(DA_Y1 - 6), "MATING FACE DETAIL")
        section_hatch(c, sx, cy - 5, 30, 35, spacing_mm=3)
        c.setLineWidth(0.6)
        c.rect(p(sx), p(cy - 5), p(30), p(35))
        # flatness callout
        c.setFont(FONTS["normal"], 5.5)
        c.drawString(p(sx + 32), p(cy + 18), "FLATNESS")
        c.drawString(p(sx + 32), p(cy + 13), "0.02 mm")
        c.drawString(p(sx + 32), p(cy + 8), "Ra 0.8 µm")

        # dimensions
        dim_line_h(c, cx - 22.5, cx + 22.5, cy + 35, "45.0 ±0.05", offset_mm=3)
        dim_line_h(c, cx - 18, cx + 18, cy + 25, "Ø48 H6 (ASSY)", offset_mm=3)
        c.setFont(FONTS["normal"], 5)
        c.drawString(p(cx + 26), p(cy + 8), "2× Ø13.5 H7")

    def _view_rod_bolt(self, c, spec):
        cy = (DA_Y0 + DA_Y1) / 2 + 10

        c.setFont(FONTS["bold"], 6)
        c.drawCentredString(p(120), p(DA_Y1 - 6), "FRONT VIEW (SCALE 2:1)")

        # head
        c.setLineWidth(0.7)
        c.rect(p(20), p(cy - 10), p(18), p(20))
        section_hatch(c, 20, cy - 10, 18, 20, spacing_mm=2.5)

        # shank
        c.rect(p(38), p(cy - 6.5), p(55), p(13))
        section_hatch(c, 38, cy - 6.5, 30, 13, spacing_mm=2.5)

        # thread area
        c.rect(p(93), p(cy - 6.5), p(25), p(13))
        # thread lines (hatch for threads)
        c.setLineWidth(0.2)
        c.setDash([p(1), p(1.5)], 0)
        for xi in range(0, 25, 3):
            c.line(p(93 + xi), p(cy - 6.5), p(93 + xi + 1.5), p(cy + 6.5))
        c.setDash([])
        c.setLineWidth(0.7)
        c.rect(p(93), p(cy - 6.5), p(25), p(13))

        centerline_h(c, 18, 122, cy)

        # dim lines
        dim_line_h(c, 38, 118, DA_Y0 + 8, "55.0 SHANK LENGTH", offset_mm=4)
        dim_line_h(c, 20, 38, cy + 15, "HEAD H=8.0", offset_mm=3)
        dim_line_v(c, cy - 6.5, cy + 6.5, 36, "M12", offset_mm=4)

        # thread callout
        c.setFont(FONTS["bold"], 6)
        c.drawString(p(95), p(cy + 12), "M12 × 1.25-6g")
        c.drawString(p(95), p(cy + 7), "FINE PITCH")
        c.setFont(FONTS["bold"], 8)
        c.drawString(p(150), p(cy), "GR 12.9")

    def _view_lock_nut(self, c, spec):
        cx, cy = 110, (DA_Y0 + DA_Y1) / 2 + 10

        c.setFont(FONTS["bold"], 6)
        c.drawCentredString(p(cx), p(DA_Y1 - 6), "FRONT VIEW (SCALE 2:1)")

        # hexagonal nut (approximated as rectangle for simplicity)
        c.setLineWidth(0.7)
        c.rect(p(cx - 19), p(cy - 10), p(38), p(20))
        # hex sides approximation
        pts_hex = []
        for i in range(6):
            angle = math.radians(i * 60 + 90)
            pts_hex.append((cx + 19 * math.cos(angle), cy + 19 * math.sin(angle)))
        pth = c.beginPath()
        pth.moveTo(p(pts_hex[0][0]), p(pts_hex[0][1]))
        for px2, py2 in pts_hex[1:]:
            pth.lineTo(p(px2), p(py2))
        pth.close()
        c.drawPath(pth, fill=0, stroke=1)

        # thread hole
        c.circle(p(cx), p(cy), p(6.5))

        # deformed thread zone indication
        c.setLineWidth(0.3)
        c.setDash([p(1.5), p(1)], 0)
        c.circle(p(cx), p(cy), p(7.5))
        c.setDash([])
        c.setFont(FONTS["normal"], 5)
        c.drawString(p(cx + 22), p(cy + 5), "DEFORMED THREAD")
        c.drawString(p(cx + 22), p(cy), "(SELF-LOCKING)")

        centerline_h(c, cx - 25, cx + 55, cy)
        centerline_v(c, cx, cy - 25, cy + 25)

        dim_line_h(c, cx - 19, cx + 19, cy + 22, "A/F 19.0", offset_mm=3)
        dim_line_v(c, cy - 10, cy + 10, cx - 21, "12.0 ±0.2", offset_mm=4)

        c.setFont(FONTS["bold"], 7)
        c.drawString(p(cx + 22), p(cy + 18), "M12 × 1.25-6H")
        c.drawString(p(cx + 22), p(cy + 12), "ISO 7042 GR 10")

    def _view_generic_component(self, c, spec):
        cx, cy = 120, (DA_Y0 + DA_Y1) / 2
        c.setLineWidth(0.7)
        c.rect(p(cx - 50), p(cy - 30), p(100), p(60))
        c.setFont(FONTS["normal"], 7)
        c.drawCentredString(p(cx), p(cy), spec.get("part_number", ""))


# ══════════════════════════════════════════════════════════════════════════════
#  PNG GENERATOR
# ══════════════════════════════════════════════════════════════════════════════

class PNGGenerator:
    """Generates PNG preview images using Pillow."""

    W, H = 2480, 1754   # A3 at ~150 dpi
    BG = (255, 255, 255)
    FG = (20, 20, 20)
    GRAY = (130, 130, 130)
    BLUE = (20, 20, 160)

    def generate(self, spec: Dict, png_path: Path):
        img = Image.new("RGB", (self.W, self.H), self.BG)
        draw = ImageDraw.Draw(img)
        self._border(draw, spec)
        self._title_block(draw, spec)
        self._content_area(draw, spec)

        # realistic imperfections
        if spec.get("blur"):
            img = img.filter(ImageFilter.GaussianBlur(radius=2.5))
        elif spec.get("drawing_status") == "in_work":
            img = img.filter(ImageFilter.GaussianBlur(radius=1.2))
        else:
            # slight noise for "scanned" look
            if random.random() > 0.5:
                img = img.filter(ImageFilter.SMOOTH)

        img.save(str(png_path), "PNG", dpi=(150, 150))

    def _px(self, mm_val: float) -> int:
        return int(mm_val * (self.W / 420))

    def _border(self, draw: ImageDraw.Draw, spec):
        m = self._px(BDR)
        draw.rectangle([m, m, self.W - m, self.H - m], outline=self.FG, width=3)
        draw.rectangle([m + self._px(2), m + self._px(2),
                        self.W - m - self._px(2), self.H - m - self._px(2)],
                       outline=self.FG, width=5)
        # zone ticks
        bw = (self.W - 2 * m) // 8
        for i in range(1, 8):
            xx = m + i * bw
            draw.line([(xx, m), (xx, m + self._px(3))], fill=self.GRAY, width=1)
            draw.line([(xx, self.H - m - self._px(3)), (xx, self.H - m)],
                      fill=self.GRAY, width=1)

    def _title_block(self, draw: ImageDraw.Draw, spec):
        m = self._px(BDR)
        tb = self._px(TB_H)
        y0 = self.H - m - tb
        # border of title block
        draw.rectangle([m, y0, self.W - m, self.H - m], outline=self.FG, width=2)
        draw.line([(m, y0 + tb // 4), (self.W - m, y0 + tb // 4)],
                  fill=self.GRAY, width=1)
        draw.line([(m, y0 + tb // 2), (self.W - m, y0 + tb // 2)],
                  fill=self.GRAY, width=1)
        draw.line([(m, y0 + 3 * tb // 4), (self.W - m, y0 + 3 * tb // 4)],
                  fill=self.GRAY, width=1)
        # vertical split
        xs = m + int((self.W - 2 * m) * 0.6)
        draw.line([(xs, y0), (xs, self.H - m)], fill=self.FG, width=2)

        # company name
        try:
            font_big = ImageFont.truetype("arial.ttf", 36)
            font_med = ImageFont.truetype("arial.ttf", 26)
            font_sm = ImageFont.truetype("arial.ttf", 22)
        except Exception:
            font_big = font_med = font_sm = ImageFont.load_default()

        draw.text((m + 20, y0 + 8), "AutoPLM DEMO  |  Edify-AI", fill=self.FG, font=font_big)
        draw.text((m + 20, y0 + 50), spec.get("drawing_title", "")[:60], fill=self.FG, font=font_med)
        draw.text((m + 20, y0 + 80), f"PART: {spec['part_number']}", fill=self.FG, font=font_sm)
        draw.text((m + 20, y0 + 105), f"MATERIAL: {spec.get('material', '')[:55]}", fill=self.GRAY, font=font_sm)
        draw.text((m + 20, y0 + 128), f"TOLERANCE: {spec.get('tolerance', 'ISO 2768-m')}   FINISH: {spec.get('finish', 'Ra 3.2')}", fill=self.GRAY, font=font_sm)

        # right side
        draw.text((xs + 20, y0 + 8), f"DWG: {spec['drawing_number']}", fill=self.FG, font=font_big)
        draw.text((xs + 20, y0 + 50), f"REV: {spec['revision']}   SHEET: 1/{spec.get('sheet_count', 1)}", fill=self.FG, font=font_med)
        draw.text((xs + 20, y0 + 80), f"DRAWN: {spec.get('drawn_by', '—')}   {spec.get('date', '—')}", fill=self.GRAY, font=font_sm)
        draw.text((xs + 20, y0 + 105), f"STATUS: {spec.get('drawing_status', '').upper()}", fill=self.FG, font=font_sm)
        draw.text((xs + 20, y0 + 128), f"SCALE: {spec.get('scale', '1:1')}   MASS: {spec.get('mass', '—')}", fill=self.GRAY, font=font_sm)

    def _content_area(self, draw: ImageDraw.Draw, spec):
        m = self._px(BDR)
        tb = self._px(TB_H)
        y0 = m + self._px(4)
        y1 = self.H - m - tb - self._px(4)
        cx = self.W // 2
        cy = (y0 + y1) // 2

        try:
            font_hdr = ImageFont.truetype("arial.ttf", 32)
            font_body = ImageFont.truetype("arial.ttf", 24)
        except Exception:
            font_hdr = font_body = ImageFont.load_default()

        dtype = spec.get("drawing_type", "component")

        if dtype in ("assembly", "sub_assembly"):
            # draw simplified assembly outline
            draw.rectangle([cx - self._px(80), cy - self._px(40),
                            cx + self._px(80), cy + self._px(40)],
                           outline=self.FG, width=4)
            draw.text((cx - self._px(60), cy - self._px(15)),
                      spec.get("drawing_title", ""), fill=self.FG, font=font_hdr)
            # BOM table in upper right
            self._png_bom(draw, spec, font_body)
            # assembly notes
            self._png_notes(draw, spec, m + self._px(5), y0 + self._px(5),
                            cx - self._px(5), font_body)
        else:
            # component — draw schematic box with cross
            draw.rectangle([cx - self._px(60), cy - self._px(40),
                            cx + self._px(60), cy + self._px(40)],
                           outline=self.FG, width=4)
            # centerlines
            draw.line([(cx - self._px(70), cy), (cx + self._px(70), cy)],
                      fill=self.BLUE, width=2)
            draw.line([(cx, cy - self._px(50)), (cx, cy + self._px(50))],
                      fill=self.BLUE, width=2)
            draw.text((cx - self._px(55), cy - self._px(35)),
                      spec.get("part_number", ""), fill=self.FG, font=font_hdr)
            # notes right side
            self._png_notes(draw, spec, cx + self._px(70), y0 + self._px(5),
                            self.W - m - self._px(5), font_body)
            # dims left side
            self._png_dims(draw, spec, m + self._px(5), y0 + self._px(5),
                           cx - self._px(70), font_body)

    def _png_bom(self, draw: ImageDraw.Draw, spec, font):
        bom = spec.get("bom", [])
        if not bom:
            return
        m = self._px(BDR)
        x0 = self.W - m - self._px(160)
        y0 = m + self._px(6)
        row_h = self._px(8)
        try:
            font_hdr2 = ImageFont.truetype("arialbd.ttf", 26)
        except Exception:
            font_hdr2 = font
        draw.text((x0, y0), "BILL OF MATERIALS", fill=self.FG, font=font_hdr2)
        y0 += self._px(8)
        draw.rectangle([x0, y0, self.W - m - self._px(4), y0 + self._px(6)],
                       fill=(200, 200, 200), outline=self.FG, width=2)
        draw.text((x0 + 5, y0 + 5), "ITEM  PART NUMBER            DESCRIPTION              QTY", fill=self.FG, font=font)
        y0 += self._px(6)
        for row in bom:
            draw.line([(x0, y0), (self.W - m - self._px(4), y0)], fill=self.GRAY, width=1)
            line = f" {row['item']}    {row['pn']:<25} {row['desc']:<28} {row['qty']}"
            draw.text((x0 + 5, y0 + 3), line, fill=self.FG, font=font)
            y0 += row_h

    def _png_notes(self, draw, spec, x0, y0, x1, font):
        notes = spec.get("notes", [])
        if not notes:
            return
        try:
            font_b = ImageFont.truetype("arialbd.ttf", 26)
        except Exception:
            font_b = font
        draw.text((x0, y0), "NOTES:", fill=self.FG, font=font_b)
        y = y0 + self._px(7)
        for note in notes[:12]:
            draw.text((x0, y), note[:60], fill=self.FG, font=font)
            y += self._px(5.5)

    def _png_dims(self, draw, spec, x0, y0, x1, font):
        dims = spec.get("dimensions", [])
        if not dims:
            return
        try:
            font_b = ImageFont.truetype("arialbd.ttf", 26)
        except Exception:
            font_b = font
        draw.text((x0, y0), "KEY DIMENSIONS:", fill=self.FG, font=font_b)
        y = y0 + self._px(7)
        for dim in dims[:10]:
            draw.text((x0, y), dim[:50], fill=self.FG, font=font)
            y += self._px(5.5)


# ══════════════════════════════════════════════════════════════════════════════
#  DATABASE SEEDER
# ══════════════════════════════════════════════════════════════════════════════

def seed_database(db_path: Path, drawings_file_info: Dict[str, Dict]):
    engine = create_engine(f"sqlite:///{db_path}", echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # clear existing
        session.query(Drawing).delete()
        session.query(Part).delete()
        session.commit()

        # insert parts
        for pd in PARTS_DATA:
            session.add(Part(**pd))

        # insert drawings
        for drw_id, spec in DRAWINGS_SPECS.items():
            file_type = spec["file_type"]
            ext = "pdf" if file_type == "pdf" else "png"
            file_path = f"data/drawings/{ext}/{drw_id}.{ext}"
            session.add(Drawing(
                drawing_id=spec["drawing_id"],
                part_number=spec["part_number"],
                drawing_number=spec["drawing_number"],
                revision=spec["revision"],
                drawing_title=spec["drawing_title"],
                file_path=file_path,
                file_type=file_type,
                sheet_count=spec.get("sheet_count", 1),
                drawing_status=spec["drawing_status"],
            ))

        session.commit()
        print(f"[OK] Seeded {len(PARTS_DATA)} parts and {len(DRAWINGS_SPECS)} drawings.")
    finally:
        session.close()


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    pdf_dir = PROJECT_ROOT / "data" / "drawings" / "pdf"
    png_dir = PROJECT_ROOT / "data" / "drawings" / "png"
    pdf_dir.mkdir(parents=True, exist_ok=True)
    png_dir.mkdir(parents=True, exist_ok=True)

    db_path = PROJECT_ROOT / "data" / "demo_plm.sqlite"

    pdf_gen = PDFGenerator()
    png_gen = PNGGenerator()

    generated_files: Dict[str, Dict] = {}

    for drw_id, spec in DRAWINGS_SPECS.items():
        file_type = spec["file_type"]
        png_path = png_dir / f"{drw_id}.png"

        # always generate PDF (even for PNG-primary drawings — for completeness)
        pdf_path = pdf_dir / f"{drw_id}.pdf"
        try:
            pdf_gen.generate(spec, pdf_path)
            print(f"  [PDF] {pdf_path.name}")
        except Exception as exc:
            print(f"  [WARN] PDF failed for {drw_id}: {exc}")

        # always generate PNG preview
        try:
            png_gen.generate(spec, png_path)
            print(f"  [PNG] {png_path.name}")
        except Exception as exc:
            print(f"  [WARN] PNG failed for {drw_id}: {exc}")

        generated_files[drw_id] = {
            "pdf": str(pdf_path) if pdf_path.exists() else None,
            "png": str(png_path) if png_path.exists() else None,
        }

    seed_database(db_path, generated_files)
    print("\n[DONE] Seed complete.")
    print(f"  Database : {db_path}")
    print(f"  PDFs     : {len(list(pdf_dir.glob('*.pdf')))} files in {pdf_dir}")
    print(f"  PNGs     : {len(list(png_dir.glob('*.png')))} files in {png_dir}")


if __name__ == "__main__":
    main()
