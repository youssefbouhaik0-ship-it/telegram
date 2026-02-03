import os
import sys

print("--- 🏥 STARTING HEALTH CHECK ---")

# 1. Check Libraries
print("1. Checking Libraries...", end=" ")
try:
    import telethon
    import pandas
    import xlsxwriter
    import openpyxl
    print("✅ OK")
except ImportError as e:
    print(f"❌ FAIL. Missing library: {e}")
    print("   FIX: Add 'xlsxwriter' to requirements.txt")
    sys.exit(1)

# 2. Check Secrets
required_secrets = ["TG_API_ID", "TG_API_HASH", "TG_SESSION_STRING", "EMAIL_USER", "EMAIL_PASS"]
print("2. Checking Secrets...")
missing = []
for key in required_secrets:
    value = os.environ.get(key)
    if not value:
        print(f"   ❌ MISSING: {key}")
        missing.append(key)
    else:
        # Check for common copy-paste errors (spaces)
        if len(value.strip()) == 0:
             print(f"   ❌ EMPTY: {key} (Value is blank)")
             missing.append(key)
        else:
            masked = value[:2] + "****" + value[-2:] if len(value) > 4 else "****"
            print(f"   ✅ FOUND: {key} ({masked})")

if missing:
    print("\n🚨 CRITICAL ERROR: The Python script cannot see your secrets.")
    print("   FIX: You must update '.github/workflows/daily_scan.yml' to pass these secrets.")
    sys.exit(1)

# 3. Check Session String Format
print("3. Checking Session String...", end=" ")
session = os.environ.get("TG_SESSION_STRING")
if len(session) < 20:
    print("❌ FAIL. String is too short.")
    sys.exit(1)
else:
    print("✅ OK")

print("\n--- 💚 HEALTH CHECK PASSED ---")
print("If you see this, the environment is perfect. The issue is in the main bot logic.")
