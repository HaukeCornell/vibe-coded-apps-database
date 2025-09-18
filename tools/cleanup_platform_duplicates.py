#!/usr/bin/env python3
"""
Platform Duplicates Cleanup Script

Consolidates duplicate platform entries in the database:
- GitHub + github.com → GitHub
- Bolt + bolt.new → Bolt  
- Lovable + lovable.dev → Lovable

Moves all applications to the primary platform and removes duplicates.
"""

import sqlite3
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def cleanup_platform_duplicates():
    """Clean up platform duplicates in the database."""
    
    project_root = Path(__file__).parent.parent
    db_path = project_root / "vibe_coded_apps.db"
    
    if not db_path.exists():
        logger.error("❌ Database not found!")
        return
    
    # Define duplicate mappings: old_platform_id -> new_platform_id
    duplicates_to_merge = [
        {
            'keep_id': 12,  # GitHub
            'keep_name': 'GitHub',
            'merge_id': 6,  # github.com
            'merge_name': 'github.com'
        },
        {
            'keep_id': 16,  # Bolt
            'keep_name': 'Bolt', 
            'merge_id': 3,  # bolt.new
            'merge_name': 'bolt.new'
        },
        {
            'keep_id': 15,  # Lovable
            'keep_name': 'Lovable',
            'merge_id': 2,  # lovable.dev  
            'merge_name': 'lovable.dev'
        }
    ]
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Start transaction
        cursor.execute("BEGIN TRANSACTION")
        
        total_moved = 0
        
        for duplicate in duplicates_to_merge:
            keep_id = duplicate['keep_id']
            keep_name = duplicate['keep_name']
            merge_id = duplicate['merge_id']
            merge_name = duplicate['merge_name']
            
            logger.info(f"🔄 Merging {merge_name} (id={merge_id}) into {keep_name} (id={keep_id})")
            
            # Check how many applications need to be moved
            cursor.execute("SELECT COUNT(*) FROM applications WHERE platform_id = ?", (merge_id,))
            apps_to_move = cursor.fetchone()[0]
            
            if apps_to_move > 0:
                logger.info(f"📱 Moving {apps_to_move} applications from {merge_name} to {keep_name}")
                
                # Move applications from duplicate platform to primary platform
                cursor.execute("""
                    UPDATE applications 
                    SET platform_id = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE platform_id = ?
                """, (keep_id, merge_id))
                
                total_moved += apps_to_move
            else:
                logger.info(f"📱 No applications to move from {merge_name}")
            
            # Remove the duplicate platform
            cursor.execute("DELETE FROM platforms WHERE id = ?", (merge_id,))
            logger.info(f"🗑️ Removed duplicate platform: {merge_name}")
        
        # Commit transaction
        cursor.execute("COMMIT")
        
        logger.info(f"✅ Platform cleanup completed!")
        logger.info(f"   Total applications moved: {total_moved}")
        logger.info(f"   Duplicate platforms removed: {len(duplicates_to_merge)}")
        
        # Show updated platform statistics
        show_updated_stats(cursor)
        
    except Exception as e:
        cursor.execute("ROLLBACK")
        logger.error(f"❌ Error during cleanup: {e}")
        raise
    
    finally:
        conn.close()

def show_updated_stats(cursor):
    """Show updated platform statistics after cleanup."""
    logger.info("\n📊 UPDATED PLATFORM STATISTICS:")
    
    cursor.execute("""
        SELECT 
            p.name as platform,
            COUNT(a.id) as app_count,
            COUNT(CASE WHEN a.is_featured = 1 THEN 1 END) as featured_count,
            COUNT(CASE WHEN a.discovery_method = 'api_gallery' THEN 1 END) as api_gallery,
            COUNT(CASE WHEN a.discovery_method = 'github_search' THEN 1 END) as github_search,
            COUNT(CASE WHEN a.discovery_method = 'api_projects' THEN 1 END) as api_projects
        FROM platforms p 
        LEFT JOIN applications a ON p.id = a.platform_id 
        GROUP BY p.name 
        HAVING COUNT(a.id) > 0
        ORDER BY app_count DESC
    """)
    
    results = cursor.fetchall()
    
    logger.info("Platform | Apps | Featured | API Gallery | GitHub Search | API Projects")
    logger.info("-" * 75)
    
    total_apps = 0
    for row in results:
        platform, apps, featured, api_gallery, github_search, api_projects = row
        total_apps += apps
        logger.info(f"{platform:<12} | {apps:>4} | {featured:>8} | {api_gallery:>11} | {github_search:>13} | {api_projects:>12}")
    
    logger.info("-" * 75)
    logger.info(f"{'TOTAL':<12} | {total_apps:>4}")

def verify_no_duplicates():
    """Verify that no duplicate platforms remain."""
    project_root = Path(__file__).parent.parent
    db_path = project_root / "vibe_coded_apps.db"
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check for remaining platforms
    cursor.execute("SELECT id, name, url FROM platforms ORDER BY name")
    platforms = cursor.fetchall()
    
    logger.info("\n🔍 REMAINING PLATFORMS:")
    for platform_id, name, url in platforms:
        cursor.execute("SELECT COUNT(*) FROM applications WHERE platform_id = ?", (platform_id,))
        app_count = cursor.fetchone()[0]
        logger.info(f"   {platform_id:>2}: {name:<15} ({app_count:>4} apps) - {url}")
    
    conn.close()

def main():
    """Main cleanup function."""
    logger.info("🧹 Starting platform duplicates cleanup...")
    
    cleanup_platform_duplicates()
    verify_no_duplicates()
    
    logger.info("🎉 Platform cleanup completed successfully!")

if __name__ == "__main__":
    main()