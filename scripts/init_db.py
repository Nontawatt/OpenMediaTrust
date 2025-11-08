#!/usr/bin/env python3
"""
Database initialization script.

Creates database tables and initial data.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.storage.database import DatabaseStorage


def main():
    """Initialize database."""
    print("OpenMediaTrust - Database Initialization")
    print("=" * 60)

    # Database connection string
    # In production, read from config
    connection_string = "sqlite:///openmediatrust.db"

    print(f"\nConnecting to database: {connection_string}")

    # Create storage instance
    storage = DatabaseStorage(connection_string)

    # Create tables
    print("\nCreating database tables...")
    storage.create_tables()

    print("✓ Database tables created successfully")

    # Create initial admin user (via access control)
    # This would be done through the API in production

    print("\n" + "=" * 60)
    print("Database initialization complete!")
    print("\nNext steps:")
    print("1. Configure config/config.yaml")
    print("2. Generate cryptographic keys")
    print("3. Start the API server")
    print("=" * 60)


if __name__ == "__main__":
    main()
