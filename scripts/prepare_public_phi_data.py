#!/usr/bin/env python
"""
Download and Prepare Public PHI Test Datasets
下載並準備公開 PHI 測試資料集

Available datasets:
1. i2b2 2014 De-identification Challenge (requires registration)
2. Synthetic samples based on i2b2 format (included here)

Usage:
    python scripts/prepare_public_phi_data.py
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd

# =============================================================================
# i2b2 2014 Format Synthetic Examples
# Based on the i2b2 2014 De-identification Challenge format
# =============================================================================

I2B2_SYNTHETIC_EXAMPLES = [
    {
        "id": "i2b2-sample-001",
        "text": """Record date: 2024-11-15

HISTORY OF PRESENT ILLNESS: Mr. John Smith is a 72-year-old male with a history of hypertension and diabetes mellitus type 2 who presents with chest pain.

CONTACT: Wife Mary Smith at 555-123-4567. Address: 123 Oak Street, Boston, MA 02115.

PAST MEDICAL HISTORY:
- Hypertension since 2010
- Diabetes since 2015
- Appendectomy 1990

SOCIAL HISTORY: Retired teacher. Former smoker. Lives with wife in Boston.

MEDICATIONS: Metformin 1000mg BID, Lisinopril 10mg daily

ATTENDING: Dr. Robert Johnson, MD
Hospital: Massachusetts General Hospital""",
        "ground_truth": [
            ("2024-11-15", "DATE"),
            ("John Smith", "NAME"),
            ("72-year-old", "AGE"),
            ("Mary Smith", "NAME"),
            ("555-123-4567", "PHONE"),
            ("123 Oak Street", "LOCATION"),
            ("Boston", "LOCATION"),
            ("MA", "LOCATION"),
            ("02115", "LOCATION"),
            ("2010", "DATE"),
            ("2015", "DATE"),
            ("1990", "DATE"),
            ("Boston", "LOCATION"),
            ("Robert Johnson", "NAME"),
            ("Massachusetts General Hospital", "FACILITY"),
        ]
    },
    {
        "id": "i2b2-sample-002",
        "text": """Admission Date: 03/15/2024
Discharge Date: 03/20/2024

Patient: Jane Doe
DOB: 04/22/1955
MRN: 12345678

CHIEF COMPLAINT: Shortness of breath

This is a 68-year-old female with history of COPD who presents with acute exacerbation.

Emergency Contact: Son Michael Doe, phone 617-555-9876

Address: 456 Maple Ave, Apt 2B, Cambridge, MA 02139

HOSPITAL COURSE: Patient was admitted to ICU for respiratory distress. Treated with bronchodilators and steroids. Improved and transferred to floor on HD3.

Discharge to: Home with daughter (Sarah Doe, 617-555-1234)

Follow-up: Dr. Emily Chen, Pulmonology, MGH, in 2 weeks.

Dictated by: Dr. James Wilson
Transcribed: 03/20/2024 14:30""",
        "ground_truth": [
            ("03/15/2024", "DATE"),
            ("03/20/2024", "DATE"),
            ("Jane Doe", "NAME"),
            ("04/22/1955", "DATE"),
            ("12345678", "ID"),
            ("68-year-old", "AGE"),
            ("Michael Doe", "NAME"),
            ("617-555-9876", "PHONE"),
            ("456 Maple Ave, Apt 2B", "LOCATION"),
            ("Cambridge", "LOCATION"),
            ("MA", "LOCATION"),
            ("02139", "LOCATION"),
            ("Sarah Doe", "NAME"),
            ("617-555-1234", "PHONE"),
            ("Emily Chen", "NAME"),
            ("MGH", "FACILITY"),
            ("James Wilson", "NAME"),
            ("03/20/2024", "DATE"),
        ]
    },
    {
        "id": "i2b2-sample-003",
        "text": """Clinical Note - Psychiatry

Date of Service: 2024-02-10

Patient: Robert Williams
Age: 45
SSN: ***-**-6789 (last 4 digits)

Chief Complaint: Depression and anxiety

HPI: Mr. Williams is a 45-year-old software engineer at Google Inc. who presents with worsening depression over the past 3 months. He reports difficulty sleeping, decreased appetite, and loss of interest in activities he previously enjoyed.

Family Hx: Mother diagnosed with bipolar disorder at age 40, died by suicide in 2018.

Social Hx: Divorced in 2022. Two children ages 12 and 15. Lives alone in Palo Alto, CA.

Contact: Ex-wife Jennifer Williams 650-555-0000 for emergencies.

Plan: Start Sertraline 50mg daily. Follow-up in 2 weeks.

Provider: Dr. Lisa Park, MD
Palo Alto Medical Clinic
555 University Ave, Palo Alto, CA 94301
Phone: 650-555-1111""",
        "ground_truth": [
            ("2024-02-10", "DATE"),
            ("Robert Williams", "NAME"),
            ("45", "AGE"),
            ("6789", "ID"),
            ("45-year-old", "AGE"),
            ("Google Inc.", "ORGANIZATION"),
            ("40", "AGE"),
            ("2018", "DATE"),
            ("2022", "DATE"),
            ("12", "AGE"),
            ("15", "AGE"),
            ("Palo Alto", "LOCATION"),
            ("CA", "LOCATION"),
            ("Jennifer Williams", "NAME"),
            ("650-555-0000", "PHONE"),
            ("Lisa Park", "NAME"),
            ("Palo Alto Medical Clinic", "FACILITY"),
            ("555 University Ave", "LOCATION"),
            ("Palo Alto", "LOCATION"),
            ("CA", "LOCATION"),
            ("94301", "LOCATION"),
            ("650-555-1111", "PHONE"),
        ]
    },
    {
        "id": "i2b2-sample-004",
        "text": """OPERATIVE REPORT

Date of Surgery: 11/28/2024
Surgeon: Dr. Michael Brown, MD
Assistant: Dr. Sarah Lee, MD

Patient: Elizabeth Taylor
DOB: 06/15/1960
Age: 64

Preoperative Diagnosis: Right knee osteoarthritis
Postoperative Diagnosis: Same

Procedure: Total right knee arthroplasty

Anesthesia: Spinal

Description: Patient is a 64-year-old retired nurse with severe OA of the right knee. Surgery performed at Stanford Medical Center, OR 5.

EBL: 200cc
Complications: None
Disposition: PACU in stable condition

Specimens: Bone and cartilage to pathology

Next of Kin: Husband Richard Taylor, 408-555-2222

Dictated: 11/28/2024 16:45
Dr. Michael Brown, MD
CA License #: G12345""",
        "ground_truth": [
            ("11/28/2024", "DATE"),
            ("Michael Brown", "NAME"),
            ("Sarah Lee", "NAME"),
            ("Elizabeth Taylor", "NAME"),
            ("06/15/1960", "DATE"),
            ("64", "AGE"),
            ("64-year-old", "AGE"),
            ("Stanford Medical Center", "FACILITY"),
            ("Richard Taylor", "NAME"),
            ("408-555-2222", "PHONE"),
            ("11/28/2024", "DATE"),
            ("Michael Brown", "NAME"),
            ("G12345", "ID"),
        ]
    },
    {
        "id": "i2b2-sample-005",
        "text": """DISCHARGE SUMMARY

Patient: Maria Garcia
MRN: MG-2024-5678
DOB: 12/01/1935
Age: 89

Admission: 10/01/2024
Discharge: 10/15/2024

DIAGNOSES:
1. Hip fracture s/p ORIF
2. Dementia, moderate stage
3. Type 2 diabetes

HOSPITAL COURSE:
Mrs. Garcia is an 89-year-old Spanish-speaking female who fell at home on 09/30/2024. She was brought to UCLA Medical Center by her son Carlos Garcia (310-555-3333).

She underwent ORIF of left hip on 10/02/2024 by Dr. Thomas Anderson. Postop course complicated by delirium, now resolved.

PT/OT consulted. Patient to be discharged to Sunrise Senior Living at 789 Sunset Blvd, Los Angeles, CA 90028.

MEDICATIONS AT DISCHARGE:
- Metformin 500mg BID
- Aricept 10mg daily
- Calcium/Vitamin D

FOLLOW-UP:
Dr. Anderson in 2 weeks (Orthopedic Surgery Clinic, UCLA)
PCP Dr. Rosa Martinez (323-555-4444) in 1 week

Social Worker: Linda Chen, LCSW
Case Manager contact: cm@ucla.edu""",
        "ground_truth": [
            ("Maria Garcia", "NAME"),
            ("MG-2024-5678", "ID"),
            ("12/01/1935", "DATE"),
            ("89", "AGE"),
            ("10/01/2024", "DATE"),
            ("10/15/2024", "DATE"),
            ("89-year-old", "AGE"),
            ("09/30/2024", "DATE"),
            ("UCLA Medical Center", "FACILITY"),
            ("Carlos Garcia", "NAME"),
            ("310-555-3333", "PHONE"),
            ("10/02/2024", "DATE"),
            ("Thomas Anderson", "NAME"),
            ("Sunrise Senior Living", "FACILITY"),
            ("789 Sunset Blvd", "LOCATION"),
            ("Los Angeles", "LOCATION"),
            ("CA", "LOCATION"),
            ("90028", "LOCATION"),
            ("UCLA", "FACILITY"),
            ("Rosa Martinez", "NAME"),
            ("323-555-4444", "PHONE"),
            ("Linda Chen", "NAME"),
            ("cm@ucla.edu", "EMAIL"),
        ]
    },
]


def create_i2b2_format_excel(output_path: str):
    """
    Create Excel file in i2b2-like format
    """
    rows = []
    for example in I2B2_SYNTHETIC_EXAMPLES:
        gt_texts = [gt[0] for gt in example["ground_truth"]]
        gt_types = [gt[1] for gt in example["ground_truth"]]

        rows.append({
            "Case ID": example["id"],
            "Clinical Text": example["text"],
            "Ground Truth PHI": "\n".join(gt_texts),
            "PHI Types": "\n".join(gt_types),
            "PHI Count": len(example["ground_truth"]),
        })

    df = pd.DataFrame(rows)
    df.to_excel(output_path, index=False)
    print(f"✓ Created {output_path}")
    print(f"  - {len(rows)} test cases")
    print(f"  - {sum(r['PHI Count'] for r in rows)} total PHI instances")


def create_tagged_format_excel(output_path: str):
    """
    Create Excel file with PHI tags inline (our format)
    """
    rows = []
    for example in I2B2_SYNTHETIC_EXAMPLES:
        text = example["text"]

        # Add tags to text
        tagged_text = text
        # Sort by position (longest first to avoid nested replacements)
        sorted_gt = sorted(example["ground_truth"], key=lambda x: len(x[0]), reverse=True)

        for i, (phi_text, phi_type) in enumerate(sorted_gt):
            if phi_text in tagged_text:
                tag_id = f"{phi_type[0]}{i:03d}"
                tagged = f"【PHI:{phi_type}:{tag_id}】{phi_text}【/PHI】"
                # Only replace first occurrence
                tagged_text = tagged_text.replace(phi_text, tagged, 1)

        rows.append({
            "Case ID": example["id"],
            "Tagged Clinical Text": tagged_text,
            "PHI Count": len(example["ground_truth"]),
        })

    df = pd.DataFrame(rows)
    df.to_excel(output_path, index=False)
    print(f"✓ Created {output_path}")


def main():
    output_dir = project_root / "data" / "test"
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("Preparing Public PHI Test Datasets")
    print("=" * 60)

    print("\n📦 Creating i2b2-format synthetic dataset...")
    create_i2b2_format_excel(str(output_dir / "i2b2_synthetic_test.xlsx"))

    print("\n📦 Creating tagged format dataset...")
    create_tagged_format_excel(str(output_dir / "i2b2_synthetic_tagged.xlsx"))

    print("\n" + "=" * 60)
    print("📋 Dataset Information:")
    print("=" * 60)
    print("""
These synthetic examples are based on the i2b2 2014 De-identification
Challenge format but are NOT from the actual i2b2 dataset.

To use the REAL i2b2 2014 dataset:
1. Register at: https://portal.dbmi.hms.harvard.edu/
2. Request access to: 2014 De-identification Challenge
3. Download and extract the dataset
4. Use the XML format files for training/testing

For MIMIC-III clinical notes:
1. Complete PhysioNet credentialing
2. Take the required CITI training
3. Access at: https://physionet.org/content/mimiciii/

Other public resources:
- MTSamples (synthetic clinical texts): https://mtsamples.com/
- Medical-NER datasets on Hugging Face
    """)

    print("\n✅ Done!")


if __name__ == "__main__":
    main()
