#!/usr/bin/env python3
"""
Subframe Platform Scraper

Scrapes projects from Subframe platform (app.subframe.com).
Based on API exploration showing working app.subframe.com/api endpoint.
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

class SubframeScraper:
    def __init__(self):
        """Initialize Subframe scraper."""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://app.subframe.com/'
        })
        
        self.base_url = 'https://app.subframe.com'
        self.scraped_projects = []
    
    def scrape_public_projects(self):
        """Scrape public projects from Subframe."""
        logger.info("🔍 Scraping Subframe public projects...")
        
        # Based on exploration, try different API endpoints
        api_endpoints = [
            '/api/projects',
            '/api/projects/public',
            '/api/public/projects',
            '/api/gallery',
            '/api/showcase'
        ]
        
        for endpoint in api_endpoints:
            try:
                url = f"{self.base_url}{endpoint}"
                logger.info(f"📡 Trying API endpoint: {url}")
                
                # Try with different parameters
                params = {
                    'limit': 100,
                    'page': 1,
                    'visibility': 'public'
                }
                
                response = self.session.get(url, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"✅ API success! Response size: {len(response.text)} chars")
                    
                    projects = self._parse_subframe_response(data, 'api')
                    if projects:
                        self.scraped_projects.extend(projects)
                        logger.info(f"📊 Found {len(projects)} projects from {endpoint}")
                        
                        # Try to get more pages
                        more_projects = self._scrape_paginated_projects(url, params)
                        self.scraped_projects.extend(more_projects)
                        break
                
                else:
                    logger.warning(f"❌ Failed API {endpoint}: {response.status_code}")
                    
            except Exception as e:
                logger.error(f"❌ Error with API {endpoint}: {e}")
                continue
                
            time.sleep(1)
        
        return self.scraped_projects
    
    def scrape_templates(self):
        """Scrape Subframe templates."""
        logger.info("🔍 Scraping Subframe templates...")
        
        template_endpoints = [
            '/api/templates',
            '/api/templates/public',
            '/api/public/templates'
        ]
        
        templates = []
        
        for endpoint in template_endpoints:
            try:
                url = f"{self.base_url}{endpoint}"
                
                params = {
                    'limit': 100,
                    'category': 'all'
                }
                
                response = self.session.get(url, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"✅ Templates from {endpoint}: {len(response.text)} chars")
                    
                    endpoint_templates = self._parse_subframe_response(data, 'templates')
                    # Mark templates as featured
                    for template in endpoint_templates:
                        template['is_featured'] = True
                        template['discovery_method'] = 'templates_api'
                    
                    templates.extend(endpoint_templates)
                    
                else:
                    logger.warning(f"❌ Failed templates {endpoint}: {response.status_code}")
                    
            except Exception as e:
                logger.error(f"❌ Error with templates {endpoint}: {e}")
                
            time.sleep(1)
        
        return templates
    
    def scrape_community(self):
        """Scrape Subframe community projects."""
        logger.info("🔍 Scraping Subframe community...")
        
        community_endpoints = [
            '/api/community',
            '/api/community/projects',
            '/api/projects/community'
        ]
        
        community_projects = []
        
        for endpoint in community_endpoints:
            try:
                url = f"{self.base_url}{endpoint}"
                
                response = self.session.get(url)
                
                if response.status_code == 200:
                    data = response.json()
                    projects = self._parse_subframe_response(data, 'community')
                    community_projects.extend(projects)
                    logger.info(f"👥 Found {len(projects)} community projects from {endpoint}")
                    
            except Exception as e:
                logger.error(f"Error with community endpoint {endpoint}: {e}")
                
            time.sleep(1)
        
        return community_projects
    
    def _scrape_paginated_projects(self, base_url, base_params):
        """Scrape additional pages if pagination is available."""
        projects = []
        page = 2
        max_pages = 10  # Reasonable limit
        
        try:
            while page <= max_pages:
                params = base_params.copy()
                params['page'] = page
                
                response = self.session.get(base_url, params=params)
                
                if response.status_code != 200:
                    break
                
                data = response.json()
                page_projects = self._parse_subframe_response(data, 'api')
                
                if not page_projects:
                    break
                
                projects.extend(page_projects)
                logger.info(f"📖 Page {page}: {len(page_projects)} more projects")
                
                page += 1
                time.sleep(1)
        
        except Exception as e:
            logger.error(f"Error with pagination: {e}")
        
        return projects
    
    def _parse_subframe_response(self, data, source_type):
        """Parse Subframe API response to extract projects."""
        projects = []
        
        try:
            # Handle different response structures
            if isinstance(data, dict):
                if 'projects' in data:
                    items = data['projects']
                elif 'templates' in data:
                    items = data['templates']
                elif 'items' in data:
                    items = data['items']
                elif 'data' in data:
                    items = data['data']
                elif 'results' in data:
                    items = data['results']
                else:
                    # Check if data itself contains project-like objects
                    items = [data] if self._looks_like_project(data) else []
            else:
                items = data if isinstance(data, list) else []
            
            for item in items:
                if not isinstance(item, dict):
                    continue
                
                project = {
                    'id': item.get('id') or item.get('projectId') or item.get('slug'),
                    'title': item.get('title') or item.get('name') or item.get('projectName'),
                    'description': item.get('description') or item.get('summary', ''),
                    'url': self._build_subframe_url(item),
                    'author': self._extract_author(item),
                    'created_at': item.get('createdAt') or item.get('created_at') or item.get('dateCreated'),
                    'updated_at': item.get('updatedAt') or item.get('updated_at') or item.get('dateModified'),
                    'tags': item.get('tags', []),
                    'category': item.get('category') or item.get('type'),
                    'framework': item.get('framework') or item.get('tech_stack'),
                    'is_public': item.get('isPublic', True),
                    'views': item.get('views', 0),
                    'likes': item.get('likes', 0),
                    'forks': item.get('forks', 0),
                    'platform': 'subframe',
                    'discovery_method': f'api_{source_type}',
                    'is_featured': source_type in ['templates', 'gallery'] or item.get('isFeatured', False)
                }
                
                if project['title']:  # Only add if has title
                    projects.append(project)
        
        except Exception as e:
            logger.error(f"Error parsing Subframe response: {e}")
        
        return projects
    
    def _looks_like_project(self, obj):
        """Check if an object looks like a project."""
        required_fields = ['title', 'name', 'projectName', 'projectTitle']
        return any(field in obj for field in required_fields)
    
    def _build_subframe_url(self, item):
        """Build Subframe project URL."""
        if 'url' in item:
            return item['url']
        
        if 'project_url' in item:
            return item['project_url']
        
        project_id = item.get('id') or item.get('slug')
        if project_id:
            return f"https://app.subframe.com/project/{project_id}"
        
        return "https://app.subframe.com/"
    
    def _extract_author(self, item):
        """Extract author from various possible fields."""
        # Check different author field variations
        author_fields = ['author', 'creator', 'user', 'owner', 'createdBy', 'userId']
        
        for field in author_fields:
            if field in item:
                author_data = item[field]
                if isinstance(author_data, dict):
                    return (author_data.get('name') or 
                           author_data.get('username') or 
                           author_data.get('displayName') or
                           author_data.get('email', '').split('@')[0])
                elif isinstance(author_data, str):
                    return author_data
        
        return 'Unknown'
    
    def run_scraper(self):
        """Run complete Subframe scraping."""
        logger.info("🚀 Starting Subframe scraper...")
        
        # Scrape public projects
        public_projects = self.scrape_public_projects()
        
        # Scrape templates
        templates = self.scrape_templates()
        
        # Scrape community projects
        community_projects = self.scrape_community()
        
        # Combine all results
        all_projects = public_projects + templates + community_projects
        
        # Remove duplicates by ID
        unique_projects = {}
        for project in all_projects:
            project_id = project.get('id')
            if project_id and project_id not in unique_projects:
                unique_projects[project_id] = project
            elif not project_id:
                # For projects without ID, use title + author as key
                key = f"{project.get('title', '')}_{project.get('author', '')}"
                if key not in unique_projects:
                    unique_projects[key] = project
        
        final_projects = list(unique_projects.values())
        
        logger.info(f"📊 Total unique Subframe projects: {len(final_projects)}")
        logger.info(f"📊 Public projects: {len(public_projects)}")
        logger.info(f"📊 Templates: {len(templates)}")
        logger.info(f"📊 Community projects: {len(community_projects)}")
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"subframe_projects_{timestamp}.json"
        
        output_data = {
            'timestamp': datetime.now().isoformat(),
            'total_projects': len(final_projects),
            'public_projects_count': len(public_projects),
            'templates_count': len(templates),
            'community_projects_count': len(community_projects),
            'projects': final_projects
        }
        
        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        logger.info(f"💾 Results saved to {output_file}")
        
        # Show sample projects
        if final_projects:
            logger.info("🔥 Sample Subframe projects:")
            for i, project in enumerate(final_projects[:3], 1):
                logger.info(f"  {i}. {project['title']} by {project['author']}")
                logger.info(f"     Framework: {project['framework']}, Featured: {project['is_featured']}")
        
        return final_projects

def main():
    """Main scraping function."""
    scraper = SubframeScraper()
    projects = scraper.run_scraper()
    
    logger.info(f"🎉 Subframe scraping completed! Found {len(projects)} projects")

if __name__ == "__main__":
    main()