#!/usr/bin/env python3
"""
Multi-Platform Vibe Coding Explorer

Explores additional vibe coding platforms:
- Replit 
- Subframe
- Stitch (Google)
- Figma Make

This script investigates the APIs and structures of these platforms.
"""

import requests
import json
import time
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MultiPlatformExplorer:
    def __init__(self):
        """Initialize the multi-platform explorer."""
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'DNT': '1'
        }
    
    def explore_replit(self):
        """Explore Replit for vibe-coded projects."""
        logger.info("🔍 Exploring Replit...")
        
        # Try common API endpoints
        endpoints = [
            "https://replit.com/api/graphql",
            "https://replit.com/api/repls/public",
            "https://replit.com/@replit",
            "https://replit.com/community",
            "https://replit.com/templates"
        ]
        
        for endpoint in endpoints:
            try:
                response = requests.get(endpoint, headers=self.headers, timeout=10)
                logger.info(f"Replit {endpoint}: Status {response.status_code}")
                if response.status_code == 200:
                    logger.info(f"✅ Working endpoint found: {endpoint}")
                    # Check if it contains project data
                    if 'repl' in response.text.lower() or 'project' in response.text.lower():
                        logger.info(f"📋 Contains project data: {len(response.text)} chars")
            except Exception as e:
                logger.warning(f"❌ {endpoint}: {e}")
            
            time.sleep(1)
    
    def explore_subframe(self):
        """Explore Subframe for vibe-coded projects.""" 
        logger.info("🔍 Exploring Subframe...")
        
        endpoints = [
            "https://subframe.com/api/projects",
            "https://subframe.com/api/public",
            "https://subframe.com/gallery",
            "https://subframe.com/showcase",
            "https://app.subframe.com/api"
        ]
        
        for endpoint in endpoints:
            try:
                response = requests.get(endpoint, headers=self.headers, timeout=10)
                logger.info(f"Subframe {endpoint}: Status {response.status_code}")
                if response.status_code == 200:
                    logger.info(f"✅ Working endpoint found: {endpoint}")
                    if 'project' in response.text.lower() or 'component' in response.text.lower():
                        logger.info(f"📋 Contains project data: {len(response.text)} chars")
            except Exception as e:
                logger.warning(f"❌ {endpoint}: {e}")
            
            time.sleep(1)
    
    def explore_stitch(self):
        """Explore Google Stitch for vibe-coded projects."""
        logger.info("🔍 Exploring Google Stitch...")
        
        endpoints = [
            "https://stitch.withgoogle.com/api",
            "https://stitch.withgoogle.com/gallery",
            "https://stitch.withgoogle.com/projects",
            "https://developers.google.com/stitch"
        ]
        
        for endpoint in endpoints:
            try:
                response = requests.get(endpoint, headers=self.headers, timeout=10)
                logger.info(f"Stitch {endpoint}: Status {response.status_code}")
                if response.status_code == 200:
                    logger.info(f"✅ Working endpoint found: {endpoint}")
                    if 'project' in response.text.lower() or 'app' in response.text.lower():
                        logger.info(f"📋 Contains project data: {len(response.text)} chars")
            except Exception as e:
                logger.warning(f"❌ {endpoint}: {e}")
            
            time.sleep(1)
    
    def explore_figma_make(self):
        """Explore Figma Make for vibe-coded projects."""
        logger.info("🔍 Exploring Figma Make...")
        
        endpoints = [
            "https://www.figma.com/make/api",
            "https://www.figma.com/api/make",
            "https://figma.com/community/make",
            "https://www.figma.com/community/plugin/1367634862448906306/Figma-to-Code"
        ]
        
        for endpoint in endpoints:
            try:
                response = requests.get(endpoint, headers=self.headers, timeout=10)
                logger.info(f"Figma Make {endpoint}: Status {response.status_code}")
                if response.status_code == 200:
                    logger.info(f"✅ Working endpoint found: {endpoint}")
                    if 'make' in response.text.lower() or 'generated' in response.text.lower():
                        logger.info(f"📋 Contains project data: {len(response.text)} chars")
            except Exception as e:
                logger.warning(f"❌ {endpoint}: {e}")
            
            time.sleep(1)
    
    def explore_lovable_github(self):
        """Explore GitHub for Lovable bot commits and patterns."""
        logger.info("🔍 Exploring GitHub for Lovable patterns...")
        
        # Search patterns for Lovable-generated repositories
        search_queries = [
            "lovable-ai commits",
            "lovable.app in:readme",
            "\"Built with Lovable\" in:readme",
            "author:lovable-ai",
            "committer:lovable-ai"
        ]
        
        # GitHub search would require authentication, so we'll just log the patterns
        for query in search_queries:
            logger.info(f"📝 GitHub search pattern: {query}")
        
        logger.info("ℹ️  GitHub search requires authentication - see github_enhanced_search.py")
        logger.info("🔗 Example Lovable repo: https://github.com/HaukeCornell/engage-flow-37")
    
    def run_exploration(self):
        """Run exploration of all platforms."""
        logger.info("🚀 Starting multi-platform vibe coding exploration...")
        
        platforms = {
            'Replit': self.explore_replit,
            'Subframe': self.explore_subframe, 
            'Stitch': self.explore_stitch,
            'Figma Make': self.explore_figma_make,
            'Lovable GitHub': self.explore_lovable_github
        }
        
        results = {}
        
        for platform_name, explore_func in platforms.items():
            logger.info(f"\n{'='*50}")
            logger.info(f"Exploring {platform_name}")
            logger.info(f"{'='*50}")
            
            try:
                explore_func()
                results[platform_name] = "explored"
            except Exception as e:
                logger.error(f"Error exploring {platform_name}: {e}")
                results[platform_name] = f"error: {e}"
            
            # Rate limiting between platforms
            time.sleep(3)
        
        # Save exploration results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"platform_exploration_{timestamp}.json"
        
        exploration_data = {
            'timestamp': datetime.now().isoformat(),
            'platforms_explored': list(platforms.keys()),
            'results': results,
            'next_steps': [
                "Identify working API endpoints",
                "Develop specific scrapers for accessible platforms", 
                "Set up GitHub search for Lovable repositories",
                "Implement featured/moderated classification"
            ]
        }
        
        with open(output_file, 'w') as f:
            json.dump(exploration_data, f, indent=2)
        
        logger.info(f"\n📝 Exploration results saved to {output_file}")
        logger.info("🎯 Ready for next phase: specific platform scrapers")

def main():
    """Main exploration function."""
    explorer = MultiPlatformExplorer()
    explorer.run_exploration()

if __name__ == "__main__":
    main()