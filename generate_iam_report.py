import csv
import random
from datetime import datetime, timedelta, timezone

# Configuration
FILENAME = "iam_report.csv"
NUM_ENTRIES = 500
DEPARTMENTS = ["Engineering", "DevOps", "Security", "Product", "Finance", "HR"]

def generate_iam_report():
    # Header based on actual AWS IAM credential report format
    header = [
        "user", "arn", "user_creation_time", "password_enabled", 
        "password_last_used", "mfa_active", "access_key_1_active", 
        "access_key_1_last_rotated", "access_key_1_last_used_date"
    ]

    now = datetime.now(timezone.utc)

    with open(FILENAME, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()

        for i in range(1, NUM_ENTRIES + 1):
            # Create a fake username
            dept = random.choice(DEPARTMENTS).lower()
            username = f"user-{dept}-{i:03}"
            
            # Randomize Security Posture
            mfa = random.choice([True, True, True, False]) # 25% chance of MFA being off
            key_active = random.choice([True, True, False]) # 33% chance of no active key
            
            # Create a rotation date (some old, some new)
            days_ago = random.randint(0, 180) # Up to 6 months ago
            rotation_date = now - timedelta(days=days_ago)
            
            # Handle "N/A" logic for inactive keys
            if key_active:
                rot_str = rotation_date.isoformat()
                use_str = (rotation_date + timedelta(days=1)).isoformat()
            else:
                rot_str = "N/A"
                use_str = "N/A"

            writer.writerow({
                "user": username,
                "arn": f"arn:aws:iam::123456789012:user/{username}",
                "user_creation_time": (now - timedelta(days=365)).isoformat(),
                "password_enabled": "true",
                "password_last_used": (now - timedelta(days=random.randint(1, 10))).isoformat(),
                "mfa_active": str(mfa).lower(),
                "access_key_1_active": str(key_active).lower(),
                "access_key_1_last_rotated": rot_str,
                "access_key_1_last_used_date": use_str
            })

    print(f"[+] Successfully generated {FILENAME} with {NUM_ENTRIES} entries.")

if __name__ == "__main__":
    generate_iam_report()