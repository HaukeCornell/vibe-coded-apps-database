#!/usr/bin/env python3
"""
Lovable-Specific Enrichment

Focuses on enriching Lovable applications since they're most likely 
to contain original prompts in their README files.
"""

import sqlite3
import sys
from pathlib import Path
import logging

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from tools.database_enrichment import DatabaseEnricher

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def enrich_lovable_apps():
    """Focus enrichment on Lovable applications."""
    import os
    
    github_token = os.getenv('GITHUB_TOKEN')
    enricher = DatabaseEnricher(github_token)
    
    # Setup schema first
    enricher.setup_enhanced_schema()
    
    # Get Lovable apps specifically
    conn = sqlite3.connect(enricher.db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT a.id, a.name, a.url, a.description, a.last_enriched_at
        FROM applications a
        JOIN platforms p ON a.platform_id = p.id
        WHERE p.name = 'Lovable' 
        AND a.url LIKE '%github.com%'
        AND (a.last_enriched_at IS NULL OR a.original_prompt IS NULL)
        ORDER BY a.id
        LIMIT 30
    """)
    
    lovable_apps = cursor.fetchall()
    conn.close()
    
    logger.info(f"🎯 Found {len(lovable_apps)} Lovable apps to enrich")
    
    if not lovable_apps:
        logger.info("✅ All Lovable apps already enriched")
        return
    
    enriched_count = 0
    prompt_found_count = 0
    
    for app_id, name, url, description, last_enriched in lovable_apps:
        logger.info(f"🔍 Enriching Lovable app: {name}")
        
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
            
            # Rate limiting
            import time
            time.sleep(1)
            
        except Exception as e:
            logger.error(f"❌ Error enriching {name}: {e}")
    
    logger.info(f"🎉 Lovable enrichment completed!")
    logger.info(f"   ✅ Enriched: {enriched_count}")
    logger.info(f"   ✨ Prompts found: {prompt_found_count}")
    
    # Show some examples of found prompts
    if prompt_found_count > 0:
        conn = sqlite3.connect(enricher.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT a.name, a.original_prompt
            FROM applications a
            JOIN platforms p ON a.platform_id = p.id
            WHERE p.name = 'Lovable' 
            AND a.original_prompt IS NOT NULL
            ORDER BY a.last_enriched_at DESC
            LIMIT 3
        """)
        
        examples = cursor.fetchall()
        conn.close()
        
        logger.info("\n🔥 EXAMPLE PROMPTS FOUND:")
        for name, prompt in examples:
            logger.info(f"   📝 {name}:")
            logger.info(f"      {prompt[:200]}...")

if __name__ == "__main__":
    enrich_lovable_apps()