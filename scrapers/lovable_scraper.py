#!/usr/bin/env python3
"""
Lovable Community API Scraper

This script fetches all projects from Lovable's community API
using the endpoint and headers from commands.md.
"""

import requests
import json
import time
import logging
from typing import List, Dict, Any
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LovableScraper:
    def __init__(self):
        """Initialize the Lovable community scraper."""
        self.base_url = "https://lovable-api.com/projects/community"
        
        self.headers = {
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.9',
            'content-type': 'application/json',
            'dnt': '1',
            'origin': 'https://lovable.dev',
            'priority': 'u=1, i',
            'referer': 'https://lovable.dev/',
            'sec-ch-ua': '"Not=A?Brand";v="24", "Chromium";v="140"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'cross-site',
            'sec-fetch-storage-access': 'active',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36'
        }
    
    def fetch_community_projects(self, limit: int = 100, order_by: str = "recent", cursor: str = None) -> Dict[str, Any]:
        """
        Fetch community projects from Lovable's API.
        
        Args:
            limit: Number of projects to fetch per request
            order_by: Order projects by (recent, popular, etc.)
            cursor: Cursor for pagination
            
        Returns:
            Response data with projects and pagination info
        """
        try:
            params = {
                'limit': limit,
                'order_by': order_by
            }
            
            if cursor:
                params['cursor'] = cursor
            
            response = requests.get(self.base_url, headers=self.headers, params=params)
            
            # Log response details for debugging
            logger.info(f"Response status: {response.status_code}")
            
            if response.status_code != 200:
                logger.error(f"Response text: {response.text}")
                
            response.raise_for_status()
            
            data = response.json()
            
            # Extract projects and pagination info
            projects = data.get('projects', [])
            has_more = data.get('hasMore', False)
            next_cursor = data.get('nextCursor')
            
            logger.info(f"Fetched {len(projects)} projects (hasMore: {has_more})")
            
            return {
                'projects': projects,
                'has_more': has_more,
                'next_cursor': next_cursor
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching projects: {e}")
            return {'projects': [], 'has_more': False, 'next_cursor': None}
    
    def fetch_all_projects(self) -> List[Dict[str, Any]]:
        """
        Fetch all community projects with cursor-based pagination.
        
        Returns:
            Complete list of all projects
        """
        all_projects = []
        cursor = None
        limit = 100
        
        while True:
            response = self.fetch_community_projects(limit=limit, cursor=cursor)
            
            projects = response['projects']
            if not projects:
                break
                
            all_projects.extend(projects)
            
            # Check if there are more pages
            if not response['has_more']:
                break
                
            cursor = response['next_cursor']
            if not cursor:
                break
            
            # Rate limiting - be respectful to the API
            time.sleep(2)
            
        logger.info(f"Total projects fetched: {len(all_projects)}")
        return all_projects
    
    def explore_api(self) -> Dict[str, Any]:
        """
        Explore the API by making a small request to understand the response format.
        
        Returns:
            Sample response data
        """
        try:
            params = {
                'limit': 1,
                'order_by': 'recent'
            }
            
            response = requests.get(self.base_url, headers=self.headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"Sample API response: {data}")
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error exploring API: {e}")
            return {}
    
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
            'workspace_id': project.get('workspace_id'),
            'title': project.get('name', project.get('title', '')),
            'description': project.get('description', ''),
            'created_at': project.get('created_at'),
            'updated_at': project.get('updated_at'),
            'created_by': project.get('created_by', ''),
            'user_id': project.get('user_id'),
            'user_display_name': project.get('user_display_name', ''),
            'user_photo_url': project.get('user_photo_url', ''),
            'url': project.get('url', ''),
            'latest_screenshot_url': project.get('latest_screenshot_url', ''),
            'status': project.get('status', ''),
            'is_published': project.get('is_published', False),
            'visibility': project.get('visibility', ''),
            'featured': project.get('featured', False),
            'featured_at': project.get('featured_at'),
            'feature_source': project.get('feature_source', ''),
            'feature_rank': project.get('feature_rank'),
            'edit_count': project.get('edit_count', 0),
            'user_message_count': project.get('user_message_count', 0),
            'remix_count': project.get('remix_count', 0),
            'source': 'lovable_community',
            'platform': 'Lovable',
            'ai_tool': 'GPT-4',  # Lovable typically uses GPT-4
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
            filename = f"lovable_community_projects_{timestamp}.json"
        
        data = {
            'scrape_timestamp': datetime.now().isoformat(),
            'total_projects': len(projects),
            'source': 'lovable_community_api',
            'projects': projects
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved {len(projects)} projects to {filename}")
        return filename


def main():
    """Main function to run the Lovable community scraper."""
    scraper = LovableScraper()
    
    logger.info("Starting Lovable community scraping...")
    
    # First explore the API
    logger.info("Exploring API structure...")
    sample = scraper.explore_api()
    
    if not sample:
        logger.error("Could not explore API. Check connection.")
        return
    
    # Fetch all projects
    raw_projects = scraper.fetch_all_projects()
    
    if not raw_projects:
        logger.error("No projects fetched. Check API connection.")
        return
    
    # Process projects
    processed_projects = [scraper.process_project(project) for project in raw_projects]
    
    # Save data
    output_file = scraper.save_data(processed_projects)
    
    logger.info(f"Scraping completed. {len(processed_projects)} projects saved to {output_file}")
    
    # Print summary
    print(f"\n=== Lovable Community Scraping Summary ===")
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