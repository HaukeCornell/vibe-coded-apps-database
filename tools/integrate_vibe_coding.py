#!/usr/bin/env python3
"""
Integrate authentic vibe-coded apps from Lovable and Bolt into the main database.
This focuses on the high-quality prompt-to-app platforms.
"""

import json
import sqlite3
from datetime import datetime
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class VibeCodingIntegrator:
    def __init__(self, db_path='vibe_coded_apps.db'):
        self.db_path = db_path
        self.stats = {
            'lovable_processed': 0,
            'lovable_added': 0,
            'bolt_processed': 0,
            'bolt_added': 0,
            'duplicates_skipped': 0,
            'errors': 0
        }
    
    def init_database(self):
        """Initialize database connection and ensure platforms exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Ensure Lovable platform exists
        cursor.execute("""
            INSERT OR IGNORE INTO platforms (name, description, url)
            VALUES (?, ?, ?)
        """, (
            'Lovable',
            'Prompt-to-app web application generator from lovable.dev',
            'https://lovable.dev'
        ))
        
        # Ensure Bolt platform exists  
        cursor.execute("""
            INSERT OR IGNORE INTO platforms (name, description, url)
            VALUES (?, ?, ?)
        """, (
            'Bolt',
            'Full-stack application generator from bolt.new',
            'https://bolt.new'
        ))
        
        conn.commit()
        return conn
    
    def process_lovable_projects(self, cursor, lovable_file):
        """Process Lovable community projects."""
        try:
            with open(lovable_file, 'r') as f:
                data = json.load(f)
            
            projects = data.get('projects', [])
            logger.info(f"Processing {len(projects)} Lovable projects...")
            
            # Get platform ID
            cursor.execute("SELECT id FROM platforms WHERE name = 'Lovable'")
            platform_id = cursor.fetchone()[0]
            
            for project in projects:
                self.stats['lovable_processed'] += 1
                
                # Extract project data
                app_name = project.get('name', 'Untitled')
                app_description = f"Lovable project by {project.get('user_display_name', 'Unknown')} - {project.get('edit_count', 0)} edits, {project.get('user_message_count', 0)} messages"
                app_url = project.get('url', '')
                external_id = project.get('id', '')
                
                # Check for duplicates
                cursor.execute("""
                    SELECT id FROM applications 
                    WHERE platform_id = ? AND (external_id = ? OR url = ?)
                """, (platform_id, external_id, app_url))
                
                if cursor.fetchone():
                    self.stats['duplicates_skipped'] += 1
                    continue
                
                # Insert application
                cursor.execute("""
                    INSERT INTO applications (
                        name, description, platform_id, url, external_id,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    app_name,
                    app_description,
                    platform_id,
                    app_url,
                    external_id,
                    datetime.now().isoformat(),
                    datetime.now().isoformat()
                ))
                
                self.stats['lovable_added'] += 1
                
        except Exception as e:
            logger.error(f"Error processing Lovable projects: {e}")
            self.stats['errors'] += 1
    
    def process_bolt_projects(self, cursor, bolt_file):
        """Process Bolt gallery projects."""
        try:
            with open(bolt_file, 'r') as f:
                data = json.load(f)
            
            projects = data.get('projects', [])
            logger.info(f"Processing {len(projects)} Bolt projects...")
            
            # Get platform ID
            cursor.execute("SELECT id FROM platforms WHERE name = 'Bolt'")
            platform_id = cursor.fetchone()[0]
            
            for project in projects:
                self.stats['bolt_processed'] += 1
                
                # Skip rejected or unpublished projects for quality
                if project.get('status') == 'rejected' or not project.get('published', True):
                    continue
                
                # Extract project data
                app_name = project.get('title', 'Untitled')
                app_description = project.get('description', f"Bolt project by {project.get('author', 'Unknown')}")
                app_url = project.get('project_url', '')
                external_id = project.get('id', '')
                
                # Check for duplicates
                cursor.execute("""
                    SELECT id FROM applications 
                    WHERE platform_id = ? AND (external_id = ? OR url = ?)
                """, (platform_id, external_id, app_url))
                
                if cursor.fetchone():
                    self.stats['duplicates_skipped'] += 1
                    continue
                
                # Insert application
                cursor.execute("""
                    INSERT INTO applications (
                        name, description, platform_id, url, external_id,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    app_name,
                    app_description,
                    platform_id,
                    app_url,
                    external_id,
                    datetime.now().isoformat(),
                    datetime.now().isoformat()
                ))
                
                self.stats['bolt_added'] += 1
                
        except Exception as e:
            logger.error(f"Error processing Bolt projects: {e}")
            self.stats['errors'] += 1
    
    def integrate_vibe_coding_data(self):
        """Main integration function for authentic vibe-coded apps."""
        logger.info("Starting integration of authentic vibe-coded applications...")
        
        # Find latest data files
        lovable_files = list(Path('.').glob('lovable_community_projects_*.json'))
        bolt_files = list(Path('.').glob('bolt_gallery_projects_*.json'))
        
        if not lovable_files:
            logger.warning("No Lovable data files found!")
        if not bolt_files:
            logger.warning("No Bolt data files found!")
        
        if not lovable_files and not bolt_files:
            logger.error("No data files found to process!")
            return
        
        # Use most recent files
        latest_lovable = max(lovable_files, key=lambda f: f.stat().st_mtime) if lovable_files else None
        latest_bolt = max(bolt_files, key=lambda f: f.stat().st_mtime) if bolt_files else None
        
        # Initialize database
        conn = self.init_database()
        cursor = conn.cursor()
        
        try:
            # Process Lovable projects
            if latest_lovable:
                logger.info(f"Processing Lovable data from {latest_lovable}")
                self.process_lovable_projects(cursor, latest_lovable)
            
            # Process Bolt projects
            if latest_bolt:
                logger.info(f"Processing Bolt data from {latest_bolt}")
                self.process_bolt_projects(cursor, latest_bolt)
            
            # Commit all changes
            conn.commit()
            
        finally:
            conn.close()
        
        # Log final statistics
        logger.info("=== Vibe Coding Integration Complete ===")
        logger.info(f"Lovable projects processed: {self.stats['lovable_processed']}")
        logger.info(f"Lovable projects added: {self.stats['lovable_added']}")
        logger.info(f"Bolt projects processed: {self.stats['bolt_processed']}")
        logger.info(f"Bolt projects added: {self.stats['bolt_added']}")
        logger.info(f"Duplicates skipped: {self.stats['duplicates_skipped']}")
        logger.info(f"Errors encountered: {self.stats['errors']}")
        
        total_added = self.stats['lovable_added'] + self.stats['bolt_added']
        logger.info(f"Total new authentic vibe-coded apps added: {total_added}")
        
        return self.stats

def main():
    """Main function to run the vibe coding integration."""
    integrator = VibeCodingIntegrator()
    stats = integrator.integrate_vibe_coding_data()
    
    logger.info("Integration completed successfully!")

if __name__ == "__main__":
    main()