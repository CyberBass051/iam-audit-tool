#!/usr/bin/env bash

FILE="iam_report.csv"
PYTHON_SCRIPT="iam_security_compliance.py"

if [[ -z "$FILE" || -z "$PYTHON_SCRIPT" ]]; then
    echo "Missing required file or python script"
    exit 1
fi

echo "[*] Starting security audit"

# 1. Run the python script
python3 "$PYTHON_SCRIPT" -f "$FILE" -d 90

# 2. Use jq to parse the JSON output script created
LATEST_JSON=$(ls -t iam_audit_*.json | head -1)
VIOLATIONS=$(jq '.summary.stale_key_count' "$LATEST_JSON")

echo "[*] Audit complete. Found $VIOLATIONS violations"

if [[ "$VIOLATIONS" -gt 0 ]]; then
    echo "[!] Violations found! Triggering GitHub Action..."

    # Using the GitHub CLI (The cleanest way)
    gh api /repos/:owner/:repo/dispatches \
      -X POST \
      -F "event_type=security_violation_found" \
      -F "client_payload[violation_count]=$VIOLATIONS" \
      -F "client_payload[report_name]=$LATEST_JSON"
      
else
    echo "[*] No violations found. Infratructure is compliant."
fi
