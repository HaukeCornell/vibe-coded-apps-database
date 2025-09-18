#!/usr/bin/env python3
"""
Vibe Coded Apps Database - Data Processing Pipeline
Processes scraped data from various platforms and imports into unified database
"""

import sqlite3
import json
import os
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from urllib.parse import urlparse
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class VibeCodedAppsDB:
    def __init__(self, db_path: str = "vibe_coded_apps.db"):
        self.db_path = db_path
        self.conn = None
        
    def connect(self):
        """Connect to SQLite database"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        return self.conn
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
    
    def initialize_database(self, schema_file: str = "database_schema.sql"):
        """Initialize database with schema"""
        if not os.path.exists(schema_file):
            raise FileNotFoundError(f"Schema file {schema_file} not found")
        
        with open(schema_file, 'r') as f:
            schema = f.read()
        
        cursor = self.conn.cursor()
        cursor.executescript(schema)
        self.conn.commit()
        logger.info("Database schema initialized")
    
    def get_platform_id(self, platform_name: str) -> Optional[int]:
        """Get platform ID by name"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT id FROM platforms WHERE name = ?", (platform_name,))
        result = cursor.fetchone()
        return result[0] if result else None
    
    def get_or_create_ai_tool(self, name: str, category: str = None, provider: str = None) -> int:
        """Get or create AI tool and return its ID"""
        cursor = self.conn.cursor()
        
        # Check if tool exists
        cursor.execute("SELECT id FROM ai_tools WHERE name = ?", (name,))
        result = cursor.fetchone()
        if result:
            return result[0]
        
        # Create new tool
        cursor.execute(
            "INSERT INTO ai_tools (name, category, provider) VALUES (?, ?, ?)",
            (name, category, provider)
        )
        self.conn.commit()
        return cursor.lastrowid

class GitHubDataProcessor:
    def __init__(self, db: VibeCodedAppsDB):
        self.db = db
    
    def process_github_search_results(self, json_file: str, file_type: str, platform_name: str = "github.com"):
        """Process GitHub API search results (agents_md.json, claude.json, gemini_md.json)"""
        logger.info(f"Processing GitHub data from {json_file} (type: {file_type})")
        
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        platform_id = self.db.get_platform_id(platform_name)
        if not platform_id:
            logger.error(f"Platform {platform_name} not found in database")
            return
        
        total_count = data.get('total_count', 0)
        items = data.get('items', [])
        
        logger.info(f"Found {total_count} total results, processing {len(items)} items")
        
        processed_count = 0
        skipped_count = 0
        
        for item in items:
            try:
                # Extract repository info
                repo_info = item.get('repository', {})
                repo_id = repo_info.get('id')
                
                if not repo_id:
                    skipped_count += 1
                    continue
                
                # Create application entry
                app_data = {
                    'platform_id': platform_id,
                    'external_id': str(repo_id),
                    'name': repo_info.get('full_name', ''),
                    'url': repo_info.get('html_url', ''),
                    'description': repo_info.get('description', ''),
                }
                
                app_id = self._insert_or_update_application(app_data)
                
                # Create GitHub repository entry
                github_data = self._extract_github_repo_data(repo_info, app_id)
                github_repo_id = self._insert_or_update_github_repo(github_data)
                
                # Create repository file entry
                file_data = {
                    'github_repo_id': github_repo_id,
                    'name': item.get('name', ''),
                    'path': item.get('path', ''),
                    'sha': item.get('sha', ''),
                    'file_url': item.get('url', ''),
                    'git_url': item.get('git_url', ''),
                    'html_url': item.get('html_url', ''),
                    'file_type': file_type
                }
                
                self._insert_repository_file(file_data)
                
                # Link AI tool based on file type
                ai_tool_name = self._get_ai_tool_from_file_type(file_type)
                if ai_tool_name:
                    ai_tool_id = self.db.get_or_create_ai_tool(ai_tool_name)
                    self._link_app_to_ai_tool(app_id, ai_tool_id, 'filename', 0.8)
                
                processed_count += 1
                
            except Exception as e:
                logger.error(f"Error processing item: {e}")
                skipped_count += 1
                continue
        
        logger.info(f"GitHub processing complete. Processed: {processed_count}, Skipped: {skipped_count}")
    
    def _extract_github_repo_data(self, repo_info: Dict, app_id: int) -> Dict:
        """Extract GitHub repository data"""
        owner = repo_info.get('owner', {})
        
        return {
            'application_id': app_id,
            'repo_id': repo_info.get('id'),
            'node_id': repo_info.get('node_id'),
            'full_name': repo_info.get('full_name'),
            'private': repo_info.get('private', False),
            'owner_login': owner.get('login'),
            'owner_id': owner.get('id'),
            'owner_type': owner.get('type'),
            'html_url': repo_info.get('html_url'),
            'git_url': repo_info.get('git_url'),
            'clone_url': repo_info.get('clone_url'),
            'ssh_url': repo_info.get('ssh_url'),
            'default_branch': repo_info.get('default_branch'),
            'language': repo_info.get('language'),
            'size_kb': repo_info.get('size'),
            'stargazers_count': repo_info.get('stargazers_count', 0),
            'watchers_count': repo_info.get('watchers_count', 0),
            'forks_count': repo_info.get('forks_count', 0),
            'open_issues_count': repo_info.get('open_issues_count', 0),
            'has_issues': repo_info.get('has_issues', True),
            'has_projects': repo_info.get('has_projects', True),
            'has_wiki': repo_info.get('has_wiki', True),
            'has_pages': repo_info.get('has_pages', False),
            'archived': repo_info.get('archived', False),
            'disabled': repo_info.get('disabled', False),
            'pushed_at': self._parse_github_date(repo_info.get('pushed_at')),
            'created_at': self._parse_github_date(repo_info.get('created_at')),
            'updated_at': self._parse_github_date(repo_info.get('updated_at')),
        }
    
    def _parse_github_date(self, date_str: str) -> Optional[str]:
        """Parse GitHub date format to SQLite format"""
        if not date_str:
            return None
        try:
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            return None
    
    def _get_ai_tool_from_file_type(self, file_type: str) -> Optional[str]:
        """Map file type to AI tool name"""
        mapping = {
            'agents_md': 'AI Agents',
            'claude_md': 'Claude',
            'gemini_md': 'Gemini',
        }
        return mapping.get(file_type)
    
    def _insert_or_update_application(self, app_data: Dict) -> int:
        """Insert or update application and return ID"""
        cursor = self.db.conn.cursor()
        
        # Check if exists
        cursor.execute(
            "SELECT id FROM applications WHERE platform_id = ? AND external_id = ?",
            (app_data['platform_id'], app_data['external_id'])
        )
        result = cursor.fetchone()
        
        if result:
            # Update existing
            app_id = result[0]
            cursor.execute("""
                UPDATE applications 
                SET name = ?, url = ?, description = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (app_data['name'], app_data['url'], app_data['description'], app_id))
        else:
            # Insert new
            cursor.execute("""
                INSERT INTO applications (platform_id, external_id, name, url, description)
                VALUES (?, ?, ?, ?, ?)
            """, (app_data['platform_id'], app_data['external_id'], 
                  app_data['name'], app_data['url'], app_data['description']))
            app_id = cursor.lastrowid
        
        self.db.conn.commit()
        return app_id
    
    def _insert_or_update_github_repo(self, github_data: Dict) -> int:
        """Insert or update GitHub repository and return ID"""
        cursor = self.db.conn.cursor()
        
        # Check if exists
        cursor.execute("SELECT id FROM github_repositories WHERE repo_id = ?", (github_data['repo_id'],))
        result = cursor.fetchone()
        
        if result:
            # Update existing
            github_repo_id = result[0]
            # Update key fields
            cursor.execute("""
                UPDATE github_repositories 
                SET stargazers_count = ?, forks_count = ?, open_issues_count = ?,
                    language = ?, size_kb = ?, updated_at = ?
                WHERE id = ?
            """, (github_data['stargazers_count'], github_data['forks_count'],
                  github_data['open_issues_count'], github_data['language'],
                  github_data['size_kb'], github_data['updated_at'], github_repo_id))
        else:
            # Insert new
            fields = ', '.join(github_data.keys())
            placeholders = ', '.join(['?' for _ in github_data])
            cursor.execute(f"INSERT INTO github_repositories ({fields}) VALUES ({placeholders})",
                          list(github_data.values()))
            github_repo_id = cursor.lastrowid
        
        self.db.conn.commit()
        return github_repo_id
    
    def _insert_repository_file(self, file_data: Dict):
        """Insert repository file entry"""
        cursor = self.db.conn.cursor()
        
        # Insert or ignore (unique constraint on github_repo_id, path)
        cursor.execute("""
            INSERT OR IGNORE INTO repository_files 
            (github_repo_id, name, path, sha, file_url, git_url, html_url, file_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (file_data['github_repo_id'], file_data['name'], file_data['path'],
              file_data['sha'], file_data['file_url'], file_data['git_url'],
              file_data['html_url'], file_data['file_type']))
        
        self.db.conn.commit()
    
    def _link_app_to_ai_tool(self, app_id: int, ai_tool_id: int, detection_method: str, confidence: float):
        """Link application to AI tool"""
        cursor = self.db.conn.cursor()
        cursor.execute("""
            INSERT OR IGNORE INTO application_ai_tools 
            (application_id, ai_tool_id, confidence_score, detection_method)
            VALUES (?, ?, ?, ?)
        """, (app_id, ai_tool_id, confidence, detection_method))
        self.db.conn.commit()

class V0DataProcessor:
    def __init__(self, db: VibeCodedAppsDB):
        self.db = db
    
    def process_v0_urls(self, json_file: str, platform_name: str = "v0.dev"):
        """Process v0.dev community URLs"""
        logger.info(f"Processing v0.dev data from {json_file}")
        
        with open(json_file, 'r') as f:
            urls = json.load(f)
        
        platform_id = self.db.get_platform_id(platform_name)
        if not platform_id:
            logger.error(f"Platform {platform_name} not found in database")
            return
        
        logger.info(f"Processing {len(urls)} v0.dev URLs")
        
        processed_count = 0
        skipped_count = 0
        
        for url in urls:
            try:
                # Extract ID from URL (e.g., https://v0.app/community/12345)
                community_id = self._extract_v0_id(url)
                if not community_id:
                    skipped_count += 1
                    continue
                
                # Create application entry
                app_data = {
                    'platform_id': platform_id,
                    'external_id': community_id,
                    'name': f"v0 Community App {community_id}",
                    'url': url,
                    'description': 'v0.dev community application'
                }
                
                app_id = self._insert_or_update_application(app_data)
                
                # Create community app entry
                community_data = {
                    'application_id': app_id,
                    'community_url': url,
                    'community_id': community_id
                }
                
                self._insert_community_app(community_data)
                
                # Link to v0 AI tool
                ai_tool_id = self.db.get_or_create_ai_tool('v0', 'code_generator', 'Vercel')
                self._link_app_to_ai_tool(app_id, ai_tool_id, 'platform_detection', 1.0)
                
                processed_count += 1
                
            except Exception as e:
                logger.error(f"Error processing URL {url}: {e}")
                skipped_count += 1
                continue
        
        logger.info(f"v0.dev processing complete. Processed: {processed_count}, Skipped: {skipped_count}")
    
    def _extract_v0_id(self, url: str) -> Optional[str]:
        """Extract ID from v0.dev URL"""
        # Pattern: https://v0.app/community/some-id
        match = re.search(r'/community/([^/?]+)', url)
        return match.group(1) if match else None
    
    def _insert_or_update_application(self, app_data: Dict) -> int:
        """Insert or update application and return ID"""
        cursor = self.db.conn.cursor()
        
        # Check if exists
        cursor.execute(
            "SELECT id FROM applications WHERE platform_id = ? AND external_id = ?",
            (app_data['platform_id'], app_data['external_id'])
        )
        result = cursor.fetchone()
        
        if result:
            app_id = result[0]
            cursor.execute("""
                UPDATE applications 
                SET name = ?, url = ?, description = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (app_data['name'], app_data['url'], app_data['description'], app_id))
        else:
            cursor.execute("""
                INSERT INTO applications (platform_id, external_id, name, url, description)
                VALUES (?, ?, ?, ?, ?)
            """, (app_data['platform_id'], app_data['external_id'], 
                  app_data['name'], app_data['url'], app_data['description']))
            app_id = cursor.lastrowid
        
        self.db.conn.commit()
        return app_id
    
    def _insert_community_app(self, community_data: Dict):
        """Insert community app entry"""
        cursor = self.db.conn.cursor()
        cursor.execute("""
            INSERT OR IGNORE INTO community_apps (application_id, community_url, community_id)
            VALUES (?, ?, ?)
        """, (community_data['application_id'], community_data['community_url'], 
              community_data['community_id']))
        self.db.conn.commit()
    
    def _link_app_to_ai_tool(self, app_id: int, ai_tool_id: int, detection_method: str, confidence: float):
        """Link application to AI tool"""
        cursor = self.db.conn.cursor()
        cursor.execute("""
            INSERT OR IGNORE INTO application_ai_tools 
            (application_id, ai_tool_id, confidence_score, detection_method)
            VALUES (?, ?, ?, ?)
        """, (app_id, ai_tool_id, confidence, detection_method))
        self.db.conn.commit()

def main():
    """Main processing function"""
    # Initialize database
    db = VibeCodedAppsDB()
    db.connect()
    
    # Initialize schema if database is empty
    cursor = db.conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='platforms'")
    if cursor.fetchone()[0] == 0:
        logger.info("Initializing database schema...")
        db.initialize_database()
    
    # Initialize processors
    github_processor = GitHubDataProcessor(db)
    v0_processor = V0DataProcessor(db)
    
    # Process data files
    data_dir = "First-Scrape"
    
    try:
        # Process GitHub data
        github_files = [
            ("agents_md.json", "agents_md"),
            ("claude.json", "claude_md"), 
            ("gemini_md.json", "gemini_md")
        ]
        
        for filename, file_type in github_files:
            filepath = os.path.join(data_dir, filename)
            if os.path.exists(filepath):
                github_processor.process_github_search_results(filepath, file_type)
            else:
                logger.warning(f"File not found: {filepath}")
        
        # Process v0.dev data
        v0_file = os.path.join(data_dir, "v0.json")
        if os.path.exists(v0_file):
            v0_processor.process_v0_urls(v0_file)
        else:
            logger.warning(f"File not found: {v0_file}")
        
        # Generate statistics
        logger.info("Generating statistics...")
        cursor.execute("SELECT * FROM platform_statistics")
        stats = cursor.fetchall()
        
        print("\n=== PLATFORM STATISTICS ===")
        for row in stats:
            print(f"{row[0]}: {row[1]} apps")
        
        cursor.execute("SELECT COUNT(*) as total FROM applications WHERE is_active = TRUE")
        total = cursor.fetchone()[0]
        print(f"\nTotal Active Applications: {total}")
        
    except Exception as e:
        logger.error(f"Error in main processing: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    main()