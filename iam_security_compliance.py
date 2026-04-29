#!/usr/bin/env python3

import sys
import csv
import logging
import argparse
import os
import json
from logging import StreamHandler
from logging.handlers import RotatingFileHandler
from datetime import datetime, timezone, timedelta

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "iam_security.log")
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
REPORT = f"iam_security_compliance_report{timestamp}.txt"

def argument_parser():
    """Dynamically parses 'report file' and 'threshold days' for key rotation"""
    parser = argparse.ArgumentParser("Dinamically checks for old access keys and users without MFA enabled")
    parser.add_argument("-f", "--file", help="Path to the CSV file", required=True)
    parser.add_argument("-d", "--days", help="Number of days to consider a key as 'old'", required=False, default=90, type=int)

    return parser.parse_args()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        RotatingFileHandler(LOG_FILE, maxBytes=5*1024*1024, backupCount=5),
        StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def check_iam_compliance(file: str, days: int) -> None:
    """Checks IAM compliance based on MFA status and access key age"""
    # Initialize consistently
    old_keys = { "data": [], "count": 0 }
    no_mfa = { "users": [], "count": 0 }

    # Inizialize a structured finding dictionary
    audit_results = {
        "audit_metadata": {
            "timestamp": timestamp,
            "target_file": file, 
            "threshold_days": days,
        },
        "violations": {
            "no_mfa": no_mfa["users"],
            "stale_keys": []
        },
        "summary": {
            "mfa_violation_count": 0,
            "stale_key_count": 0
        }
    }
    
    try:
        with open(file, mode='r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # MFA logic
                if row['mfa_active'].lower() == 'false':
                    no_mfa['users'].append(row['user'])
                    no_mfa['count'] += 1
                
                # Old keys logic (Key 1)
                if row['access_key_1_active'].lower() == 'true':
                    # Handle Z or offset strings correctly
                    last_rotated = datetime.fromisoformat(row['access_key_1_last_rotated'].replace('Z', '+00:00'))
                    if datetime.now(timezone.utc) - last_rotated > timedelta(days=days):
                        old_keys['data'].append((row['user'], last_rotated))
                        old_keys['count'] += 1
                        audit_results["violations"]["stale_keys"].append({
                            "username": row['user'],
                            "last_rotated": last_rotated.isoformat()
                        })
                        logger.warning(f"[!] User {row['user']} has an access key older than {days} days.")

        # Reporting MFA
        if no_mfa["count"] > 0:
            logger.warning(f"[!] Found {no_mfa['count']} users without MFA.")
            with open(REPORT, 'a') as r:
                r.write(f"\n[!] Found {no_mfa['count']} users without MFA enabled.\n")
                r.write("-" * 50 + "\n")
                r.write('\n'.join(no_mfa["users"]) + "\n")

        # Reporting Old Keys
        if old_keys['count'] > 0:
            logger.warning(f"[!] Found {old_keys['count']} users with old keys.")
            with open(REPORT, 'a') as r:
                r.write(f"\n[!] Found {old_keys['count']} users with keys older than {days} days.\n")
                r.write("-" * 50 + "\n")
                for user, date in old_keys['data']:
                    r.write(f"User: {user}, Last Rotated: {date}\n")

        # Update count inside json_report
        audit_results["summary"]["mfa_violation_count"] = no_mfa["count"]
        audit_results["summary"]["stale_key_count"] = old_keys['count']

        # Write the JSON file 
        json_report = f"iam_audit_{timestamp}.json"
        with open(json_report, 'w') as j:
            json.dump(audit_results, j, indent=4)

        logger.info(f"JSON data sounrce generated: {json_report}")
    
    except FileNotFoundError:
        logger.error(f"[!] Error: file {file} not found")
        sys.exit(1)
    except KeyError as e:
        logger.error(f"[!] Error: missing column in CSV file - {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"[!] Unexpected error: {e}")
        sys.exit(1)


def main():
    args = argument_parser()
    logger.info("Starting IAM Security Compliance Check")
    check_iam_compliance(args.file, args.days)
    logger.info("IAM Security Compliance Check completed")

if __name__ == "__main__":
    main()

