#!/usr/bin/env python3
"""
Export SQLite database to GitHub-visible CSV and JSON formats
Creates well-structured tables that are easily browsable on GitHub
"""

import sqlite3
import pandas as pd
import json
from pathlib import Path
import os

def export_database_to_github():
    """Export all database tables to CSV and JSON formats for GitHub visibility"""
    
    # Database path
    db_path = Path(__file__).parent.parent / "vibe_coded_apps.db"
    export_dir = Path(__file__).parent.parent / "export"
    
    if not db_path.exists():
        print(f"Database not found at {db_path}")
        return
    
    # Create export directory
    export_dir.mkdir(exist_ok=True)
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    
    try:
        # Get all table names
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        
        print(f"Found {len(tables)} tables: {tables}")
        
        # Export each table
        for table in tables:
            print(f"\nExporting {table}...")
            
            # Read table into DataFrame
            df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
            
            if len(df) == 0:
                print(f"  {table} is empty, skipping...")
                continue
                
            print(f"  {table}: {len(df)} rows, {len(df.columns)} columns")
            
            # Export to CSV
            csv_path = export_dir / f"{table}.csv"
            df.to_csv(csv_path, index=False)
            print(f"  ✓ Exported to {csv_path}")
            
            # Export to JSON (structured) - handle encoding issues
            json_path = export_dir / f"{table}.json"
            try:
                # Convert to records and handle encoding issues
                records = df.to_dict('records')
                with open(json_path, 'w', encoding='utf-8', errors='ignore') as f:
                    json.dump(records, f, indent=2, ensure_ascii=False, default=str)
                print(f"  ✓ Exported to {json_path}")
            except Exception as e:
                print(f"  ⚠ JSON export failed for {table}: {e}")
                # Fall back to CSV only
                pass
            
            # Show sample data
            print(f"  Sample columns: {list(df.columns)}")
            if len(df) > 0:
                print(f"  Sample record: {dict(df.iloc[0])}")
        
        # Create summary stats
        create_summary_stats(conn, export_dir)
        
    except Exception as e:
        print(f"Error exporting database: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

def create_summary_stats(conn, export_dir):
    """Create a summary statistics file"""
    
    cursor = conn.cursor()
    
    # Get table counts
    stats = {"database_summary": {}}
    
    # Count records in each table
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        stats["database_summary"][table] = count
    
    # Get platform breakdown if apps table exists
    try:
        cursor.execute("SELECT platform, COUNT(*) FROM apps GROUP BY platform ORDER BY COUNT(*) DESC")
        platform_counts = dict(cursor.fetchall())
        stats["platforms"] = platform_counts
    except:
        pass
    
    # Get total unique apps
    try:
        cursor.execute("SELECT COUNT(DISTINCT url) FROM apps")
        unique_apps = cursor.fetchone()[0]
        stats["total_unique_apps"] = unique_apps
    except:
        pass
    
    # Save summary
    summary_path = export_dir / "database_summary.json"
    with open(summary_path, 'w') as f:
        json.dump(stats, f, indent=2)
    
    print(f"\n✓ Created summary at {summary_path}")
    print(f"Summary: {stats}")

if __name__ == "__main__":
    export_database_to_github()