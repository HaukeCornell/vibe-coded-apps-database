#!/usr/bin/env python3
"""
Stitch Platform Scraper

Scrapes projects from Google's Stitch platform (stitch.withgoogle.com).
Based on API exploration showing gallery and projects endpoints.
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

class StitchScraper:
    def __init__(self):
        """Initialize Stitch scraper."""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://stitch.withgoogle.com/'
        })
        
        self.base_url = 'https://stitch.withgoogle.com'
        self.scraped_projects = []
    
    def scrape_gallery(self):
        """Scrape projects from Stitch gallery."""
        logger.info("🔍 Scraping Stitch gallery...")
        
        # Based on exploration, try different gallery endpoints
        gallery_endpoints = [
            '/api/gallery',
            '/api/gallery/projects',
            '/api/projects/gallery',
            '/gallery/api/projects'
        ]
        
        for endpoint in gallery_endpoints:
            try:
                url = f"{self.base_url}{endpoint}"
                logger.info(f"📡 Trying gallery endpoint: {url}")
                
                response = self.session.get(url)
                
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"✅ Gallery success! Response size: {len(response.text)} chars")
                    
                    projects = self._parse_stitch_response(data, 'gallery')
                    if projects:
                        self.scraped_projects.extend(projects)
                        logger.info(f"📊 Found {len(projects)} gallery projects")
                        break
                
                else:
                    logger.warning(f"❌ Failed gallery {endpoint}: {response.status_code}")
                    
            except Exception as e:
                logger.error(f"❌ Error with gallery {endpoint}: {e}")
                continue
                
            time.sleep(1)
        
        return self.scraped_projects
    
    def scrape_projects(self):
        """Scrape general projects from Stitch."""
        logger.info("🔍 Scraping Stitch projects...")
        
        project_endpoints = [
            '/api/projects',
            '/api/projects/public',
            '/api/projects/featured',
            '/projects/api',
            '/api/v1/projects'
        ]
        
        projects = []
        
        for endpoint in project_endpoints:
            try:
                url = f"{self.base_url}{endpoint}"
                
                # Try with pagination parameters
                params = {
                    'page': 1,
                    'limit': 100,
                    'sort': 'recent'
                }
                
                response = self.session.get(url, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"✅ Projects from {endpoint}: {len(response.text)} chars")
                    
                    endpoint_projects = self._parse_stitch_response(data, 'projects')
                    projects.extend(endpoint_projects)
                    
                    # Try to get more pages if available
                    if 'pagination' in data or 'next' in data:
                        projects.extend(self._scrape_paginated_projects(url, data))
                
                else:
                    logger.warning(f"❌ Failed projects {endpoint}: {response.status_code}")
                    
            except Exception as e:
                logger.error(f"❌ Error with projects {endpoint}: {e}")
                
            time.sleep(1)
        
        return projects
    
    def _scrape_paginated_projects(self, base_url, initial_data):
        """Scrape additional pages if pagination is available."""
        projects = []
        page = 2
        max_pages = 5  # Limit to prevent infinite loops
        
        try:
            while page <= max_pages:
                params = {'page': page, 'limit': 100}
                response = self.session.get(base_url, params=params)
                
                if response.status_code != 200:
                    break
                
                data = response.json()
                page_projects = self._parse_stitch_response(data, 'projects')
                
                if not page_projects:
                    break
                
                projects.extend(page_projects)
                logger.info(f"📖 Page {page}: {len(page_projects)} more projects")
                
                page += 1
                time.sleep(1)
        
        except Exception as e:
            logger.error(f"Error with pagination: {e}")
        
        return projects
    
    def _parse_stitch_response(self, data, source_type):
        """Parse Stitch API response to extract projects."""
        projects = []
        
        try:
            # Handle different response structures
            if isinstance(data, dict):
                if 'projects' in data:
                    items = data['projects']
                elif 'items' in data:
                    items = data['items']
                elif 'data' in data:
                    items = data['data']
                elif 'gallery' in data:
                    items = data['gallery']
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
                    'url': self._build_stitch_url(item),
                    'author': self._extract_author(item),
                    'created_at': item.get('createdAt') or item.get('created_at') or item.get('dateCreated'),
                    'updated_at': item.get('updatedAt') or item.get('updated_at') or item.get('dateModified'),
                    'tags': item.get('tags', []),
                    'category': item.get('category') or item.get('type'),
                    'is_public': item.get('isPublic', True),
                    'views': item.get('views', 0),
                    'likes': item.get('likes', 0),
                    'platform': 'stitch',
                    'discovery_method': f'api_{source_type}',
                    'is_featured': source_type == 'gallery' or 'featured' in str(item.get('category', '')).lower()
                }
                
                if project['title']:  # Only add if has title
                    projects.append(project)
        
        except Exception as e:
            logger.error(f"Error parsing Stitch response: {e}")
        
        return projects
    
    def _looks_like_project(self, obj):
        """Check if an object looks like a project."""
        required_fields = ['title', 'name', 'projectName']
        return any(field in obj for field in required_fields)
    
    def _build_stitch_url(self, item):
        """Build Stitch project URL."""
        if 'url' in item:
            return item['url']
        
        project_id = item.get('id') or item.get('slug')
        if project_id:
            return f"https://stitch.withgoogle.com/project/{project_id}"
        
        return "https://stitch.withgoogle.com/"
    
    def _extract_author(self, item):
        """Extract author from various possible fields."""
        # Check different author field variations
        author_fields = ['author', 'creator', 'user', 'owner', 'createdBy']
        
        for field in author_fields:
            if field in item:
                author_data = item[field]
                if isinstance(author_data, dict):
                    return author_data.get('name') or author_data.get('username') or author_data.get('displayName')
                elif isinstance(author_data, str):
                    return author_data
        
        return 'Unknown'
    
    def scrape_featured_projects(self):
        """Scrape featured projects specifically."""
        logger.info("🔍 Scraping Stitch featured projects...")
        
        featured_endpoints = [
            '/api/featured',
            '/api/projects/featured', 
            '/api/gallery/featured',
            '/featured/api/projects'
        ]
        
        featured_projects = []
        
        for endpoint in featured_endpoints:
            try:
                url = f"{self.base_url}{endpoint}"
                response = self.session.get(url)
                
                if response.status_code == 200:
                    data = response.json()
                    projects = self._parse_stitch_response(data, 'featured')
                    
                    # Mark all as featured
                    for project in projects:
                        project['is_featured'] = True
                    
                    featured_projects.extend(projects)
                    logger.info(f"✨ Found {len(projects)} featured projects from {endpoint}")
                    
            except Exception as e:
                logger.error(f"Error with featured endpoint {endpoint}: {e}")
                
            time.sleep(1)
        
        return featured_projects
    
    def run_scraper(self):
        """Run complete Stitch scraping."""
        logger.info("🚀 Starting Stitch scraper...")
        
        # Scrape gallery projects
        gallery_projects = self.scrape_gallery()
        
        # Scrape general projects
        general_projects = self.scrape_projects()
        
        # Scrape featured projects
        featured_projects = self.scrape_featured_projects()
        
        # Combine all results
        all_projects = gallery_projects + general_projects + featured_projects
        
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
        
        logger.info(f"📊 Total unique Stitch projects: {len(final_projects)}")
        logger.info(f"📊 Gallery projects: {len(gallery_projects)}")
        logger.info(f"📊 General projects: {len(general_projects)}")
        logger.info(f"📊 Featured projects: {len(featured_projects)}")
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"stitch_projects_{timestamp}.json"
        
        output_data = {
            'timestamp': datetime.now().isoformat(),
            'total_projects': len(final_projects),
            'gallery_projects_count': len(gallery_projects),
            'general_projects_count': len(general_projects),
            'featured_projects_count': len(featured_projects),
            'projects': final_projects
        }
        
        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        logger.info(f"💾 Results saved to {output_file}")
        
        # Show sample projects
        if final_projects:
            logger.info("🔥 Sample Stitch projects:")
            for i, project in enumerate(final_projects[:3], 1):
                logger.info(f"  {i}. {project['title']} by {project['author']}")
                logger.info(f"     Category: {project['category']}, Featured: {project['is_featured']}")
        
        return final_projects

def main():
    """Main scraping function."""
    scraper = StitchScraper()
    projects = scraper.run_scraper()
    
    logger.info(f"🎉 Stitch scraping completed! Found {len(projects)} projects")

if __name__ == "__main__":
    main()