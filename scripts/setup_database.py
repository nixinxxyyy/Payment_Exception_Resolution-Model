"""
Database setup script — creates the MySQL database and all tables.

Usage:
    python scripts/setup_database.py

Prerequisites:
    1. MySQL server running
    2. .env file configured with DB_HOST, DB_PORT, DB_USER, DB_PASSWORD
    3. The DB_USER must have CREATE DATABASE privileges
"""

import sys
import os

# Ensure project root is on the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pymysql
from dotenv import load_dotenv

load_dotenv()


def create_database():
    """Create the MySQL database if it doesn't exist."""
    db_host     = os.getenv("DB_HOST", "localhost")
    db_port     = int(os.getenv("DB_PORT", "3306"))
    db_user     = os.getenv("DB_USER", "root")
    db_password = os.getenv("DB_PASSWORD", "")
    db_name     = os.getenv("DB_NAME", "payment_exception_db")

    print(f"Connecting to MySQL at {db_host}:{db_port} as {db_user}...")

    conn = pymysql.connect(
        host=db_host,
        port=db_port,
        user=db_user,
        password=db_password,
        charset="utf8mb4",
    )
    cursor = conn.cursor()

    print(f"Creating database '{db_name}' if not exists...")
    cursor.execute(
        f"CREATE DATABASE IF NOT EXISTS `{db_name}` "
        "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
    )
    conn.commit()
    cursor.close()
    conn.close()
    print(f"✓ Database '{db_name}' ready.")


def create_tables():
    """Create all ORM-mapped tables."""
    from src.database.schema import init_db
    print("Creating tables...")
    init_db()
    print("✓ All tables created.")


def main():
    print("=" * 60)
    print("  Payment Exception Resolution — Database Setup")
    print("=" * 60)

    try:
        create_database()
        create_tables()
        print()
        print("✓ Database setup complete. You can now start the API server.")
        print()
        print("  Run:  uvicorn src.api.main:api_app --reload --port 8000")
    except pymysql.err.OperationalError as e:
        print(f"\n✗ MySQL connection failed: {e}")
        print("\nCheck your .env file:")
        print("  DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Setup failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
