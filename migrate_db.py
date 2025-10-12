#!/usr/bin/env python3
"""
Quick database migration script to run on Render.
This adds the missing GPT analysis columns to the PostgreSQL database.
"""

import os
import sys
from pathlib import Path

# Add the app directory to the Python path
app_dir = Path(__file__).parent / "app"
sys.path.insert(0, str(app_dir))

from database import engine
from sqlalchemy import text

def main():
    print("🔄 Adding GPT analysis columns to PostgreSQL database...")
    
    # SQL statements to add the new columns
    migrations = [
        "ALTER TABLE contracts ADD COLUMN IF NOT EXISTS gpt_summary TEXT",
        "ALTER TABLE contracts ADD COLUMN IF NOT EXISTS gpt_key_risks TEXT",
        "ALTER TABLE contracts ADD COLUMN IF NOT EXISTS gpt_recommendations TEXT", 
        "ALTER TABLE contracts ADD COLUMN IF NOT EXISTS gpt_overall_assessment TEXT",
        "ALTER TABLE contracts ADD COLUMN IF NOT EXISTS gpt_confidence_score TEXT",
        "ALTER TABLE contracts ADD COLUMN IF NOT EXISTS gpt_analysis_date TIMESTAMP"
    ]
    
    try:
        with engine.connect() as connection:
            for sql in migrations:
                try:
                    connection.execute(text(sql))
                    print(f"✓ {sql}")
                except Exception as e:
                    print(f"⚠ {sql} - {e}")
            
            connection.commit()
            print("\n✅ Migration completed successfully!")
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
