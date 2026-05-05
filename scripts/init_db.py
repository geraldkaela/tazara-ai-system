import sys
import os
from pathlib import Path

# Add project root to sys.path
sys.path.append(os.getcwd())

from database.db_manager import db_manager

def main():
    print("Initializing Postgres database for TAZARA Multi-Route...")
    success = db_manager.initialize_database()
    if success:
        print("Database initialized successfully!")
    else:
        print("Database initialization failed. Check logs for details.")

if __name__ == "__main__":
    main()
