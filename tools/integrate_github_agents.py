#!/usr/bin/env python3
"""
Integrate GitHub AGENTS.md search results into the main database.
This processes the GitHub search results and adds new repositories and applications
to our vibe-coded apps database.
"""

import json
import sqlite3
from datetime import datetime
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GitHubAgentsIntegrator:
    def __init__(self, db_path='vibe_coded_apps.db'):
        self.db_path = db_path
        self.stats = {
            'repositories_processed': 0,
            'repositories_added': 0,
            'applications_added': 0,
            'duplicates_skipped': 0,
            'errors': 0
        }
    
    def load_github_results(self, results_file):
        """Load GitHub search results from JSON file."""
        try:
            with open(results_file, 'r') as f:
                data = json.load(f)
            
            logger.info(f"Loaded {data['total_files']} GitHub results from {results_file}")
            return data['results_by_type']['agents']
        
        except Exception as e:
            logger.error(f"Error loading GitHub results: {e}")
            return []
    
    def init_database(self):
        """Initialize database connection and ensure tables exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Ensure platform exists for GitHub
        cursor.execute("""
            INSERT OR IGNORE INTO platforms (name, description, url)
            VALUES (?, ?, ?)
        """, (
            'GitHub',
            'Code repositories with AGENTS.md files indicating vibe-coded applications',
            'https://github.com'
        ))
        
        conn.commit()
        return conn
    
    def process_repository(self, cursor, repo_data):
        """Process a single repository and extract application information."""
        try:
            # Get platform ID
            cursor.execute("SELECT id FROM platforms WHERE name = 'GitHub'")
            platform_id = cursor.fetchone()[0]
            
            # Check if repository already exists
            cursor.execute("""
                SELECT id FROM github_repositories 
                WHERE repo_id = ? OR full_name = ?
            """, (repo_data['repository_id'], repo_data['repository_full_name']))
            
            existing_repo = cursor.fetchone()
            if existing_repo:
                self.stats['duplicates_skipped'] += 1
                return existing_repo[0]
            
            # Create application entry first
            app_name = repo_data['repository_name']
            app_description = repo_data['repository_description'] or f"Vibe-coded application: {app_name}"
            
            # Check if application already exists
            cursor.execute("""
                SELECT id FROM applications 
                WHERE LOWER(name) = LOWER(?) AND platform_id = ?
            """, (app_name, platform_id))
            
            existing_app = cursor.fetchone()
            if existing_app:
                application_id = existing_app[0]
            else:
                cursor.execute("""
                    INSERT INTO applications (
                        name, description, platform_id, url,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    app_name,
                    app_description,
                    platform_id,
                    repo_data['repository_url'],
                    datetime.now().isoformat(),
                    datetime.now().isoformat()
                ))
                
                application_id = cursor.lastrowid
                self.stats['applications_added'] += 1
            
            # Insert new repository
            cursor.execute("""
                INSERT INTO github_repositories (
                    application_id, repo_id, full_name,
                    html_url, language, stargazers_count, forks_count,
                    owner_login, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                application_id,
                repo_data['repository_id'],
                repo_data['repository_full_name'],
                repo_data['repository_url'],
                repo_data['repository_language'],
                repo_data['repository_stars'],
                repo_data['repository_forks'],
                repo_data['repository_owner'],
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
            
            github_repo_id = cursor.lastrowid
            self.stats['repositories_added'] += 1
            
            return github_repo_id
            
        except Exception as e:
            logger.error(f"Error processing repository {repo_data.get('repository_full_name', 'unknown')}: {e}")
            self.stats['errors'] += 1
            return None
    
    def integrate_results(self, results_file):
        """Main integration function."""
        logger.info(f"Starting GitHub AGENTS.md integration from {results_file}")
        
        # Load results
        github_results = self.load_github_results(results_file)
        if not github_results:
            logger.error("No GitHub results to process")
            return
        
        # Initialize database
        conn = self.init_database()
        cursor = conn.cursor()
        
        try:
            # Process each repository
            for i, repo_data in enumerate(github_results, 1):
                self.stats['repositories_processed'] += 1
                
                if i % 100 == 0:
                    logger.info(f"Processed {i}/{len(github_results)} repositories...")
                    conn.commit()  # Commit periodically
                
                self.process_repository(cursor, repo_data)
            
            # Final commit
            conn.commit()
            
            logger.info("GitHub AGENTS.md data integration completed successfully!")
            
        finally:
            conn.close()
        
        # Log final statistics
        logger.info("=== GitHub AGENTS.md Integration Complete ===")
        logger.info(f"Repositories processed: {self.stats['repositories_processed']}")
        logger.info(f"New repositories added: {self.stats['repositories_added']}")
        logger.info(f"New applications added: {self.stats['applications_added']}")
        logger.info(f"Duplicates skipped: {self.stats['duplicates_skipped']}")
        logger.info(f"Errors encountered: {self.stats['errors']}")
        
        return self.stats

def main():
    """Main function to run the GitHub AGENTS.md integration."""
    # Find the most recent GitHub results file
    results_files = list(Path('.').glob('github_code_search_results_*.json'))
    if not results_files:
        logger.error("No GitHub search results files found!")
        logger.error("Please run github_enhanced_search.py first.")
        return
    
    # Use the most recent file
    latest_file = max(results_files, key=lambda f: f.stat().st_mtime)
    logger.info(f"Using results file: {latest_file}")
    
    # Run integration
    integrator = GitHubAgentsIntegrator()
    stats = integrator.integrate_results(latest_file)
    
    logger.info(f"Integration completed successfully!")

if __name__ == "__main__":
    main()