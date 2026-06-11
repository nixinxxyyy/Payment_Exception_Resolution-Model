"""
End-to-end example script — demonstrates all 7 failure type scenarios.

Usage:
    python scripts/run_example.py

Requires:
    - API server running: uvicorn src.api.main:api_app --reload
"""

import sys
import os
import json
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import requests

BASE = "http://localhost:8000/api/v1"

SCENARIOS = [
    {
        "name": "1. Insufficient Funds",
        "payload": {
            "payment_id":   "PAY-DEMO-001",
            "client_id":    "CLT-4521",
            "account_id":   "ACC-10023456",
            "payment_rail": "NEFT",
            "payment_type": "domestic_transfer",
            "amount":       75000.0,
            "currency":     "INR",
            "beneficiary_details": {"account_no": "123456789012", "ifsc": "HDFC0001234", "name": "Rajesh Kumar"},
            "failure_code": "INSUF_FUNDS",
            "failure_message": "Available balance insufficient",
        },
    },
    {
        "name": "2. Invalid IFSC (Beneficiary Error)",
        "payload": {
            "payment_id":   "PAY-DEMO-002",
            "client_id":    "CLT-7830",
            "account_id":   "ACC-20045678",
            "payment_rail": "NEFT",
            "payment_type": "domestic_transfer",
            "amount":       12500.0,
            "currency":     "INR",
            "beneficiary_details": {"account_no": "987654321098", "ifsc": "INVALIFSC9", "name": "Priya Sharma"},
            "failure_code": "INVALID_IFSC",
            "failure_message": "IFSC not found in RBI directory",
        },
    },
    {
        "name": "3. AML Compliance Hold",
        "payload": {
            "payment_id":   "PAY-DEMO-003",
            "client_id":    "CLT-3341",
            "account_id":   "ACC-30067890",
            "payment_rail": "SWIFT",
            "payment_type": "wire",
            "amount":       150000.0,
            "currency":     "USD",
            "beneficiary_details": {"iban": "DE89370400440532013000", "bic": "COBADEFFXXX", "name": "International Corp Ltd"},
            "failure_code": "AML_HOLD",
            "failure_message": "AML screening flagged",
        },
    },
    {
        "name": "4. Network / Rail Outage",
        "payload": {
            "payment_id":   "PAY-DEMO-004",
            "client_id":    "CLT-9102",
            "account_id":   "ACC-40089012",
            "payment_rail": "RTGS",
            "payment_type": "domestic_transfer",
            "amount":       500000.0,
            "currency":     "INR",
            "beneficiary_details": {"account_no": "112233445566", "ifsc": "SBIN0001234", "name": "Ananya Enterprises"},
            "failure_code": "NETWORK_ERROR",
            "failure_message": "RTGS clearing unavailable",
        },
    },
    {
        "name": "5. Duplicate Payment",
        "payload": {
            "payment_id":   "PAY-DEMO-005",
            "client_id":    "CLT-6654",
            "account_id":   "ACC-50091234",
            "payment_rail": "UPI",
            "payment_type": "domestic_transfer",
            "amount":       5000.0,
            "currency":     "INR",
            "beneficiary_details": {"upi_id": "merchant@okicici", "name": "Metro Retail Pvt Ltd"},
            "failure_code": "DUPLICATE_TXN",
            "failure_message": "Duplicate transaction in 5-minute window",
        },
    },
    {
        "name": "6. Cut-off Time Missed",
        "payload": {
            "payment_id":   "PAY-DEMO-006",
            "client_id":    "CLT-2211",
            "account_id":   "ACC-60012345",
            "payment_rail": "RTGS",
            "payment_type": "domestic_transfer",
            "amount":       200000.0,
            "currency":     "INR",
            "beneficiary_details": {"account_no": "998877665544", "ifsc": "ICIC0001234", "name": "Sunrise Industries"},
            "failure_code": "CUTOFF_EXCEEDED",
            "failure_message": "Submitted after RTGS 17:00 cut-off",
        },
    },
    {
        "name": "7. Uncertain Retry Status",
        "payload": {
            "payment_id":   "PAY-DEMO-007",
            "client_id":    "CLT-8876",
            "account_id":   "ACC-70067890",
            "payment_rail": "NEFT",
            "payment_type": "domestic_transfer",
            "amount":       35000.0,
            "currency":     "INR",
            "beneficiary_details": {"account_no": "445566778899", "ifsc": "AXIS0001234", "name": "Tech Solutions Ltd"},
            "failure_code": "RETRY_UNKNOWN",
            "failure_message": "Prior retry status unknown — debit state uncertain",
        },
    },
]


def run_scenario(s):
    print(f"\n{'─' * 60}")
    print(f"  {s['name']}")
    print(f"{'─' * 60}")

    resp = requests.post(f"{BASE}/exceptions/submit", json=s["payload"], timeout=90)
    if resp.status_code != 200:
        print(f"  ✗ Error {resp.status_code}: {resp.text}")
        return

    r = resp.json()
    print(f"  Exception ID  : {r['exception_id']}")
    print(f"  Failure Type  : {r['failure_type']}")
    print(f"  Resolution    : {r['resolution_action']}")
    print(f"  Status        : {r['status']}")
    print(f"  Confidence    : {(r.get('decision_confidence') or 0) * 100:.0f}%")
    print(f"  Escalated To  : {r.get('escalation_queue') or 'N/A'}")
    print(f"  Process Time  : {r['processing_time_s']}s")
    print(f"  Audit Entries : {r['audit_trail_length']}")
    if r.get("decision_rationale"):
        short = r["decision_rationale"][:120]
        print(f"  Rationale     : {short}{'...' if len(r['decision_rationale']) > 120 else ''}")
    return r


def main():
    print("\n" + "=" * 60)
    print("  Payment Exception Resolution — End-to-End Demo")
    print("=" * 60)

    # Health check
    try:
        health = requests.get("http://localhost:8000/health", timeout=5).json()
        print(f"\n✓ API healthy | DB connected: {health.get('db_connected', '?')}")
    except Exception:
        print("\n✗ API not reachable. Start with: uvicorn src.api.main:api_app --reload")
        sys.exit(1)

    results = []
    for scenario in SCENARIOS:
        try:
            r = run_scenario(scenario)
            if r:
                results.append(r)
        except Exception as e:
            print(f"  ✗ Scenario failed: {e}")
        time.sleep(1)

    # Summary
    print(f"\n{'=' * 60}")
    print(f"  SUMMARY: {len(results)}/{len(SCENARIOS)} scenarios processed")
    actions = {}
    for r in results:
        a = r.get("resolution_action", "UNKNOWN")
        actions[a] = actions.get(a, 0) + 1
    for action, count in sorted(actions.items()):
        print(f"    {action}: {count}")
    print("=" * 60)


if __name__ == "__main__":
    main()
