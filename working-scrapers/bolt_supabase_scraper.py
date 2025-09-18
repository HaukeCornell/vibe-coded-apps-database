#!/usr/bin/env python3
"""
Bolt Supabase Gallery Scraper

This script fetches all projects from Bolt's Supabase gallery_projects endpoint
using the API credentials and headers from commands.md.
"""

import requests
import json
import time
import logging
from typing import List, Dict, Any
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BoltSupabaseScraper:
    def __init__(self):
        """Initialize the Bolt Supabase scraper with API credentials."""
        self.base_url = "https://ksyayehmkytbjiphildq.supabase.co/rest/v1/gallery_projects"
        self.api_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtzeWF5ZWhta3l0YmppcGhpbGRxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDgyNTIyNDMsImV4cCI6MjA2MzgyODI0M30.n4zBbct5kPTvpfS_TwsYUaSZRTdA2JWRf27dPNL4TtQ"
        
        self.headers = {
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.9',
            'accept-profile': 'public',
            'apikey': self.api_key,
            'authorization': f'Bearer {self.api_key}',
            'dnt': '1',
            'origin': 'https://bolt.new',
            'priority': 'u=1, i',
            'referer': 'https://bolt.new/',
            'sec-ch-ua': '"Not=A?Brand";v="24", "Chromium";v="140"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'cross-site',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
            'x-client-info': 'supabase-js-web/2.53.0'
        }
    
    def explore_schema(self) -> Dict[str, Any]:
        """
        Explore the gallery_projects table schema by making a simple request.
        
        Returns:
            Sample response data
        """
        try:
            params = {
                'limit': 1
            }
            
            response = requests.get(self.base_url, headers=self.headers, params=params)
            response.raise_for_status()
            
            projects = response.json()
            if projects:
                logger.info(f"Sample project structure: {projects[0]}")
                return projects[0]
            else:
                logger.info("No projects returned")
                return {}
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error exploring schema: {e}")
            return {}
    
    def fetch_gallery_projects(self, limit: int = 1000, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Fetch gallery projects from Bolt's Supabase API.
        
        Args:
            limit: Number of projects to fetch per request
            offset: Offset for pagination
            
        Returns:
            List of project dictionaries
        """
        try:
            params = {
                'limit': limit,
                'offset': offset
                # Removed order parameter since we don't know valid column names yet
            }
            
            response = requests.get(self.base_url, headers=self.headers, params=params)
            
            # Log response details for debugging
            logger.info(f"Response status: {response.status_code}")
            
            if response.status_code != 200:
                logger.error(f"Response text: {response.text}")
                
            response.raise_for_status()
            
            projects = response.json()
            logger.info(f"Fetched {len(projects)} projects from offset {offset}")
            
            return projects
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching projects: {e}")
            return []
    
    def fetch_all_projects(self) -> List[Dict[str, Any]]:
        """
        Fetch all gallery projects with pagination.
        
        Returns:
            Complete list of all projects
        """
        all_projects = []
        offset = 0
        limit = 1000
        
        while True:
            batch = self.fetch_gallery_projects(limit=limit, offset=offset)
            
            if not batch:
                break
                
            all_projects.extend(batch)
            
            # If we got fewer results than requested, we've reached the end
            if len(batch) < limit:
                break
                
            offset += limit
            
            # Rate limiting - be respectful to the API
            time.sleep(1)
            
        logger.info(f"Total projects fetched: {len(all_projects)}")
        return all_projects
    
    def process_project(self, project: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single project to extract relevant information.
        
        Args:
            project: Raw project data from API
            
        Returns:
            Processed project data
        """
        return {
            'id': project.get('id'),
            'title': project.get('title', ''),
            'description': project.get('description', ''),
            'start_date': project.get('start_date'),  # Using actual field name
            'author': project.get('author', ''),
            'author_email': project.get('author_email', ''),
            'author_social': project.get('author_social', ''),
            'slug': project.get('slug', ''),
            'published': project.get('published', False),
            'status': project.get('status', ''),
            'project_url': project.get('project_url', ''),
            'project_preview': project.get('project_preview', ''),
            'thumbnail_image': project.get('thumbnail_image', ''),
            'category_slugs': project.get('category_slugs', []),
            'categories': project.get('categories', []),
            'source': 'bolt_gallery',
            'platform': 'Bolt',
            'ai_tool': 'Claude',  # Bolt typically uses Claude
        }
    
    def save_data(self, projects: List[Dict[str, Any]], filename: str = None) -> str:
        """
        Save projects data to JSON file.
        
        Args:
            projects: List of processed projects
            filename: Output filename (optional)
            
        Returns:
            Path to saved file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"bolt_gallery_projects_{timestamp}.json"
        
        data = {
            'scrape_timestamp': datetime.now().isoformat(),
            'total_projects': len(projects),
            'source': 'bolt_supabase_gallery',
            'projects': projects
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved {len(projects)} projects to {filename}")
        return filename


def main():
    """Main function to run the Bolt gallery scraper."""
    scraper = BoltSupabaseScraper()
    
    logger.info("Starting Bolt Supabase gallery scraping...")
    
    # First explore the schema
    logger.info("Exploring API schema...")
    sample = scraper.explore_schema()
    
    if not sample:
        logger.error("Could not explore schema. Check API credentials or connection.")
        return
    
    # Fetch all projects
    raw_projects = scraper.fetch_all_projects()
    
    if not raw_projects:
        logger.error("No projects fetched. Check API credentials or connection.")
        return
    
    # Process projects
    processed_projects = [scraper.process_project(project) for project in raw_projects]
    
    # Save data
    output_file = scraper.save_data(processed_projects)
    
    logger.info(f"Scraping completed. {len(processed_projects)} projects saved to {output_file}")
    
    # Print summary
    print(f"\n=== Bolt Gallery Scraping Summary ===")
    print(f"Total projects: {len(processed_projects)}")
    print(f"Output file: {output_file}")
    
    # Show sample of data
    if processed_projects:
        print("\nSample project:")
        sample = processed_projects[0]
        for key, value in sample.items():
            print(f"  {key}: {value}")


if __name__ == "__main__":
    main()