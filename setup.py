"""
Setup configuration for the Customer Support Ticket Management System.

This file exists for backward compatibility with older tools.
All configuration is now in pyproject.toml (PEP 518/621).
"""

if __name__ == "__main__":
    try:
        from setuptools import setup
        setup()
    except ImportError:
        print(
            "setuptools is not installed. "
            "Please install it using: pip install setuptools"
        )
        print(
            "\nFor modern installation, use: pip install -e . "
            "(requires pip >= 21.3)"
        )