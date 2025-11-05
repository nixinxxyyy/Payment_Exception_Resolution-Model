"""
Utility script to add new FAQ entries to the knowledge base.
"""

import json
import os
import sys
from typing import Dict, Any, Optional

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.config import config


def load_faq_database() -> Optional[Dict[str, Any]]:
    """Load the FAQ database."""
    try:
        with open(config.FAQ_DATABASE_PATH, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"FAQ database not found at {config.FAQ_DATABASE_PATH}")
        return None


def save_faq_database(faq_db: Dict[str, Any]) -> None:
    """Save the FAQ database."""
    with open(config.FAQ_DATABASE_PATH, 'w') as f:
        json.dump(faq_db, f, indent=2)
    print(f"✅ FAQ database saved to {config.FAQ_DATABASE_PATH}")


def add_faq_entry(category: str, question: str, answer: str) -> bool:
    """
    Add a new FAQ entry to the database.

    Args:
        category: Category (TECHNICAL, BILLING, or GENERAL)
        question: The FAQ question
        answer: The FAQ answer
    """
    # Load database
    faq_db = load_faq_database()
    if faq_db is None:
        return False

    # Get next ID
    max_id = max(faq['id'] for faq in faq_db['faqs']) if faq_db['faqs'] else 0
    new_id = max_id + 1

    # Create new entry
    new_entry = {
        "id": new_id,
        "category": category.upper(),
        "question": question,
        "answer": answer
    }

    # Add to database
    faq_db['faqs'].append(new_entry)
    faq_db['metadata']['total_faqs'] = len(faq_db['faqs'])

    # Save
    save_faq_database(faq_db)

    print(f"\n✅ Successfully added FAQ #{new_id}")
    print(f"Category: {category}")
    print(f"Question: {question}")
    print(f"Answer: {answer}\n")

    return True


def interactive_add() -> bool:
    """Interactive mode to add FAQ entries."""
    print("\n" + "="*80)
    print("ADD FAQ ENTRY - INTERACTIVE MODE")
    print("="*80 + "\n")

    # Get category
    print("Select category:")
    print("1. TECHNICAL")
    print("2. BILLING")
    print("3. GENERAL")

    category_map = {
        "1": "TECHNICAL",
        "2": "BILLING",
        "3": "GENERAL"
    }

    while True:
        choice = input("\nEnter choice (1-3): ").strip()
        if choice in category_map:
            category = category_map[choice]
            break
        print("Invalid choice. Please enter 1, 2, or 3.")

    # Get question
    print(f"\nCategory: {category}")
    question = input("Enter question: ").strip()

    # Get answer
    answer = input("Enter answer: ").strip()

    # Confirm
    print("\n" + "-"*80)
    print("Preview:")
    print("-"*80)
    print(f"Category: {category}")
    print(f"Question: {question}")
    print(f"Answer: {answer}")
    print("-"*80)

    confirm = input("\nAdd this FAQ entry? (y/n): ").strip().lower()

    if confirm == 'y':
        return add_faq_entry(category, question, answer)
    else:
        print("❌ Cancelled")
        return False


def list_faqs() -> None:
    """List all FAQ entries."""
    faq_db = load_faq_database()
    if faq_db is None:
        return

    print("\n" + "="*80)
    print(f"FAQ DATABASE - {faq_db['metadata']['total_faqs']} entries")
    print("="*80 + "\n")

    for faq in faq_db['faqs']:
        print(f"[{faq['id']}] {faq['category']}")
        print(f"Q: {faq['question']}")
        print(f"A: {faq['answer'][:100]}..." if len(faq['answer']) > 100 else f"A: {faq['answer']}")
        print()


def main() -> None:
    """Main function."""
    if len(sys.argv) > 1:
        if sys.argv[1] == 'list':
            list_faqs()
        elif sys.argv[1] == 'add':
            if len(sys.argv) == 5:
                category, question, answer = sys.argv[2], sys.argv[3], sys.argv[4]
                add_faq_entry(category, question, answer)
            else:
                interactive_add()
        else:
            print("Usage:")
            print("  python add_faq.py list           - List all FAQs")
            print("  python add_faq.py add            - Add FAQ interactively")
            print("  python add_faq.py add <category> <question> <answer>")
    else:
        interactive_add()


if __name__ == "__main__":
    main()
