#!/usr/bin/env python3
"""
Data Integration Script
Combines all scraped data sources into the unified SQLite database.

This script processes:
- Bolt Supabase projects (1,227 projects)
- Lovable community projects (99 projects) 
- Jules GitHub PRs (1,000+ PRs)
- Original scraped data (2,051 apps)

Total expected: ~4,377+ apps
"""

import json
import sqlite3
import logging
import os
from datetime import datetime
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataIntegrator:
    """Integrates all scraped data sources into unified database."""
    
    def __init__(self, db_path="/Users/hgs52/Documents/Github/vibe-coded-apps-database/vibe_apps.db"):
        self.db_path = db_path
        self.data_dir = "/Users/hgs52/Documents/Github/vibe-coded-apps-database/data"
        self.scraped_data_dir = "/Users/hgs52/Documents/Github/vibe-coded-apps-database/scraped_data"
        self.first_scrape_dir = "/Users/hgs52/Documents/Github/vibe-coded-apps-database/First-Scrape"
        self.stats = {
            'total_processed': 0,
            'bolt_projects': 0,
            'lovable_projects': 0,
            'jules_prs': 0,
            'original_apps': 0,
            'duplicates_skipped': 0,
            'errors': 0
        }
        
    def setup_database(self):
        """Ensure database tables exist with latest schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create enhanced schema for new data sources
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS apps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                description TEXT,
                url TEXT UNIQUE,
                source_platform TEXT,
                created_at TEXT,
                updated_at TEXT,
                stars INTEGER,
                language TEXT,
                license TEXT,
                topics TEXT,
                raw_data TEXT,
                UNIQUE(url, source_platform)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS platforms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                description TEXT,
                base_url TEXT,
                scraping_method TEXT,
                last_scraped TEXT,
                total_apps INTEGER DEFAULT 0
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS github_repos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                app_id INTEGER,
                repo_url TEXT UNIQUE,
                owner TEXT,
                name TEXT,
                stars INTEGER,
                forks INTEGER,
                language TEXT,
                created_at TEXT,
                updated_at TEXT,
                FOREIGN KEY (app_id) REFERENCES apps (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_tools (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                app_id INTEGER,
                tool_name TEXT,
                tool_version TEXT,
                usage_context TEXT,
                FOREIGN KEY (app_id) REFERENCES apps (id)
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Database schema updated")
        
    def load_json_file(self, filename, directory=None):
        """Load data from JSON file."""
        if directory is None:
            directory = self.data_dir
            
        filepath = os.path.join(directory, filename)
        if not os.path.exists(filepath):
            logger.warning(f"File not found: {filepath}")
            return []
            
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info(f"Loaded {len(data)} items from {filename}")
            return data
        except Exception as e:
            logger.error(f"Error loading {filename}: {e}")
            return []
    
    def insert_platform(self, conn, name, description, base_url, method):
        """Insert or update platform record."""
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO platforms 
            (name, description, base_url, scraping_method, last_scraped)
            VALUES (?, ?, ?, ?, ?)
        ''', (name, description, base_url, method, datetime.now().isoformat()))
        return cursor.lastrowid
    
    def insert_app(self, conn, app_data):
        """Insert app with duplicate checking."""
        cursor = conn.cursor()
        
        try:
            # Check for duplicates based on URL
            if app_data.get('url'):
                cursor.execute('SELECT id FROM apps WHERE url = ?', (app_data['url'],))
                if cursor.fetchone():
                    self.stats['duplicates_skipped'] += 1
                    return None
            
            # Insert app
            cursor.execute('''
                INSERT OR IGNORE INTO apps 
                (name, description, url, source_platform, created_at, updated_at, 
                 stars, language, license, topics, raw_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                app_data.get('name', ''),
                app_data.get('description', ''),
                app_data.get('url', ''),
                app_data.get('source_platform', ''),
                app_data.get('created_at', datetime.now().isoformat()),
                datetime.now().isoformat(),
                app_data.get('stars', 0),
                app_data.get('language', ''),
                app_data.get('license', ''),
                json.dumps(app_data.get('topics', [])),
                json.dumps(app_data)
            ))
            
            app_id = cursor.lastrowid
            if app_id:
                self.stats['total_processed'] += 1
                return app_id
            else:
                self.stats['duplicates_skipped'] += 1
                return None
                
        except Exception as e:
            logger.error(f"Error inserting app: {e}")
            self.stats['errors'] += 1
            return None
    
    def process_bolt_projects(self, conn):
        """Process Bolt Supabase projects."""
        logger.info("Processing Bolt projects...")
        
        # Insert platform
        self.insert_platform(conn, 'Bolt', 'Bolt.new Supabase gallery projects', 
                           'https://bolt.new', 'supabase_api')
        
        # Try different possible filenames and locations
        possible_files = [
            ('bolt_projects.json', self.data_dir),
            ('bolt_apps_20250917_194907.json', self.scraped_data_dir),
            ('bolt.json', self.first_scrape_dir)
        ]
        
        projects = []
        for filename, directory in possible_files:
            data = self.load_json_file(filename, directory)
            if data:
                projects = data
                break
        
        for project in projects:
            app_data = {
                'name': project.get('title', project.get('name', '')),
                'description': project.get('description', ''),
                'url': project.get('url', ''),
                'source_platform': 'bolt',
                'created_at': project.get('created_at', ''),
                'stars': project.get('star_count', 0),
                'language': project.get('primary_language', ''),
                'topics': project.get('tags', []),
                'raw_data': project
            }
            
            app_id = self.insert_app(conn, app_data)
            if app_id:
                self.stats['bolt_projects'] += 1
                
        logger.info(f"Processed {self.stats['bolt_projects']} Bolt projects")
    
    def process_lovable_projects(self, conn):
        """Process Lovable community projects."""
        logger.info("Processing Lovable projects...")
        
        # Insert platform
        self.insert_platform(conn, 'Lovable', 'Lovable.dev community projects', 
                           'https://lovable.dev', 'api')
        
        # Try different possible filenames and locations
        possible_files = [
            ('lovable_projects.json', self.data_dir),
            ('lovable_apps_20250917_194907.json', self.scraped_data_dir),
            ('lovable.json', self.first_scrape_dir)
        ]
        
        projects = []
        for filename, directory in possible_files:
            data = self.load_json_file(filename, directory)
            if data:
                projects = data
                break
        
        for project in projects:
            app_data = {
                'name': project.get('name', project.get('title', '')),
                'description': project.get('description', ''),
                'url': project.get('url', project.get('project_url', '')),
                'source_platform': 'lovable',
                'created_at': project.get('created_at', ''),
                'language': project.get('technology', ''),
                'topics': project.get('tags', []),
                'raw_data': project
            }
            
            app_id = self.insert_app(conn, app_data)
            if app_id:
                self.stats['lovable_projects'] += 1
                
        logger.info(f"Processed {self.stats['lovable_projects']} Lovable projects")
    
    def process_jules_prs(self, conn):
        """Process Jules GitHub PRs."""
        logger.info("Processing Jules PRs...")
        
        # Insert platform
        self.insert_platform(conn, 'Jules', 'Google Jules AI assistant pull requests', 
                           'https://github.com', 'github_api')
        
        # Try different possible filenames and locations
        possible_files = [
            ('jules_prs.json', self.data_dir),
            ('jules_github_prs.json', self.scraped_data_dir),
            ('jules.json', self.first_scrape_dir)
        ]
        
        prs = []
        for filename, directory in possible_files:
            data = self.load_json_file(filename, directory)
            if data:
                prs = data
                break
        
        for pr in prs:
            app_data = {
                'name': pr.get('title', ''),
                'description': pr.get('body', '')[:500] if pr.get('body') else '',
                'url': pr.get('html_url', ''),
                'source_platform': 'jules',
                'created_at': pr.get('created_at', ''),
                'language': 'Multiple',  # Jules works with multiple languages
                'topics': ['ai-assistant', 'google-jules'],
                'raw_data': pr
            }
            
            app_id = self.insert_app(conn, app_data)
            if app_id:
                self.stats['jules_prs'] += 1
                
                # Add GitHub repo info if available
                if pr.get('base', {}).get('repo'):
                    repo = pr['base']['repo']
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT OR IGNORE INTO github_repos 
                        (app_id, repo_url, owner, name, stars, forks, language, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        app_id,
                        repo.get('html_url', ''),
                        repo.get('owner', {}).get('login', ''),
                        repo.get('name', ''),
                        repo.get('stargazers_count', 0),
                        repo.get('forks_count', 0),
                        repo.get('language', ''),
                        repo.get('created_at', ''),
                        repo.get('updated_at', '')
                    ))
                
        logger.info(f"Processed {self.stats['jules_prs']} Jules PRs")
    
    def process_original_data(self, conn):
        """Process original scraped data."""
        logger.info("Processing original scraped data...")
        
        # Process existing JSON files from original scraping
        original_files = [
            ('agents_md.json', 'Agents Md'),
            ('claude.json', 'Claude'), 
            ('gemini_md.json', 'Gemini Md'),
            ('lovable.json', 'Lovable Original'),
            ('v0.json', 'V0 Original')
        ]
        
        for filename, platform_name in original_files:
            # Insert platform
            self.insert_platform(conn, platform_name, f'Original {platform_name} scraping data', 
                               '', 'original_scraping')
            
            data = self.load_json_file(filename, self.first_scrape_dir)
            
            # Handle different data structures
            if isinstance(data, dict) and 'items' in data:
                # GitHub API response format
                items = data['items']
            elif isinstance(data, list):
                # Direct list format
                items = data
            else:
                logger.warning(f"Unknown data format in {filename}: {type(data)}")
                continue
                
            for item in items:
                # Extract meaningful information from GitHub API response
                if filename == 'claude.json':
                    # GitHub API response for Claude files
                    repo = item.get('repository', {})
                    app_data = {
                        'name': repo.get('name', ''),
                        'description': repo.get('description', '')[:500] if repo.get('description') else '',
                        'url': repo.get('html_url', ''),
                        'source_platform': platform_name.lower().replace(' ', '_'),
                        'created_at': repo.get('created_at', ''),
                        'language': repo.get('language', ''),
                        'topics': [],
                        'stars': repo.get('stargazers_count', 0),
                        'raw_data': item
                    }
                else:
                    # Regular format for other files
                    app_data = {
                        'name': item.get('name', item.get('title', '')),
                        'description': item.get('description', item.get('summary', ''))[:500] if item.get('description', item.get('summary', '')) else '',
                        'url': item.get('url', item.get('link', '')),
                        'source_platform': platform_name.lower().replace(' ', '_'),
                        'created_at': item.get('created_at', item.get('date', '')),
                        'language': item.get('language', ''),
                        'topics': item.get('tags', item.get('topics', [])),
                        'raw_data': item
                    }
                
                app_id = self.insert_app(conn, app_data)
                if app_id:
                    self.stats['original_apps'] += 1
        
        # Also process scraped_data files if different
        scraped_files = [
            ('v0_community_20250917_194905.json', 'V0 Community')
        ]
        
        for filename, platform_name in scraped_files:
            self.insert_platform(conn, platform_name, f'{platform_name} scraping data', 
                               '', 'scraped_data')
            
            data = self.load_json_file(filename, self.scraped_data_dir)
            
            # Handle different data structures
            if isinstance(data, list):
                items = data
            else:
                logger.warning(f"Unknown data format in {filename}: {type(data)}")
                continue
                
            for item in items:
                app_data = {
                    'name': item.get('name', item.get('title', '')),
                    'description': item.get('description', item.get('summary', ''))[:500] if item.get('description', item.get('summary', '')) else '',
                    'url': item.get('url', item.get('link', '')),
                    'source_platform': platform_name.lower().replace(' ', '_'),
                    'created_at': item.get('created_at', item.get('date', '')),
                    'language': item.get('language', ''),
                    'topics': item.get('tags', item.get('topics', [])),
                    'raw_data': item
                }
                
                app_id = self.insert_app(conn, app_data)
                if app_id:
                    self.stats['original_apps'] += 1
        
        logger.info(f"Processed {self.stats['original_apps']} original apps")
    
    def update_platform_stats(self, conn):
        """Update platform statistics."""
        cursor = conn.cursor()
        
        # Update app counts per platform
        cursor.execute('''
            UPDATE platforms 
            SET total_apps = (
                SELECT COUNT(*) FROM apps 
                WHERE apps.source_platform = platforms.name COLLATE NOCASE
            )
        ''')
        
        conn.commit()
        logger.info("Updated platform statistics")
    
    def generate_stats_report(self):
        """Generate comprehensive statistics report."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get platform statistics
        cursor.execute('''
            SELECT name, total_apps, last_scraped 
            FROM platforms 
            ORDER BY total_apps DESC
        ''')
        platforms = cursor.fetchall()
        
        # Get total counts
        cursor.execute('SELECT COUNT(*) FROM apps')
        total_apps = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM github_repos')
        total_repos = cursor.fetchone()[0]
        
        # Get language statistics
        cursor.execute('''
            SELECT language, COUNT(*) as count 
            FROM apps 
            WHERE language != '' 
            GROUP BY language 
            ORDER BY count DESC 
            LIMIT 10
        ''')
        languages = cursor.fetchall()
        
        conn.close()
        
        # Print comprehensive report
        report = f"""
=== VIBE CODED APPS DATABASE INTEGRATION REPORT ===

Processing Statistics:
- Total apps processed: {self.stats['total_processed']}
- Bolt projects: {self.stats['bolt_projects']}
- Lovable projects: {self.stats['lovable_projects']}
- Jules PRs: {self.stats['jules_prs']}
- Original apps: {self.stats['original_apps']}
- Duplicates skipped: {self.stats['duplicates_skipped']}
- Errors: {self.stats['errors']}

Database Totals:
- Total apps in database: {total_apps}
- Total GitHub repos: {total_repos}

Platform Breakdown:
"""
        for platform, count, last_scraped in platforms:
            report += f"- {platform}: {count} apps (last scraped: {last_scraped})\n"
        
        report += f"\nTop Programming Languages:\n"
        for lang, count in languages:
            report += f"- {lang}: {count} apps\n"
        
        logger.info(report)
        return report
    
    def run_integration(self):
        """Run complete data integration process."""
        logger.info("Starting data integration...")
        
        # Setup database
        self.setup_database()
        
        # Process all data sources
        conn = sqlite3.connect(self.db_path)
        try:
            self.process_bolt_projects(conn)
            self.process_lovable_projects(conn)
            self.process_jules_prs(conn)
            self.process_original_data(conn)
            
            # Update statistics
            self.update_platform_stats(conn)
            conn.commit()
            
        except Exception as e:
            logger.error(f"Error during integration: {e}")
            conn.rollback()
        finally:
            conn.close()
        
        # Generate report
        return self.generate_stats_report()

def main():
    """Main execution function."""
    integrator = DataIntegrator()
    report = integrator.run_integration()
    
    # Save report to file
    report_path = "/Users/hgs52/Documents/Github/vibe-coded-apps-database/integration_report.txt"
    with open(report_path, 'w') as f:
        f.write(report)
    
    logger.info(f"Integration complete! Report saved to {report_path}")

if __name__ == "__main__":
    main()