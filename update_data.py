#!/usr/bin/env python3
"""
Vibe Coded Apps Database - Update Automation
Continuous data collection from all vibe coding platforms
"""

import os
import json
import requests
import subprocess
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
from process_data import VibeCodedAppsDB, GitHubDataProcessor, V0DataProcessor

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PlatformScraper:
    def __init__(self, db: VibeCodedAppsDB):
        self.db = db
        self.data_dir = "scraped_data"
        os.makedirs(self.data_dir, exist_ok=True)
    
    def create_scraping_job(self, platform_name: str, job_type: str, query_params: Dict = None) -> int:
        """Create a new scraping job"""
        platform_id = self.db.get_platform_id(platform_name)
        if not platform_id:
            raise ValueError(f"Platform {platform_name} not found")
        
        cursor = self.db.conn.cursor()
        cursor.execute("""
            INSERT INTO scraping_jobs (platform_id, job_type, query_params, started_at)
            VALUES (?, ?, ?, ?)
        """, (platform_id, job_type, json.dumps(query_params or {}), datetime.now().isoformat()))
        
        job_id = cursor.lastrowid
        self.db.conn.commit()
        return job_id
    
    def update_job_status(self, job_id: int, status: str, items_found: int = None, 
                         items_processed: int = None, error_message: str = None):
        """Update scraping job status"""
        cursor = self.db.conn.cursor()
        
        updates = ["status = ?"]
        params = [status]
        
        if items_found is not None:
            updates.append("items_found = ?")
            params.append(items_found)
        
        if items_processed is not None:
            updates.append("items_processed = ?")
            params.append(items_processed)
        
        if error_message:
            updates.append("error_message = ?")
            params.append(error_message)
        
        if status == 'completed':
            updates.append("completed_at = ?")
            params.append(datetime.now().isoformat())
        
        params.append(job_id)
        
        cursor.execute(f"UPDATE scraping_jobs SET {', '.join(updates)} WHERE id = ?", params)
        self.db.conn.commit()

class GitHubScraper(PlatformScraper):
    def __init__(self, db: VibeCodedAppsDB, github_token: str = None):
        super().__init__(db)
        self.github_token = github_token or os.getenv('GITHUB_TOKEN')
        self.headers = {}
        if self.github_token:
            self.headers['Authorization'] = f'token {self.github_token}'
        
        # Rate limiting
        self.requests_per_hour = 5000 if self.github_token else 60
        self.last_request_time = 0
        self.request_count = 0
        self.hour_start = time.time()
    
    def _rate_limit(self):
        """Implement GitHub API rate limiting"""
        current_time = time.time()
        
        # Reset counter every hour
        if current_time - self.hour_start > 3600:
            self.request_count = 0
            self.hour_start = current_time
        
        # Check if we've hit the limit
        if self.request_count >= self.requests_per_hour:
            sleep_time = 3600 - (current_time - self.hour_start)
            if sleep_time > 0:
                logger.info(f"Rate limit reached, sleeping for {sleep_time:.0f} seconds")
                time.sleep(sleep_time)
                self.request_count = 0
                self.hour_start = time.time()
        
        # Ensure minimum time between requests
        time_since_last = current_time - self.last_request_time
        if time_since_last < 1:  # 1 second minimum between requests
            time.sleep(1 - time_since_last)
        
        self.last_request_time = time.time()
        self.request_count += 1
    
    def search_repositories(self, query: str, file_type: str, max_pages: int = 10) -> List[Dict]:
        """Search GitHub repositories"""
        all_items = []
        page = 1
        
        while page <= max_pages:
            self._rate_limit()
            
            url = "https://api.github.com/search/code"
            params = {
                'q': query,
                'sort': 'indexed',
                'order': 'desc',
                'per_page': 100,
                'page': page
            }
            
            try:
                response = requests.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                
                data = response.json()
                items = data.get('items', [])
                
                if not items:
                    break
                
                all_items.extend(items)
                logger.info(f"Page {page}: Retrieved {len(items)} items (total: {len(all_items)})")
                
                # Check if we have more pages
                if len(items) < 100:
                    break
                
                page += 1
                
            except requests.exceptions.RequestException as e:
                logger.error(f"GitHub API request failed: {e}")
                break
            except Exception as e:
                logger.error(f"Error processing GitHub response: {e}")
                break
        
        return all_items
    
    def update_github_data(self):
        """Update GitHub repository data"""
        searches = [
            ("filename:AGENTS.md", "agents_md"),
            ("filename:claude.md OR filename:CLAUDE.md", "claude_md"),
            ("filename:gemini.md OR filename:GEMINI.md", "gemini_md"),
            ("filename:README.md lovable", "lovable_md"),
            ("filename:README.md bolt.new", "bolt_md"),
            ("filename:README.md replit", "replit_md"),
            ("filename:README.md v0.dev", "v0_readme_md"),
        ]
        
        for query, file_type in searches:
            logger.info(f"Searching GitHub for: {query}")
            
            job_id = self.create_scraping_job("github.com", "github_search", {"query": query, "file_type": file_type})
            
            try:
                self.update_job_status(job_id, "running")
                
                items = self.search_repositories(query, file_type)
                
                if items:
                    # Save raw data
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"{self.data_dir}/github_{file_type}_{timestamp}.json"
                    
                    result_data = {
                        "total_count": len(items),
                        "incomplete_results": False,
                        "items": items
                    }
                    
                    with open(filename, 'w') as f:
                        json.dump(result_data, f, indent=2)
                    
                    # Process data
                    processor = GitHubDataProcessor(self.db)
                    processor.process_github_search_results(filename, file_type)
                    
                    self.update_job_status(job_id, "completed", len(items), len(items))
                    logger.info(f"Completed {file_type}: {len(items)} items processed")
                else:
                    self.update_job_status(job_id, "completed", 0, 0)
                    logger.info(f"No items found for {file_type}")
                
            except Exception as e:
                error_msg = str(e)
                self.update_job_status(job_id, "failed", error_message=error_msg)
                logger.error(f"Failed to process {file_type}: {error_msg}")

class V0Scraper(PlatformScraper):
    def update_v0_data(self):
        """Update v0.dev community data"""
        logger.info("Updating v0.dev community data")
        
        job_id = self.create_scraping_job("v0.dev", "community_scrape")
        
        try:
            self.update_job_status(job_id, "running")
            
            # Use curl command from commands.md to get v0 data
            # This would need to be implemented based on v0.dev's actual API
            # For now, we'll simulate with existing data
            
            existing_file = "First-Scrape/v0.json"
            if os.path.exists(existing_file):
                with open(existing_file, 'r') as f:
                    urls = json.load(f)
                
                # Save updated data
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{self.data_dir}/v0_community_{timestamp}.json"
                
                with open(filename, 'w') as f:
                    json.dump(urls, f, indent=2)
                
                # Process data
                processor = V0DataProcessor(self.db)
                processor.process_v0_urls(filename)
                
                self.update_job_status(job_id, "completed", len(urls), len(urls))
                logger.info(f"Completed v0.dev: {len(urls)} URLs processed")
            else:
                self.update_job_status(job_id, "completed", 0, 0)
                logger.info("No v0.dev data file found")
                
        except Exception as e:
            error_msg = str(e)
            self.update_job_status(job_id, "failed", error_message=error_msg)
            logger.error(f"Failed to process v0.dev data: {error_msg}")

class BoltScraper(PlatformScraper):
    def update_bolt_data(self):
        """Update bolt.new data using Supabase API"""
        logger.info("Updating bolt.new data")
        
        job_id = self.create_scraping_job("bolt.new", "api_fetch")
        
        try:
            self.update_job_status(job_id, "running")
            
            # Based on commands.md: curl for Bolt Supabase API
            # This would need actual API credentials and endpoints
            # For now, implement the structure
            
            apps = []
            # TODO: Implement actual Bolt API scraping
            # Example structure based on commands.md:
            # curl -X GET "https://supabase-api-url" -H "Authorization: Bearer token"
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{self.data_dir}/bolt_apps_{timestamp}.json"
            
            with open(filename, 'w') as f:
                json.dump(apps, f, indent=2)
            
            self.update_job_status(job_id, "completed", len(apps), len(apps))
            logger.info(f"Completed bolt.new: {len(apps)} apps processed")
            
        except Exception as e:
            error_msg = str(e)
            self.update_job_status(job_id, "failed", error_message=error_msg)
            logger.error(f"Failed to process bolt.new data: {error_msg}")

class LovableScraper(PlatformScraper):
    def update_lovable_data(self):
        """Update lovable.dev data"""
        logger.info("Updating lovable.dev data")
        
        job_id = self.create_scraping_job("lovable.dev", "api_fetch")
        
        try:
            self.update_job_status(job_id, "running")
            
            # Based on commands.md: Lovable API
            # This would need actual API implementation
            
            apps = []
            # TODO: Implement actual Lovable API scraping
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{self.data_dir}/lovable_apps_{timestamp}.json"
            
            with open(filename, 'w') as f:
                json.dump(apps, f, indent=2)
            
            self.update_job_status(job_id, "completed", len(apps), len(apps))
            logger.info(f"Completed lovable.dev: {len(apps)} apps processed")
            
        except Exception as e:
            error_msg = str(e)
            self.update_job_status(job_id, "failed", error_message=error_msg)
            logger.error(f"Failed to process lovable.dev data: {error_msg}")

def run_update_cycle():
    """Run a complete update cycle for all platforms"""
    logger.info("Starting update cycle")
    
    # Initialize database
    db = VibeCodedAppsDB()
    db.connect()
    
    try:
        # Initialize scrapers
        github_scraper = GitHubScraper(db)
        v0_scraper = V0Scraper(db)
        bolt_scraper = BoltScraper(db)
        lovable_scraper = LovableScraper(db)
        
        # Run scrapers
        github_scraper.update_github_data()
        v0_scraper.update_v0_data()
        bolt_scraper.update_bolt_data()
        lovable_scraper.update_lovable_data()
        
        logger.info("Update cycle completed successfully")
        
    except Exception as e:
        logger.error(f"Error in update cycle: {e}")
        raise
    finally:
        db.close()

def main():
    """Main function for update automation"""
    # Check for required environment variables
    github_token = os.getenv('GITHUB_TOKEN')
    if not github_token:
        logger.warning("GITHUB_TOKEN not set. Rate limiting will be more restrictive.")
    
    # Run update cycle
    run_update_cycle()

if __name__ == "__main__":
    main()