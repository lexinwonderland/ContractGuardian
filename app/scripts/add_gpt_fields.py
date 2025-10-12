#!/usr/bin/env python3
"""
Database migration script to add GPT analysis fields to the contracts table.
Run this script to update your existing database with the new GPT analysis columns.
"""

import os
import sys
import sqlite3
from pathlib import Path

# Add the app directory to the Python path
app_dir = Path(__file__).parent.parent
sys.path.insert(0, str(app_dir))

from database import engine
from sqlalchemy import text

def migrate_database():
    """Add GPT analysis fields to the contracts table"""
    
    # SQL statements to add the new columns
    migration_sql = [
        "ALTER TABLE contracts ADD COLUMN gpt_summary TEXT",
        "ALTER TABLE contracts ADD COLUMN gpt_key_risks TEXT",
        "ALTER TABLE contracts ADD COLUMN gpt_recommendations TEXT", 
        "ALTER TABLE contracts ADD COLUMN gpt_overall_assessment TEXT",
        "ALTER TABLE contracts ADD COLUMN gpt_confidence_score TEXT",
        "ALTER TABLE contracts ADD COLUMN gpt_analysis_date DATETIME"
    ]
    
    try:
        with engine.connect() as connection:
            for sql in migration_sql:
                try:
                    connection.execute(text(sql))
                    print(f"✓ Executed: {sql}")
                except Exception as e:
                    if "duplicate column name" in str(e).lower():
                        print(f"⚠ Column already exists: {sql}")
                    else:
                        print(f"✗ Error executing {sql}: {e}")
            
            connection.commit()
            print("\n✅ Database migration completed successfully!")
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🔄 Starting database migration to add GPT analysis fields...")
    print("This will add the following columns to the contracts table:")
    print("- gpt_summary")
    print("- gpt_key_risks") 
    print("- gpt_recommendations")
    print("- gpt_overall_assessment")
    print("- gpt_confidence_score")
    print("- gpt_analysis_date")
    print()
    
    if migrate_database():
        print("\n🎉 Migration completed! Your Contract Guardian app is now ready for GPT integration.")
        print("\nNext steps:")
        print("1. Set your OPENAI_API_KEY environment variable in Render")
        print("2. Deploy your updated app")
        print("3. Start analyzing contracts with AI-powered insights!")
    else:
        print("\n💥 Migration failed. Please check the error messages above.")
        sys.exit(1)
