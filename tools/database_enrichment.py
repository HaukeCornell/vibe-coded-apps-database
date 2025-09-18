#!/usr/bin/env python3
"""
Database Enrichment with Prompts and Metadata

Enhances the database with additional information including:
- Original prompts from GitHub repositories
- Tech stack analysis
- Categories and tags
- Enhanced descriptions
- Community metrics (stars, forks, etc.)
"""

import sqlite3
import requests
import json
import re
import time
import logging
from datetime import datetime
from pathlib import Path
import sys
from urllib.parse import urlparse
import base64

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseEnricher:
    def __init__(self, github_token=None):
        """Initialize database enricher."""
        self.project_root = project_root
        self.db_path = self.project_root / "vibe_coded_apps.db"
        self.github_token = github_token or self._get_github_token()
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Vibe-Coded-Apps-Database/1.0',
            'Accept': 'application/vnd.github.v3+json'
        })
        
        if self.github_token:
            self.session.headers['Authorization'] = f'token {self.github_token}'
            logger.info("✅ GitHub token configured")
        else:
            logger.warning("⚠️ No GitHub token - limited to 60 requests/hour")
        
        # Enhancement patterns
        self.prompt_patterns = [
            # Common prompt indicators
            r'(?i)prompt[:\s]*["\']([^"\']+)["\']',
            r'(?i)description[:\s]*["\']([^"\']+)["\']',
            r'(?i)build[:\s]*["\']([^"\']+)["\']',
            r'(?i)create[:\s]*["\']([^"\']+)["\']',
            r'(?i)generate[:\s]*["\']([^"\']+)["\']',
            
            # Specific platform patterns
            r'(?i)lovable[:\s]*["\']([^"\']+)["\']',
            r'(?i)v0[:\s]*["\']([^"\']+)["\']',
            r'(?i)bolt[:\s]*["\']([^"\']+)["\']',
            
            # README sections
            r'(?i)## prompt\s*\n([^\n#]+)',
            r'(?i)## description\s*\n([^\n#]+)',
            r'(?i)## what this does\s*\n([^\n#]+)',
        ]
        
        self.tech_stack_patterns = {
            'react': r'(?i)\b(react|jsx|tsx)\b',
            'vue': r'(?i)\bvue\b',
            'angular': r'(?i)\bangular\b',
            'svelte': r'(?i)\bsvelte\b',
            'nextjs': r'(?i)\bnext\.?js\b',
            'nuxt': r'(?i)\bnuxt\b',
            'typescript': r'(?i)\btypescript\b',
            'javascript': r'(?i)\bjavascript\b',
            'python': r'(?i)\bpython\b',
            'node': r'(?i)\bnode\.?js\b',
            'express': r'(?i)\bexpress\b',
            'fastapi': r'(?i)\bfastapi\b',
            'django': r'(?i)\bdjango\b',
            'flask': r'(?i)\bflask\b',
            'tailwind': r'(?i)\btailwind\b',
            'bootstrap': r'(?i)\bbootstrap\b',
            'css': r'(?i)\bcss\b',
            'scss': r'(?i)\bscss\b',
            'mongodb': r'(?i)\bmongodb\b',
            'postgresql': r'(?i)\bpostgresql\b',
            'mysql': r'(?i)\bmysql\b',
            'sqlite': r'(?i)\bsqlite\b',
            'supabase': r'(?i)\bsupabase\b',
            'firebase': r'(?i)\bfirebase\b',
            'prisma': r'(?i)\bprisma\b'
        }
    
    def _get_github_token(self):
        """Get GitHub token from environment or return None."""
        import os
        return os.getenv('GITHUB_TOKEN')
    
    def setup_enhanced_schema(self):
        """Add new columns for enhanced metadata."""
        logger.info("🏗️ Setting up enhanced database schema...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Add new columns if they don't exist
        new_columns = [
            ('original_prompt', 'TEXT'),
            ('tech_stack', 'TEXT'),  # JSON array
            ('category', 'VARCHAR(100)'),
            ('tags', 'TEXT'),  # JSON array
            ('github_stars', 'INTEGER DEFAULT 0'),
            ('github_forks', 'INTEGER DEFAULT 0'),
            ('github_language', 'VARCHAR(50)'),
            ('enhanced_description', 'TEXT'),
            ('last_enriched_at', 'TIMESTAMP')
        ]
        
        for column_name, column_type in new_columns:
            try:
                cursor.execute(f"ALTER TABLE applications ADD COLUMN {column_name} {column_type}")
                logger.info(f"➕ Added column: {column_name}")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e):
                    logger.debug(f"Column {column_name} already exists")
                else:
                    logger.error(f"Error adding column {column_name}: {e}")
        
        conn.commit()
        conn.close()
        logger.info("✅ Schema enhancement completed")
    
    def get_github_apps_to_enrich(self, limit=100):
        """Get GitHub applications that need enrichment."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get GitHub apps that haven't been enriched recently
        cursor.execute("""
            SELECT a.id, a.name, a.url, a.description, a.last_enriched_at
            FROM applications a
            JOIN platforms p ON a.platform_id = p.id
            WHERE p.name IN ('GitHub', 'Lovable') 
            AND a.url LIKE '%github.com%'
            AND (a.last_enriched_at IS NULL OR a.last_enriched_at < datetime('now', '-7 days'))
            ORDER BY a.last_enriched_at ASC NULLS FIRST
            LIMIT ?
        """, (limit,))
        
        apps = cursor.fetchall()
        conn.close()
        
        logger.info(f"📋 Found {len(apps)} GitHub apps to enrich")
        return apps
    
    def extract_github_info(self, github_url):
        """Extract owner and repo from GitHub URL."""
        try:
            parsed = urlparse(github_url)
            path_parts = parsed.path.strip('/').split('/')
            
            if len(path_parts) >= 2:
                return path_parts[0], path_parts[1]
        except:
            pass
        
        return None, None
    
    def fetch_github_repository_data(self, owner, repo):
        """Fetch repository data from GitHub API."""
        try:
            # Get basic repository info
            repo_url = f"https://api.github.com/repos/{owner}/{repo}"
            response = self.session.get(repo_url)
            
            if response.status_code == 200:
                repo_data = response.json()
                
                # Get README content
                readme_content = self.fetch_readme_content(owner, repo)
                
                return {
                    'repo_data': repo_data,
                    'readme_content': readme_content,
                    'success': True
                }
            else:
                logger.warning(f"❌ Failed to fetch {owner}/{repo}: {response.status_code}")
                return {'success': False, 'error': response.status_code}
        
        except Exception as e:
            logger.error(f"❌ Error fetching {owner}/{repo}: {e}")
            return {'success': False, 'error': str(e)}
    
    def fetch_readme_content(self, owner, repo):
        """Fetch README content from repository."""
        readme_files = ['README.md', 'readme.md', 'README.txt', 'readme.txt']
        
        for readme_file in readme_files:
            try:
                content_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{readme_file}"
                response = self.session.get(content_url)
                
                if response.status_code == 200:
                    content_data = response.json()
                    
                    if content_data.get('encoding') == 'base64':
                        readme_content = base64.b64decode(content_data['content']).decode('utf-8')
                        return readme_content
            except:
                continue
        
        return None
    
    def extract_prompt_from_content(self, readme_content, repo_data):
        """Extract original prompt from README content."""
        if not readme_content:
            return None
        
        # Try each pattern
        for pattern in self.prompt_patterns:
            matches = re.findall(pattern, readme_content, re.MULTILINE | re.DOTALL)
            if matches:
                # Return the longest match (likely most complete)
                prompt = max(matches, key=len).strip()
                if len(prompt) > 20:  # Filter out very short matches
                    return prompt
        
        # Fallback: use repository description if it looks like a prompt
        if repo_data and repo_data.get('description'):
            desc = repo_data['description']
            if any(keyword in desc.lower() for keyword in ['built with', 'generated', 'created using', 'made with']):
                return desc
        
        return None
    
    def analyze_tech_stack(self, readme_content, repo_data):
        """Analyze tech stack from README and repository data."""
        tech_stack = []
        
        # Analyze README content
        if readme_content:
            content_lower = readme_content.lower()
            
            for tech, pattern in self.tech_stack_patterns.items():
                if re.search(pattern, content_lower):
                    tech_stack.append(tech)
        
        # Add primary language from GitHub
        if repo_data and repo_data.get('language'):
            primary_lang = repo_data['language'].lower()
            if primary_lang not in tech_stack:
                tech_stack.append(primary_lang)
        
        return list(set(tech_stack))  # Remove duplicates
    
    def categorize_application(self, name, description, readme_content):
        """Categorize application based on content."""
        content = f"{name} {description or ''} {readme_content or ''}".lower()
        
        categories = {
            'web_app': ['website', 'web app', 'webapp', 'dashboard', 'frontend'],
            'mobile_app': ['mobile', 'app', 'ios', 'android', 'react native'],
            'ai_tool': ['ai', 'machine learning', 'ml', 'gpt', 'llm', 'chatbot'],
            'productivity': ['todo', 'task', 'productivity', 'manager', 'planner'],
            'ecommerce': ['shop', 'store', 'ecommerce', 'cart', 'payment'],
            'social': ['social', 'chat', 'messaging', 'community', 'forum'],
            'game': ['game', 'gaming', 'puzzle', 'quiz'],
            'education': ['education', 'learning', 'course', 'tutorial'],
            'finance': ['finance', 'banking', 'money', 'budget', 'investment'],
            'health': ['health', 'medical', 'fitness', 'workout'],
            'utility': ['tool', 'utility', 'converter', 'calculator']
        }
        
        for category, keywords in categories.items():
            if any(keyword in content for keyword in keywords):
                return category
        
        return 'other'
    
    def enrich_application(self, app_id, app_name, app_url, app_description):
        """Enrich a single application with additional metadata."""
        logger.info(f"🔍 Enriching: {app_name}")
        
        # Extract GitHub info
        owner, repo = self.extract_github_info(app_url)
        if not owner or not repo:
            logger.warning(f"❌ Invalid GitHub URL: {app_url}")
            return False
        
        # Fetch GitHub data
        github_data = self.fetch_github_repository_data(owner, repo)
        if not github_data['success']:
            return False
        
        repo_data = github_data['repo_data']
        readme_content = github_data['readme_content']
        
        # Extract enhancements
        original_prompt = self.extract_prompt_from_content(readme_content, repo_data)
        tech_stack = self.analyze_tech_stack(readme_content, repo_data)
        category = self.categorize_application(app_name, app_description, readme_content)
        
        # Enhanced description
        enhanced_desc = app_description
        if readme_content and len(readme_content) > len(app_description or ''):
            # Extract first paragraph from README as enhanced description
            first_paragraph = readme_content.split('\n\n')[0].strip()
            if len(first_paragraph) > len(app_description or ''):
                enhanced_desc = first_paragraph[:500]  # Limit length
        
        # Update database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE applications SET
                original_prompt = ?,
                tech_stack = ?,
                category = ?,
                github_stars = ?,
                github_forks = ?,
                github_language = ?,
                enhanced_description = ?,
                last_enriched_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (
            original_prompt,
            json.dumps(tech_stack) if tech_stack else None,
            category,
            repo_data.get('stargazers_count', 0),
            repo_data.get('forks_count', 0),
            repo_data.get('language'),
            enhanced_desc,
            app_id
        ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"✅ Enriched {app_name}: prompt={'✓' if original_prompt else '✗'}, tech={len(tech_stack)}, category={category}")
        return True
    
    def run_enrichment_batch(self, batch_size=50):
        """Run enrichment for a batch of applications."""
        logger.info("🚀 Starting database enrichment...")
        
        # Setup schema
        self.setup_enhanced_schema()
        
        # Get apps to enrich
        apps_to_enrich = self.get_github_apps_to_enrich(batch_size)
        
        if not apps_to_enrich:
            logger.info("✅ No applications need enrichment")
            return
        
        enriched_count = 0
        failed_count = 0
        
        for app_id, name, url, description, last_enriched in apps_to_enrich:
            try:
                success = self.enrich_application(app_id, name, url, description)
                
                if success:
                    enriched_count += 1
                else:
                    failed_count += 1
                
                # Rate limiting for GitHub API
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"❌ Error enriching {name}: {e}")
                failed_count += 1
        
        logger.info(f"🎉 Enrichment completed!")
        logger.info(f"   ✅ Enriched: {enriched_count}")
        logger.info(f"   ❌ Failed: {failed_count}")
        logger.info(f"   📊 Total processed: {len(apps_to_enrich)}")
        
        return {
            'enriched': enriched_count,
            'failed': failed_count,
            'total_processed': len(apps_to_enrich)
        }
    
    def show_enrichment_stats(self):
        """Show statistics about enriched data."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Count enriched applications
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(original_prompt) as with_prompts,
                COUNT(tech_stack) as with_tech_stack,
                COUNT(category) as with_category
            FROM applications
            WHERE last_enriched_at IS NOT NULL
        """)
        
        stats = cursor.fetchone()
        
        # Category breakdown
        cursor.execute("""
            SELECT category, COUNT(*) 
            FROM applications 
            WHERE category IS NOT NULL 
            GROUP BY category 
            ORDER BY COUNT(*) DESC
        """)
        
        categories = cursor.fetchall()
        
        # Tech stack analysis
        cursor.execute("""
            SELECT tech_stack, COUNT(*) 
            FROM applications 
            WHERE tech_stack IS NOT NULL 
            GROUP BY tech_stack 
            ORDER BY COUNT(*) DESC
            LIMIT 10
        """)
        
        tech_stacks = cursor.fetchall()
        
        conn.close()
        
        logger.info("📊 ENRICHMENT STATISTICS:")
        logger.info(f"   Enriched applications: {stats[0]}")
        logger.info(f"   With original prompts: {stats[1]}")
        logger.info(f"   With tech stack: {stats[2]}")
        logger.info(f"   With categories: {stats[3]}")
        
        if categories:
            logger.info("\n📋 TOP CATEGORIES:")
            for category, count in categories[:5]:
                logger.info(f"   {category}: {count}")
        
        return {
            'total_enriched': stats[0],
            'with_prompts': stats[1],
            'with_tech_stack': stats[2],
            'with_categories': stats[3],
            'categories': categories,
            'tech_stacks': tech_stacks
        }

def main():
    """Main enrichment function."""
    import os
    
    # Check for GitHub token
    github_token = os.getenv('GITHUB_TOKEN')
    if not github_token:
        logger.warning("⚠️ No GITHUB_TOKEN environment variable found!")
        logger.warning("Set with: export GITHUB_TOKEN='your_token'")
        logger.info("Proceeding with limited rate limits...")
    
    enricher = DatabaseEnricher(github_token)
    
    # Run enrichment
    results = enricher.run_enrichment_batch(batch_size=20)  # Start small
    
    # Show stats
    enricher.show_enrichment_stats()
    
    logger.info("🎉 Database enrichment completed!")

if __name__ == "__main__":
    main()