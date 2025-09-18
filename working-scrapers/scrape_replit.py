#!/usr/bin/env python3
"""
Replit Community Projects Scraper

Scrapes projects from Replit's community and templates sections.
Based on API exploration showing large datasets available.
"""

import requests
import json
import time
import logging
from datetime import datetime
import sys
import os

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ReplitScraper:
    def __init__(self):
        """Initialize Replit scraper."""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://replit.com/'
        })
        
        self.base_url = 'https://replit.com'
        self.scraped_projects = []
    
    def scrape_community_projects(self, limit=500):
        """Scrape community projects from Replit."""
        logger.info("🔍 Scraping Replit community projects...")
        
        # Try different community endpoints
        endpoints = [
            '/api/community/projects',
            '/api/community/featured',
            '/api/projects/community',
            '/api/graphql'  # GraphQL endpoint for more structured data
        ]
        
        for endpoint in endpoints:
            try:
                url = f"{self.base_url}{endpoint}"
                logger.info(f"📡 Trying endpoint: {url}")
                
                if endpoint == '/api/graphql':
                    # GraphQL query for community projects
                    query = {
                        "query": """
                        query CommunityProjects($limit: Int!) {
                            communityProjects(limit: $limit) {
                                id
                                title
                                description
                                url
                                user {
                                    username
                                }
                                language
                                isPublic
                                createdAt
                                updatedAt
                                stars
                                forks
                            }
                        }
                        """,
                        "variables": {"limit": limit}
                    }
                    
                    response = self.session.post(url, json=query)
                else:
                    # REST API call
                    params = {'limit': limit, 'page': 1}
                    response = self.session.get(url, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"✅ Success! Response size: {len(response.text)} chars")
                    
                    # Parse response based on structure
                    projects = self._parse_replit_response(data, endpoint)
                    if projects:
                        self.scraped_projects.extend(projects)
                        logger.info(f"📊 Found {len(projects)} projects from {endpoint}")
                        break  # Use first successful endpoint
                
                else:
                    logger.warning(f"❌ Failed {endpoint}: {response.status_code}")
                    
            except Exception as e:
                logger.error(f"❌ Error with {endpoint}: {e}")
                continue
                
            time.sleep(1)  # Rate limiting
        
        return self.scraped_projects
    
    def scrape_templates(self, limit=200):
        """Scrape Replit templates."""
        logger.info("🔍 Scraping Replit templates...")
        
        template_endpoints = [
            '/api/templates',
            '/api/templates/featured',
            '/api/templates/popular'
        ]
        
        templates = []
        
        for endpoint in template_endpoints:
            try:
                url = f"{self.base_url}{endpoint}"
                params = {'limit': limit}
                
                response = self.session.get(url, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"✅ Templates from {endpoint}: {len(response.text)} chars")
                    
                    # Parse templates
                    endpoint_templates = self._parse_templates_response(data, endpoint)
                    templates.extend(endpoint_templates)
                    
                else:
                    logger.warning(f"❌ Failed templates {endpoint}: {response.status_code}")
                    
            except Exception as e:
                logger.error(f"❌ Error with templates {endpoint}: {e}")
                
            time.sleep(1)
        
        return templates
    
    def _parse_replit_response(self, data, endpoint):
        """Parse Replit API response to extract projects."""
        projects = []
        
        try:
            # Handle different response structures
            if isinstance(data, dict):
                if 'data' in data and 'communityProjects' in data['data']:
                    # GraphQL response
                    items = data['data']['communityProjects']
                elif 'projects' in data:
                    items = data['projects']
                elif 'items' in data:
                    items = data['items']
                elif 'results' in data:
                    items = data['results']
                else:
                    # Direct list in data
                    items = data if isinstance(data, list) else []
            else:
                items = data if isinstance(data, list) else []
            
            for item in items:
                if not isinstance(item, dict):
                    continue
                
                project = {
                    'id': item.get('id') or item.get('slug'),
                    'title': item.get('title') or item.get('name'),
                    'description': item.get('description', ''),
                    'url': self._build_replit_url(item),
                    'author': self._extract_author(item),
                    'language': item.get('language') or item.get('lang'),
                    'created_at': item.get('createdAt') or item.get('created_at'),
                    'updated_at': item.get('updatedAt') or item.get('updated_at'),
                    'is_public': item.get('isPublic', True),
                    'stars': item.get('stars', 0),
                    'forks': item.get('forks', 0),
                    'platform': 'replit',
                    'discovery_method': f'api_{endpoint.split("/")[-1]}',
                    'is_featured': 'featured' in endpoint.lower()
                }
                
                if project['title']:  # Only add if has title
                    projects.append(project)
        
        except Exception as e:
            logger.error(f"Error parsing Replit response: {e}")
        
        return projects
    
    def _parse_templates_response(self, data, endpoint):
        """Parse Replit templates response."""
        templates = []
        
        try:
            items = data if isinstance(data, list) else data.get('templates', [])
            
            for item in items:
                template = {
                    'id': item.get('id'),
                    'title': item.get('title') or item.get('name'),
                    'description': item.get('description', ''),
                    'url': f"https://replit.com/@templates/{item.get('slug', '')}",
                    'author': 'Replit Templates',
                    'language': item.get('language'),
                    'created_at': item.get('createdAt'),
                    'updated_at': item.get('updatedAt'),
                    'is_public': True,
                    'stars': item.get('likes', 0),
                    'forks': item.get('forks', 0),
                    'platform': 'replit',
                    'discovery_method': 'templates_api',
                    'is_featured': True  # Templates are curated
                }
                
                if template['title']:
                    templates.append(template)
        
        except Exception as e:
            logger.error(f"Error parsing templates: {e}")
        
        return templates
    
    def _build_replit_url(self, item):
        """Build Replit project URL."""
        if 'url' in item:
            return item['url']
        
        username = self._extract_author(item)
        project_name = item.get('slug') or item.get('id') or item.get('title', '').replace(' ', '-')
        
        if username and project_name:
            return f"https://replit.com/@{username}/{project_name}"
        
        return f"https://replit.com/projects/{item.get('id', '')}"
    
    def _extract_author(self, item):
        """Extract author from various possible fields."""
        if 'user' in item and isinstance(item['user'], dict):
            return item['user'].get('username')
        
        return item.get('username') or item.get('author') or item.get('owner')
    
    def run_scraper(self):
        """Run complete Replit scraping."""
        logger.info("🚀 Starting Replit scraper...")
        
        # Scrape community projects
        community_projects = self.scrape_community_projects()
        
        # Scrape templates
        templates = self.scrape_templates()
        
        # Combine results
        all_projects = community_projects + templates
        
        # Remove duplicates by ID
        unique_projects = {}
        for project in all_projects:
            project_id = project.get('id')
            if project_id and project_id not in unique_projects:
                unique_projects[project_id] = project
        
        final_projects = list(unique_projects.values())
        
        logger.info(f"📊 Total unique Replit projects: {len(final_projects)}")
        logger.info(f"📊 Community projects: {len(community_projects)}")
        logger.info(f"📊 Templates: {len(templates)}")
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"replit_projects_{timestamp}.json"
        
        output_data = {
            'timestamp': datetime.now().isoformat(),
            'total_projects': len(final_projects),
            'community_projects_count': len(community_projects),
            'templates_count': len(templates),
            'projects': final_projects
        }
        
        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        logger.info(f"💾 Results saved to {output_file}")
        
        # Show sample projects
        if final_projects:
            logger.info("🔥 Sample Replit projects:")
            for i, project in enumerate(final_projects[:3], 1):
                logger.info(f"  {i}. {project['title']} by {project['author']}")
                logger.info(f"     Language: {project['language']}, URL: {project['url']}")
        
        return final_projects

def main():
    """Main scraping function."""
    scraper = ReplitScraper()
    projects = scraper.run_scraper()
    
    logger.info(f"🎉 Replit scraping completed! Found {len(projects)} projects")

if __name__ == "__main__":
    main()