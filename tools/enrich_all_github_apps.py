#!/usr/bin/env python3
"""
Comprehensive Database Enrichment

Enriches all GitHub-based applications across all platforms,
focusing on prompt extraction and metadata enhancement.
"""

import sqlite3
import sys
from pathlib import Path
import logging
import time

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from tools.database_enrichment import DatabaseEnricher

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def enrich_all_github_apps():
    """Enrich all GitHub-based applications across all platforms."""
    import os
    
    github_token = os.getenv('GITHUB_TOKEN')
    enricher = DatabaseEnricher(github_token)
    
    # Setup schema first
    enricher.setup_enhanced_schema()
    
    # Get all GitHub apps that haven't been enriched yet
    conn = sqlite3.connect(enricher.db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            a.id, 
            a.name, 
            a.url, 
            a.description,
            p.name as platform,
            a.last_enriched_at
        FROM applications a
        JOIN platforms p ON a.platform_id = p.id
        WHERE a.url LIKE '%github.com%'
        AND a.last_enriched_at IS NULL
        ORDER BY 
            CASE p.name 
                WHEN 'Lovable' THEN 1 
                WHEN 'GitHub' THEN 2 
                WHEN 'Bolt' THEN 3 
                ELSE 4 
            END,
            a.id
        LIMIT 100
    """)
    
    github_apps = cursor.fetchall()
    conn.close()
    
    logger.info(f"🎯 Found {len(github_apps)} GitHub apps to enrich")
    
    if not github_apps:
        logger.info("✅ All GitHub apps already enriched")
        return
    
    # Group by platform for reporting
    platform_counts = {}
    for app in github_apps:
        platform = app[4]
        platform_counts[platform] = platform_counts.get(platform, 0) + 1
    
    logger.info("📊 Apps to enrich by platform:")
    for platform, count in platform_counts.items():
        logger.info(f"   {platform}: {count}")
    
    enriched_count = 0
    prompt_found_count = 0
    errors = 0
    
    for app_id, name, url, description, platform, last_enriched in github_apps:
        logger.info(f"🔍 [{platform}] Enriching: {name}")
        
        try:
            success = enricher.enrich_application(app_id, name, url, description)
            
            if success:
                enriched_count += 1
                
                # Check if we found a prompt
                conn = sqlite3.connect(enricher.db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT original_prompt FROM applications WHERE id = ?", (app_id,))
                prompt = cursor.fetchone()[0]
                conn.close()
                
                if prompt:
                    prompt_found_count += 1
                    logger.info(f"✨ Found prompt for {name}: {prompt[:100]}...")
            else:
                errors += 1
            
            # Rate limiting - be gentle with GitHub API
            time.sleep(1.2)
            
            # Progress update every 10 apps
            if enriched_count % 10 == 0:
                logger.info(f"📈 Progress: {enriched_count} enriched, {prompt_found_count} prompts found")
            
        except Exception as e:
            logger.error(f"❌ Error enriching {name}: {e}")
            errors += 1
            time.sleep(2)  # Longer delay on error
    
    logger.info(f"\n🎉 Comprehensive enrichment completed!")
    logger.info(f"   ✅ Enriched: {enriched_count}")
    logger.info(f"   ✨ Prompts found: {prompt_found_count}")
    logger.info(f"   ❌ Errors: {errors}")
    
    # Final statistics
    conn = sqlite3.connect(enricher.db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            p.name as platform,
            COUNT(*) as total_apps,
            SUM(CASE WHEN a.original_prompt IS NOT NULL THEN 1 ELSE 0 END) as with_prompts,
            printf('%.1f%%', 100.0 * SUM(CASE WHEN a.original_prompt IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*)) as prompt_rate
        FROM applications a 
        JOIN platforms p ON a.platform_id = p.id 
        WHERE a.url LIKE '%github.com%'
        GROUP BY p.name 
        ORDER BY with_prompts DESC
    """)
    
    results = cursor.fetchall()
    conn.close()
    
    logger.info("\n📊 FINAL GITHUB ENRICHMENT STATS:")
    total_github_apps = 0
    total_prompts = 0
    
    for platform, total, prompts, rate in results:
        logger.info(f"   {platform}: {prompts}/{total} ({rate}) prompts found")
        total_github_apps += total
        total_prompts += prompts
    
    overall_rate = (total_prompts / total_github_apps * 100) if total_github_apps > 0 else 0
    logger.info(f"   🌟 OVERALL: {total_prompts}/{total_github_apps} ({overall_rate:.1f}%) prompts found")
    
    # Show some recent examples
    if prompt_found_count > 0:
        conn = sqlite3.connect(enricher.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT a.name, a.original_prompt, p.name
            FROM applications a
            JOIN platforms p ON a.platform_id = p.id
            WHERE a.original_prompt IS NOT NULL
            AND a.url LIKE '%github.com%'
            ORDER BY a.last_enriched_at DESC
            LIMIT 5
        """)
        
        examples = cursor.fetchall()
        conn.close()
        
        logger.info("\n🔥 RECENT PROMPTS FOUND:")
        for name, prompt, platform in examples:
            logger.info(f"   📝 [{platform}] {name}:")
            logger.info(f"      {prompt[:150]}...")

if __name__ == "__main__":
    enrich_all_github_apps()