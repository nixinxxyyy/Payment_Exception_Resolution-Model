"""
Script to test the FastAPI endpoints.
Make sure the API server is running before executing this script.
"""

import json
import time

import requests


API_BASE_URL = "http://localhost:8000"


def print_section(title: str) -> None:
    """Print a formatted section header."""
    print(f"\n{'='*80}")
    print(f"{title}")
    print(f"{'='*80}\n")


def test_health_check() -> bool:
    """Test the health check endpoint."""
    print_section("1. Testing Health Check")

    response = requests.get(f"{API_BASE_URL}/health")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    return response.status_code == 200


def test_root_endpoint() -> bool:
    """Test the root endpoint."""
    print_section("2. Testing Root Endpoint")

    response = requests.get(f"{API_BASE_URL}/")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    return response.status_code == 200


def test_process_ticket(query: str, description: str) -> bool:
    """Test ticket processing endpoint."""
    print_section(f"Testing: {description}")

    payload = {
        "customer_query": query,
        "customer_email": "test@example.com"
    }

    print(f"Request Payload:")
    print(json.dumps(payload, indent=2))
    print()

    start_time = time.time()
    response = requests.post(
        f"{API_BASE_URL}/api/v1/tickets/process",
        json=payload
    )
    elapsed_time = time.time() - start_time

    print(f"Status Code: {response.status_code}")
    print(f"Processing Time: {elapsed_time:.2f}s")

    if response.status_code == 200:
        result = response.json()
        print(f"\nTicket ID: {result['ticket_id']}")
        print(f"Category: {result['category']}")
        print(f"Priority: {result['priority']}")
        print(f"Escalated: {result['needs_escalation']}")
        print(f"\nFinal Response Preview:")
        print("-" * 80)
        print(result['final_response'][:300] + "..." if len(result['final_response']) > 300 else result['final_response'])
        print("-" * 80)
    else:
        print(f"Error: {response.text}")

    return response.status_code == 200


def test_metrics() -> bool:
    """Test metrics endpoint."""
    print_section("Testing Metrics Endpoint")

    response = requests.get(f"{API_BASE_URL}/api/v1/metrics")
    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        metrics = response.json()
        print(f"Response: {json.dumps(metrics, indent=2)}")
    else:
        print(f"Error: {response.text}")

    return response.status_code == 200


def main() -> None:
    """Run all API tests."""
    print("\n" + "="*80)
    print("CUSTOMER SUPPORT API - TEST SUITE")
    print("="*80)

    print(f"\nTarget API: {API_BASE_URL}")
    print("Make sure the API server is running!\n")

    try:
        # Test basic endpoints
        if not test_health_check():
            print("\n❌ Health check failed. Is the server running?")
            return

        test_root_endpoint()

        # Test ticket processing with various scenarios
        test_cases = [
            {
                "query": "My application keeps crashing when I upload large files. I'm using Chrome on Windows 10.",
                "description": "Technical Issue - Application Crash"
            },
            {
                "query": "I was charged $99 twice this month. I need a refund for the duplicate charge.",
                "description": "Billing Issue - Duplicate Charge"
            },
            {
                "query": "How do I reset my password?",
                "description": "General Question - Password Reset"
            },
            {
                "query": "I need to speak with a manager immediately! This is unacceptable and I'll be contacting my lawyer!",
                "description": "High Priority - Escalation Expected"
            },
        ]

        print_section("3. Testing Ticket Processing")
        success_count = 0

        for i, test_case in enumerate(test_cases, 1):
            print(f"\nTest Case {i}/{len(test_cases)}")
            if test_process_ticket(test_case["query"], test_case["description"]):
                success_count += 1

            if i < len(test_cases):
                time.sleep(1)  # Brief pause between requests

        # Test metrics
        test_metrics()

        # Summary
        print_section("TEST SUMMARY")
        print(f"✅ Successful ticket processing: {success_count}/{len(test_cases)}")
        print(f"Success Rate: {(success_count/len(test_cases)*100):.1f}%")
        print("\n" + "="*80 + "\n")

    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Could not connect to the API server.")
        print("Please make sure the server is running:")
        print("  python -m src.api.main")
        print("or")
        print("  uvicorn src.api.main:api_app --reload\n")
    except Exception as e:
        print(f"\n❌ ERROR: {e}\n")


if __name__ == "__main__":
    main()
