#!/usr/bin/env python3
"""
GitHub Pull Request Scraper for Google Jules

This script fetches pull requests from Jules bot (google-labs-jules) 
to collect the estimated 15-20k vibe coded applications.
"""

import requests
import json
import time
import logging
from typing import List, Dict, Any
from datetime import datetime
import subprocess
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class JulesPRScraper:
    def __init__(self, github_token: str = None):
        """Initialize the Jules PR scraper."""
        self.github_token = github_token
        self.base_url = "https://api.github.com"
        
        self.headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'vibe-coded-apps-database-scraper'
        }
        
        if github_token:
            self.headers['Authorization'] = f'token {github_token}'
    
    def check_gh_cli(self) -> bool:
        """Check if GitHub CLI is available."""
        try:
            result = subprocess.run(['gh', '--version'], 
                                  capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False
    
    def fetch_jules_prs_api(self, per_page: int = 100, page: int = 1) -> Dict[str, Any]:
        """
        Fetch Jules pull requests using GitHub API directly.
        
        Args:
            per_page: Number of PRs per page
            page: Page number
            
        Returns:
            Response with PRs and pagination info
        """
        try:
            params = {
                'q': 'author:google-labs-jules[bot] type:pr',
                'sort': 'created',
                'order': 'desc',
                'per_page': per_page,
                'page': page
            }
            
            url = f"{self.base_url}/search/issues"
            response = requests.get(url, headers=self.headers, params=params)
            
            logger.info(f"Response status: {response.status_code}")
            
            if response.status_code == 403:
                logger.error("Rate limit exceeded. Consider using GitHub token.")
                return {'items': [], 'total_count': 0}
            elif response.status_code != 200:
                logger.error(f"Response text: {response.text}")
                
            response.raise_for_status()
            
            data = response.json()
            items = data.get('items', [])
            total_count = data.get('total_count', 0)
            
            logger.info(f"Fetched {len(items)} PRs from page {page} (total: {total_count})")
            
            return {
                'items': items,
                'total_count': total_count,
                'has_more': len(items) == per_page
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching PRs: {e}")
            return {'items': [], 'total_count': 0, 'has_more': False}
    
    def fetch_jules_prs_gh_cli(self) -> List[Dict[str, Any]]:
        """
        Fetch Jules pull requests using GitHub CLI (faster and no rate limits).
        
        Returns:
            List of all PRs
        """
        try:
            # Use gh cli search command
            command = [
                'gh', 'search', 'prs',
                '--author=google-labs-jules[bot]',
                '--limit=1000',  # gh cli limit
                '--json=url,title,body,createdAt,updatedAt,author,repository,state'
            ]
            
            logger.info("Fetching PRs using GitHub CLI...")
            result = subprocess.run(command, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"GitHub CLI error: {result.stderr}")
                return []
            
            prs = json.loads(result.stdout)
            logger.info(f"Fetched {len(prs)} PRs using GitHub CLI")
            
            return prs
            
        except Exception as e:
            logger.error(f"Error using GitHub CLI: {e}")
            return []
    
    def fetch_all_prs_api(self) -> List[Dict[str, Any]]:
        """
        Fetch all Jules PRs using GitHub API with pagination.
        
        Returns:
            Complete list of all PRs
        """
        all_prs = []
        page = 1
        per_page = 100
        
        while True:
            response = self.fetch_jules_prs_api(per_page=per_page, page=page)
            
            items = response['items']
            if not items:
                break
                
            all_prs.extend(items)
            
            logger.info(f"Total PRs collected so far: {len(all_prs)}")
            
            # Check if there are more pages
            if not response.get('has_more', False):
                break
                
            page += 1
            
            # Rate limiting for API
            time.sleep(1)
            
            # API has a 1000 result limit for search
            if len(all_prs) >= 1000:
                logger.warning("Reached GitHub API search limit of 1000 results")
                break
            
        logger.info(f"Total PRs fetched via API: {len(all_prs)}")
        return all_prs
    
    def fetch_all_prs(self) -> List[Dict[str, Any]]:
        """
        Fetch all Jules PRs using the best available method.
        
        Returns:
            Complete list of all PRs
        """
        # Try GitHub CLI first (no rate limits, can get more results)
        if self.check_gh_cli():
            logger.info("Using GitHub CLI for fetching PRs...")
            prs = self.fetch_jules_prs_gh_cli()
            if prs:
                return prs
        
        # Fallback to API
        logger.info("Using GitHub API for fetching PRs...")
        return self.fetch_all_prs_api()
    
    def process_pr(self, pr: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single PR to extract relevant information.
        
        Args:
            pr: Raw PR data from API
            
        Returns:
            Processed PR data
        """
        # Handle different formats (API vs CLI)
        if 'repository' in pr and isinstance(pr['repository'], dict):
            # GitHub CLI format
            repo_name = pr['repository'].get('name', '')
            repo_owner = pr['repository'].get('owner', {}).get('login', '')
            repo_full_name = f"{repo_owner}/{repo_name}" if repo_owner and repo_name else ''
        else:
            # API format
            repo_url = pr.get('repository_url', pr.get('html_url', ''))
            repo_full_name = repo_url.replace('https://api.github.com/repos/', '').replace('https://github.com/', '')
            if '/pull/' in repo_full_name:
                repo_full_name = repo_full_name.split('/pull/')[0]
        
        return {
            'id': pr.get('id'),
            'number': pr.get('number'),
            'title': pr.get('title', ''),
            'body': pr.get('body', ''),
            'state': pr.get('state', ''),
            'created_at': pr.get('created_at', pr.get('createdAt')),
            'updated_at': pr.get('updated_at', pr.get('updatedAt')),
            'closed_at': pr.get('closed_at'),
            'merged_at': pr.get('merged_at'),
            'html_url': pr.get('html_url', pr.get('url', '')),
            'repository_full_name': repo_full_name,
            'author': pr.get('user', {}).get('login') if 'user' in pr else pr.get('author', {}).get('login', 'google-labs-jules'),
            'source': 'github_jules_prs',
            'platform': 'GitHub',
            'ai_tool': 'Gemini',  # Jules uses Gemini
        }
    
    def save_data(self, prs: List[Dict[str, Any]], filename: str = None) -> str:
        """
        Save PRs data to JSON file.
        
        Args:
            prs: List of processed PRs
            filename: Output filename (optional)
            
        Returns:
            Path to saved file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"jules_github_prs_{timestamp}.json"
        
        data = {
            'scrape_timestamp': datetime.now().isoformat(),
            'total_prs': len(prs),
            'source': 'github_jules_pull_requests',
            'prs': prs
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved {len(prs)} PRs to {filename}")
        return filename


def main():
    """Main function to run the Jules PR scraper."""
    # Try to get GitHub token from environment or gh cli
    github_token = None
    
    scraper = JulesPRScraper(github_token=github_token)
    
    logger.info("Starting Jules GitHub PR scraping...")
    
    # Fetch all PRs
    raw_prs = scraper.fetch_all_prs()
    
    if not raw_prs:
        logger.error("No PRs fetched. Check GitHub connection or authentication.")
        return
    
    # Process PRs
    processed_prs = [scraper.process_pr(pr) for pr in raw_prs]
    
    # Save data
    output_file = scraper.save_data(processed_prs)
    
    logger.info(f"Scraping completed. {len(processed_prs)} PRs saved to {output_file}")
    
    # Print summary
    print(f"\n=== Jules GitHub PRs Scraping Summary ===")
    print(f"Total PRs: {len(processed_prs)}")
    print(f"Output file: {output_file}")
    
    # Analyze repositories
    if processed_prs:
        repos = {}
        for pr in processed_prs:
            repo = pr['repository_full_name']
            repos[repo] = repos.get(repo, 0) + 1
        
        print(f"\nTop repositories:")
        for repo, count in sorted(repos.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {repo}: {count} PRs")
        
        print("\nSample PR:")
        sample = processed_prs[0]
        for key, value in sample.items():
            if len(str(value)) > 100:
                value = str(value)[:100] + "..."
            print(f"  {key}: {value}")


if __name__ == "__main__":
    main()