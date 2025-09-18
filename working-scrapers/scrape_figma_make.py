#!/usr/bin/env python3
"""
Figma Make Community Scraper

Scrapes projects from Figma Make community platform.
Based on API exploration showing community endpoint with project data.
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

class FigmaMakeScraper:
    def __init__(self):
        """Initialize Figma Make scraper."""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.figma.com/'
        })
        
        self.base_url = 'https://www.figma.com'
        self.scraped_projects = []
    
    def scrape_community_projects(self):
        """Scrape projects from Figma Make community."""
        logger.info("🔍 Scraping Figma Make community projects...")
        
        # Based on exploration, the community endpoint had substantial data
        community_endpoints = [
            '/api/make/community',
            '/api/community/make',
            '/make/api/community',
            '/api/community/projects'
        ]
        
        for endpoint in community_endpoints:
            try:
                url = f"{self.base_url}{endpoint}"
                logger.info(f"📡 Trying community endpoint: {url}")
                
                response = self.session.get(url)
                
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"✅ Community success! Response size: {len(response.text)} chars")
                    
                    projects = self._parse_figma_response(data, 'community')
                    if projects:
                        self.scraped_projects.extend(projects)
                        logger.info(f"📊 Found {len(projects)} community projects")
                        break
                
                else:
                    logger.warning(f"❌ Failed community {endpoint}: {response.status_code}")
                    
            except Exception as e:
                logger.error(f"❌ Error with community {endpoint}: {e}")
                continue
                
            time.sleep(1)
        
        return self.scraped_projects
    
    def scrape_make_gallery(self):
        """Scrape Figma Make gallery/showcase."""
        logger.info("🔍 Scraping Figma Make gallery...")
        
        gallery_endpoints = [
            '/api/make/gallery',
            '/api/make/showcase', 
            '/make/api/gallery',
            '/api/gallery/make'
        ]
        
        gallery_projects = []
        
        for endpoint in gallery_endpoints:
            try:
                url = f"{self.base_url}{endpoint}"
                
                # Try with different parameters
                params = {
                    'limit': 100,
                    'sort': 'recent',
                    'category': 'all'
                }
                
                response = self.session.get(url, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"✅ Gallery from {endpoint}: {len(response.text)} chars")
                    
                    projects = self._parse_figma_response(data, 'gallery')
                    # Mark gallery projects as featured
                    for project in projects:
                        project['is_featured'] = True
                    
                    gallery_projects.extend(projects)
                    
                else:
                    logger.warning(f"❌ Failed gallery {endpoint}: {response.status_code}")
                    
            except Exception as e:
                logger.error(f"❌ Error with gallery {endpoint}: {e}")
                
            time.sleep(1)
        
        return gallery_projects
    
    def scrape_featured_makes(self):
        """Scrape featured Figma Make projects."""
        logger.info("🔍 Scraping featured Figma Make projects...")
        
        featured_endpoints = [
            '/api/make/featured',
            '/api/featured/make',
            '/make/api/featured'
        ]
        
        featured_projects = []
        
        for endpoint in featured_endpoints:
            try:
                url = f"{self.base_url}{endpoint}"
                response = self.session.get(url)
                
                if response.status_code == 200:
                    data = response.json()
                    projects = self._parse_figma_response(data, 'featured')
                    
                    # Mark all as featured
                    for project in projects:
                        project['is_featured'] = True
                    
                    featured_projects.extend(projects)
                    logger.info(f"✨ Found {len(projects)} featured projects from {endpoint}")
                    
            except Exception as e:
                logger.error(f"Error with featured endpoint {endpoint}: {e}")
                
            time.sleep(1)
        
        return featured_projects
    
    def _parse_figma_response(self, data, source_type):
        """Parse Figma Make API response to extract projects."""
        projects = []
        
        try:
            # Handle different response structures
            if isinstance(data, dict):
                if 'projects' in data:
                    items = data['projects']
                elif 'makes' in data:
                    items = data['makes']
                elif 'items' in data:
                    items = data['items']
                elif 'data' in data:
                    items = data['data']
                elif 'community' in data:
                    items = data['community']
                elif 'gallery' in data:
                    items = data['gallery']
                else:
                    # Check if data itself contains project-like objects
                    items = [data] if self._looks_like_figma_project(data) else []
            else:
                items = data if isinstance(data, list) else []
            
            for item in items:
                if not isinstance(item, dict):
                    continue
                
                project = {
                    'id': item.get('id') or item.get('make_id') or item.get('project_id'),
                    'title': item.get('title') or item.get('name') or item.get('make_name'),
                    'description': item.get('description') or item.get('summary', ''),
                    'url': self._build_figma_url(item),
                    'author': self._extract_author(item),
                    'created_at': item.get('created_at') or item.get('createdAt') or item.get('date_created'),
                    'updated_at': item.get('updated_at') or item.get('updatedAt') or item.get('date_modified'),
                    'tags': item.get('tags', []),
                    'category': item.get('category') or item.get('type'),
                    'thumbnail': item.get('thumbnail') or item.get('preview_url'),
                    'views': item.get('views', 0),
                    'likes': item.get('likes', 0),
                    'comments': item.get('comments', 0),
                    'platform': 'figma_make',
                    'discovery_method': f'api_{source_type}',
                    'is_featured': source_type in ['gallery', 'featured'] or item.get('is_featured', False)
                }
                
                if project['title']:  # Only add if has title
                    projects.append(project)
        
        except Exception as e:
            logger.error(f"Error parsing Figma Make response: {e}")
        
        return projects
    
    def _looks_like_figma_project(self, obj):
        """Check if an object looks like a Figma Make project."""
        required_fields = ['title', 'name', 'make_name', 'project_name']
        return any(field in obj for field in required_fields)
    
    def _build_figma_url(self, item):
        """Build Figma Make project URL."""
        if 'url' in item:
            return item['url']
        
        if 'figma_url' in item:
            return item['figma_url']
        
        project_id = item.get('id') or item.get('make_id')
        if project_id:
            return f"https://www.figma.com/make/{project_id}"
        
        return "https://www.figma.com/make/"
    
    def _extract_author(self, item):
        """Extract author from various possible fields."""
        # Check different author field variations
        author_fields = ['author', 'creator', 'user', 'owner', 'made_by', 'created_by']
        
        for field in author_fields:
            if field in item:
                author_data = item[field]
                if isinstance(author_data, dict):
                    return (author_data.get('name') or 
                           author_data.get('username') or 
                           author_data.get('display_name') or
                           author_data.get('handle'))
                elif isinstance(author_data, str):
                    return author_data
        
        return 'Unknown'
    
    def scrape_categories(self):
        """Scrape projects by categories."""
        logger.info("🔍 Scraping Figma Make by categories...")
        
        # Common categories for design/make platforms
        categories = [
            'web-design', 'mobile-design', 'ui-design', 'prototypes',
            'components', 'icons', 'illustrations', 'templates'
        ]
        
        category_projects = []
        
        for category in categories:
            try:
                url = f"{self.base_url}/api/make/category/{category}"
                params = {'limit': 50}
                
                response = self.session.get(url, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    projects = self._parse_figma_response(data, f'category_{category}')
                    
                    # Add category info
                    for project in projects:
                        project['category'] = category
                    
                    category_projects.extend(projects)
                    logger.info(f"📂 Category {category}: {len(projects)} projects")
                    
            except Exception as e:
                logger.error(f"Error with category {category}: {e}")
                
            time.sleep(1)
        
        return category_projects
    
    def run_scraper(self):
        """Run complete Figma Make scraping."""
        logger.info("🚀 Starting Figma Make scraper...")
        
        # Scrape community projects
        community_projects = self.scrape_community_projects()
        
        # Scrape gallery
        gallery_projects = self.scrape_make_gallery()
        
        # Scrape featured projects
        featured_projects = self.scrape_featured_makes()
        
        # Scrape by categories
        category_projects = self.scrape_categories()
        
        # Combine all results
        all_projects = community_projects + gallery_projects + featured_projects + category_projects
        
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
        
        logger.info(f"📊 Total unique Figma Make projects: {len(final_projects)}")
        logger.info(f"📊 Community projects: {len(community_projects)}")
        logger.info(f"📊 Gallery projects: {len(gallery_projects)}")
        logger.info(f"📊 Featured projects: {len(featured_projects)}")
        logger.info(f"📊 Category projects: {len(category_projects)}")
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"figma_make_projects_{timestamp}.json"
        
        output_data = {
            'timestamp': datetime.now().isoformat(),
            'total_projects': len(final_projects),
            'community_projects_count': len(community_projects),
            'gallery_projects_count': len(gallery_projects),
            'featured_projects_count': len(featured_projects),
            'category_projects_count': len(category_projects),
            'projects': final_projects
        }
        
        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        logger.info(f"💾 Results saved to {output_file}")
        
        # Show sample projects
        if final_projects:
            logger.info("🔥 Sample Figma Make projects:")
            for i, project in enumerate(final_projects[:3], 1):
                logger.info(f"  {i}. {project['title']} by {project['author']}")
                logger.info(f"     Category: {project['category']}, Featured: {project['is_featured']}")
        
        return final_projects

def main():
    """Main scraping function."""
    scraper = FigmaMakeScraper()
    projects = scraper.run_scraper()
    
    logger.info(f"🎉 Figma Make scraping completed! Found {len(projects)} projects")

if __name__ == "__main__":
    main()