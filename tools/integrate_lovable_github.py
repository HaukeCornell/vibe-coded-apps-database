#!/usr/bin/env python3
"""
Integrate Lovable GitHub Discoveries into Database

Takes the GitHub discovery results and adds them to the main database.
"""

import json
import sqlite3
import logging
from datetime import datetime
from pathlib import Path
import sys
import os

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def integrate_lovable_github_discoveries():
    """Integrate Lovable GitHub discoveries into the database."""
    
    # Find the most recent discovery file
    tools_dir = project_root / "tools"
    discovery_files = list(tools_dir.glob("lovable_github_discovery_*.json"))
    
    if not discovery_files:
        logger.error("❌ No Lovable GitHub discovery files found!")
        return
    
    latest_file = max(discovery_files, key=lambda p: p.stat().st_mtime)
    logger.info(f"📖 Using discovery file: {latest_file}")
    
    # Load discovery data
    with open(latest_file, 'r') as f:
        discovery_data = json.load(f)
    
    likely_repos = discovery_data.get('likely_lovable_repositories', [])
    logger.info(f"🔍 Found {len(likely_repos)} likely Lovable repositories")
    
    # Connect to database
    db_path = project_root / "vibe_coded_apps.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get Lovable platform ID (check both "Lovable" and "lovable.dev")
    cursor.execute("SELECT id FROM platforms WHERE name IN ('lovable', 'Lovable', 'lovable.dev')")
    platform_row = cursor.fetchone()
    
    if not platform_row:
        # Create Lovable platform if it doesn't exist
        cursor.execute("""
            INSERT INTO platforms (name, url, description) 
            VALUES ('lovable', 'https://lovable.dev', 'Lovable AI-powered development platform')
        """)
        lovable_platform_id = cursor.lastrowid
        logger.info("➕ Created Lovable platform entry")
    else:
        lovable_platform_id = platform_row[0]
    
    # Process each likely repository
    added_count = 0
    updated_count = 0
    
    for repo_analysis in likely_repos:
        repo_name = repo_analysis.get('repo_name', '')
        description = repo_analysis.get('description', '')
        
        if not repo_name:
            continue
        
        # Build GitHub URL
        github_url = f"https://github.com/{repo_name}"
        
        # Extract title from repo name
        name = repo_name.split('/')[-1].replace('-', ' ').replace('_', ' ').title()
        
        # Extract author
        author = repo_name.split('/')[0] if '/' in repo_name else 'Unknown'
        
        # Check if this GitHub URL already exists
        cursor.execute("""
            SELECT id, name, description FROM applications 
            WHERE url = ?
        """, (github_url,))
        existing = cursor.fetchone()
        
        if existing:
            # Update existing record to mark as Lovable-created
            app_id = existing[0]
            cursor.execute("""
                UPDATE applications 
                SET platform_id = ?, discovery_method = 'github_search',
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (lovable_platform_id, app_id))
            updated_count += 1
            logger.info(f"🔄 Updated existing: {repo_name}")
        else:
            # Add new application
            try:
                cursor.execute("""
                    INSERT INTO applications (
                        name, description, url, platform_id,
                        created_at, is_featured, discovery_method, external_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    name,
                    description,
                    github_url,  # Use GitHub URL as main URL
                    lovable_platform_id,
                    repo_analysis.get('created_at'),
                    False,  # Not featured since discovered via search
                    'github_search',
                    repo_name  # Use repo name as external_id
                ))
                added_count += 1
                logger.info(f"➕ Added new: {repo_name}")
                
            except Exception as e:
                logger.error(f"❌ Error adding {repo_name}: {e}")
    
    # Commit changes
    conn.commit()
    conn.close()
    
    logger.info(f"✅ Integration complete!")
    logger.info(f"   Added: {added_count} new applications")
    logger.info(f"   Updated: {updated_count} existing applications")
    logger.info(f"   Total processed: {len(likely_repos)} repositories")
    
    return added_count, updated_count

def update_database_stats():
    """Show updated database statistics."""
    db_path = project_root / "vibe_coded_apps.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get total counts
    cursor.execute("SELECT COUNT(*) FROM applications")
    total_apps = cursor.fetchone()[0]
    
    # Get Lovable counts
    cursor.execute("""
        SELECT COUNT(*) FROM applications a
        JOIN platforms p ON a.platform_id = p.id
        WHERE p.name IN ('lovable', 'Lovable', 'lovable.dev')
    """)
    lovable_apps = cursor.fetchone()[0]
    
    # Get discovery method breakdown
    cursor.execute("""
        SELECT discovery_method, COUNT(*) 
        FROM applications a
        JOIN platforms p ON a.platform_id = p.id
        WHERE p.name IN ('lovable', 'Lovable', 'lovable.dev')
        GROUP BY discovery_method
    """)
    discovery_breakdown = cursor.fetchall()
    
    conn.close()
    
    logger.info(f"📊 DATABASE STATISTICS:")
    logger.info(f"   Total applications: {total_apps}")
    logger.info(f"   Lovable applications: {lovable_apps}")
    logger.info(f"   Discovery breakdown:")
    for method, count in discovery_breakdown:
        logger.info(f"     {method}: {count}")

def main():
    """Main integration function."""
    logger.info("🚀 Starting Lovable GitHub integration...")
    
    added, updated = integrate_lovable_github_discoveries()
    update_database_stats()
    
    logger.info("🎉 Lovable GitHub integration completed!")

if __name__ == "__main__":
    main()