#!/usr/bin/env python3
"""
GitHub AGENTS.md Search Processor

This script searches for legitimate vibe-coded repositories that contain AGENTS.md files.
AGENTS.md files are a strong indicator of actual vibe-coded applications.

Focus: Only AGENTS.md files (6,712 repositories)
NOT: Generic Claude/Gemini mentions (not necessarily vibe-coded)
"""

import json
import logging
import requests
import time
from typing import List, Dict, Any, Optional
from datetime import datetime
import subprocess

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GitHubCodeSearchProcessor:
    def __init__(self, github_token: str = None):
        """Initialize the GitHub code search processor."""
        self.github_token = github_token
        self.base_url = "https://api.github.com"
        
        self.headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'vibe-coded-apps-database-scraper'
        }
        
        if github_token:
            self.headers['Authorization'] = f'token {github_token}'
    
    def search_code_files(self, query: str, per_page: int = 100, max_results: int = None) -> List[Dict[str, Any]]:
        """
        Search for code files using GitHub API with full pagination.
        
        Args:
            query: GitHub search query
            per_page: Results per page
            max_results: Maximum results to fetch (None for all)
            
        Returns:
            List of all matching files
        """
        all_files = []
        page = 1
        
        while True:
            try:
                params = {
                    'q': query,
                    'per_page': per_page,
                    'page': page
                }
                
                url = f"{self.base_url}/search/code"
                response = requests.get(url, headers=self.headers, params=params)
                
                logger.info(f"Search '{query}' - Page {page} - Status: {response.status_code}")
                
                if response.status_code == 403:
                    logger.warning("Rate limit hit. Waiting 60 seconds...")
                    time.sleep(60)
                    continue
                elif response.status_code != 200:
                    logger.error(f"Error response: {response.text}")
                    break
                    
                data = response.json()
                items = data.get('items', [])
                total_count = data.get('total_count', 0)
                
                if not items:
                    break
                    
                all_files.extend(items)
                logger.info(f"Collected {len(all_files)}/{total_count} files")
                
                # Check if we've reached our limit
                if max_results and len(all_files) >= max_results:
                    all_files = all_files[:max_results]
                    break
                
                # Check if we've reached the end
                if len(items) < per_page:
                    break
                    
                page += 1
                
                # API rate limiting
                time.sleep(2)
                
                # GitHub API search has a 1000 result limit
                if len(all_files) >= 1000:
                    logger.warning("Reached GitHub API search limit of 1000 results")
                    break
                    
            except Exception as e:
                logger.error(f"Error in search: {e}")
                break
        
        logger.info(f"Total files collected for '{query}': {len(all_files)}")
        return all_files
    
    def search_claude_files(self) -> List[Dict[str, Any]]:
        """Search for claude.md files using the query from commands.md."""
        query = 'claude extension:md filename:claude'
        return self.search_code_files(query)
    
    def search_gemini_files(self) -> List[Dict[str, Any]]:
        """Search for gemini.md files."""
        query = 'gemini extension:md filename:gemini'
        return self.search_code_files(query)
    
    def search_agents_files(self) -> List[Dict[str, Any]]:
        """Search for AGENTS.md files."""
        query = 'filename:AGENTS.md'
        return self.search_code_files(query)
    
    def use_gh_cli_search(self, search_type: str, query: str) -> List[Dict[str, Any]]:
        """
        Use GitHub CLI for searches (can potentially get more results).
        
        Args:
            search_type: 'code' or 'repos'
            query: Search query
            
        Returns:
            List of search results
        """
        try:
            if search_type == 'code':
                command = ['gh', 'search', 'code', query, '--limit=1000', '--json=url,repository,name,path']
            else:
                return []
            
            logger.info(f"Using GitHub CLI to search: {query}")
            result = subprocess.run(command, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"GitHub CLI error: {result.stderr}")
                return []
            
            results = json.loads(result.stdout) if result.stdout.strip() else []
            logger.info(f"GitHub CLI found {len(results)} results for '{query}'")
            
            return results
            
        except Exception as e:
            logger.error(f"Error using GitHub CLI: {e}")
            return []
    
    def process_code_file(self, file_data: Dict[str, Any], search_type: str) -> Dict[str, Any]:
        """
        Process a single code file result.
        
        Args:
            file_data: Raw file data from GitHub API
            search_type: Type of search (claude, gemini, agents)
            
        Returns:
            Processed file data
        """
        repo_info = file_data.get('repository', {})
        
        return {
            'file_name': file_data.get('name', ''),
            'file_path': file_data.get('path', ''),
            'file_url': file_data.get('html_url', ''),
            'api_url': file_data.get('url', ''),
            'git_url': file_data.get('git_url', ''),
            'repository_id': repo_info.get('id'),
            'repository_name': repo_info.get('name', ''),
            'repository_full_name': repo_info.get('full_name', ''),
            'repository_url': repo_info.get('html_url', ''),
            'repository_description': repo_info.get('description', ''),
            'repository_language': repo_info.get('language', ''),
            'repository_topics': repo_info.get('topics', []),
            'repository_stars': repo_info.get('stargazers_count', 0),
            'repository_forks': repo_info.get('forks_count', 0),
            'repository_created_at': repo_info.get('created_at'),
            'repository_updated_at': repo_info.get('updated_at'),
            'repository_owner': repo_info.get('owner', {}).get('login', ''),
            'search_type': search_type,
            'platform': 'GitHub',
            'ai_tool': self.determine_ai_tool(search_type),
            'source': f'github_{search_type}_files',
        }
    
    def determine_ai_tool(self, search_type: str) -> str:
        """Determine the AI tool based on search type."""
        if search_type == 'claude':
            return 'Claude'
        elif search_type == 'gemini':
            return 'Gemini'
        elif search_type == 'agents':
            return 'Various'  # AGENTS.md could be any AI tool
        else:
            return 'Unknown'
    
    def run_all_searches(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Run searches for all vibe-coded file types.
        
        Focus only on AGENTS.md files which indicate legitimate vibe-coded repositories.
        
        Returns:
            Dictionary with search results by type
        """
        results = {}
        
        # Search for AGENTS.md files - strong indicator of vibe-coded repositories
        logger.info("Searching for AGENTS.md files in vibe-coded repositories...")
        agents_files = self.search_agents_files()
        results['agents'] = [self.process_code_file(f, 'agents') for f in agents_files]
        
        return results
    
    def save_results(self, results: Dict[str, List[Dict[str, Any]]], filename: str = None) -> str:
        """
        Save all search results to JSON file.
        
        Args:
            results: Dictionary of search results
            filename: Output filename (optional)
            
        Returns:
            Path to saved file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"github_code_search_results_{timestamp}.json"
        
        # Calculate totals
        total_files = sum(len(files) for files in results.values())
        
        data = {
            'scrape_timestamp': datetime.now().isoformat(),
            'total_files': total_files,
            'source': 'github_agents_search',
            'description': 'AGENTS.md files from vibe-coded repositories',
            'results_by_type': results,
            'summary': {
                'agents_files': len(results.get('agents', [])),
                'vibe_coded_repositories': len(results.get('agents', [])),
            }
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved {total_files} files to {filename}")
        return filename


def main():
    """Main function to run the GitHub AGENTS.md search."""
    import os
    
    # Get GitHub token from environment
    github_token = os.getenv('GITHUB_TOKEN')
    if not github_token:
        logger.error("GITHUB_TOKEN not found in environment variables!")
        logger.error("Please set your GitHub token: export GITHUB_TOKEN='your_token'")
        return
    
    logger.info(f"Using GitHub token: {github_token[:8]}...")
    processor = GitHubCodeSearchProcessor(github_token=github_token)
    
    logger.info("Starting GitHub AGENTS.md search for vibe-coded repositories...")
    
    # Run AGENTS.md search only
    results = processor.run_all_searches()
    
    # Save results
    output_file = processor.save_results(results)
    
    # Print summary
    print(f"\n=== GitHub AGENTS.md Search Summary ===")
    print(f"Output file: {output_file}")
    print(f"Total AGENTS.md files found: {sum(len(files) for files in results.values())}")
    
    for search_type, files in results.items():
        print(f"{search_type.capitalize()} files: {len(files)}")
        
        if files:
            # Show top repositories
            repos = {}
            for file_data in files:
                repo = file_data['repository_full_name']
                repos[repo] = repos.get(repo, 0) + 1
            
            print(f"  Top {search_type} repositories:")
            for repo, count in sorted(repos.items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"    {repo}: {count} files")
    
    logger.info("GitHub AGENTS.md search completed!")


if __name__ == "__main__":
    main()