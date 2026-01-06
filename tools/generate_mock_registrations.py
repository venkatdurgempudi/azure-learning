#!/usr/bin/env python3
"""
Generate mock registrations CSV and small master CSVs.

Usage:
  python tools/generate_mock_registrations.py --rows 2000 --out data/registrations_2000.csv \
      --start 2025-04-01 --end 2026-01-04 --seed 42

This will also write:
  data/gender_master.csv
  data/unit_master.csv
"""
import csv
import argparse
from datetime import datetime, timedelta
import random
import os

def rand_datetime_between(rng, start_dt, end_dt):
    total_seconds = int((end_dt - start_dt).total_seconds())
    if total_seconds <= 0:
        return start_dt
    offset = rng.randint(0, total_seconds)
    return start_dt + timedelta(seconds=offset)

def iso_fmt(dt):
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def generate_registrations(path, rows, start_date, end_date, seed=42, start_reg_id=1001, start_patient=5001):
    rng = random.Random(seed)
    sources = ["walkin","online","referral","phone","mobile_app"]
    # patient ids will cycle in a range so there are repeats
    patient_range = (start_patient, start_patient + max(500, rows//2))
    unit_choices = [10,11,12,13,14]
    gender_choices = [1,2,3]

    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    # use end of day for end_date
    end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(hours=23, minutes=59, seconds=59)

    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["registration_id","patient_id","reg_dt","unit_id","gender_id","source","created_at","modified_at"])
        for i in range(rows):
            reg_id = start_reg_id + i
            patient_id = rng.randint(patient_range[0], patient_range[1])
            reg_dt = rand_datetime_between(rng, start_dt, end_dt)
            # created_at equals reg_dt in this synthetic data
            created_at = reg_dt
            # modified_at is reg_dt + 0..72 hours but capped to end_dt
            max_add_seconds = 72 * 3600
            add_seconds = rng.randint(0, max_add_seconds)
            modified_at = reg_dt + timedelta(seconds=add_seconds)
            if modified_at > end_dt:
                modified_at = end_dt
            unit_id = rng.choice(unit_choices)
            gender_id = rng.choice(gender_choices)
            source = rng.choice(sources)
            w.writerow([reg_id, patient_id, iso_fmt(reg_dt), unit_id, gender_id, source, iso_fmt(created_at), iso_fmt(modified_at)])
    print(f"Wrote {rows} registrations to {path}")

def write_gender_master(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["gender_id","gender_desc"])
        w.writerow([1,"Male"])
        w.writerow([2,"Female"])
        w.writerow([3,"Other"])
    print(f"Wrote gender master to {path}")

def write_unit_master(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    units = [
        (10, "General Ward", 1),
        (11, "Emergency", 1),
        (12, "Outpatient", 1),
        (13, "Pediatrics", 2),
        (14, "Maternity", 2),
    ]
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["unit_id","unit_name","facility_id"])
        for r in units:
            w.writerow(r)
    print(f"Wrote unit master to {path}")

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--rows", type=int, default=2000, help="Number of registration rows")
    p.add_argument("--out", type=str, default="data/registrations_2000.csv", help="Output CSV path")
    p.add_argument("--start", type=str, default="2025-04-01", help="Start date (YYYY-MM-DD)")
    p.add_argument("--end", type=str, default="2026-01-04", help="End date (YYYY-MM-DD)")
    p.add_argument("--seed", type=int, default=42, help="Random seed")
    args = p.parse_args()

    write_gender_master("data/gender_master.csv")
    write_unit_master("data/unit_master.csv")
    generate_registrations(args.out, args.rows, args.start, args.end, seed=args.seed)

if __name__ == "__main__":
    main()