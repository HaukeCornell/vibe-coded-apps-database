#!/usr/bin/env python3
"""
Advanced Platform Research & Alternative Scraping

Deep investigation of platforms using multiple approaches:
- Web scraping with browser automation
- Alternative API endpoints
- RSS/Sitemap discovery
- GitHub repository analysis
- Community forums and documentation

Platforms: Replit, Subframe, Stitch (Google), Figma Make
"""

import requests
import json
import time
import logging
from datetime import datetime
from pathlib import Path
import sys
import re
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AdvancedPlatformResearcher:
    def __init__(self):
        """Initialize advanced platform research."""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        self.platforms = {
            'replit': {
                'base_url': 'https://replit.com',
                'name': 'Replit',
                'focus': 'Community coding projects and templates'
            },
            'subframe': {
                'base_url': 'https://subframe.com',
                'name': 'Subframe', 
                'focus': 'React component library and visual development'
            },
            'stitch': {
                'base_url': 'https://stitch.withgoogle.com',
                'name': 'Google Stitch',
                'focus': 'Google development tools and integrations'
            },
            'figma_make': {
                'base_url': 'https://www.figma.com',
                'name': 'Figma Make',
                'focus': 'Design-to-code generation and community'
            }
        }
        
        self.results = {}
    
    def discover_endpoints(self, platform_key):
        """Discover API endpoints and data sources for a platform."""
        platform = self.platforms[platform_key]
        base_url = platform['base_url']
        
        logger.info(f"🔍 Researching {platform['name']} ({base_url})")
        
        endpoints_found = []
        
        # 1. Check robots.txt for API hints
        robots_endpoints = self._check_robots_txt(base_url)
        endpoints_found.extend(robots_endpoints)
        
        # 2. Check sitemap for data pages
        sitemap_endpoints = self._check_sitemap(base_url)
        endpoints_found.extend(sitemap_endpoints)
        
        # 3. Analyze main page for API calls
        main_page_apis = self._analyze_main_page(base_url)
        endpoints_found.extend(main_page_apis)
        
        # 4. Check common API patterns
        common_apis = self._check_common_api_patterns(base_url)
        endpoints_found.extend(common_apis)
        
        # 5. Look for GraphQL endpoints
        graphql_endpoints = self._check_graphql_endpoints(base_url)
        endpoints_found.extend(graphql_endpoints)
        
        return endpoints_found
    
    def _check_robots_txt(self, base_url):
        """Check robots.txt for API endpoint hints."""
        endpoints = []
        
        try:
            robots_url = urljoin(base_url, '/robots.txt')
            response = self.session.get(robots_url, timeout=10)
            
            if response.status_code == 200:
                logger.info(f"📄 Found robots.txt for {base_url}")
                
                # Look for API-related paths
                api_patterns = [r'/api/', r'/graphql', r'/_next/static/', r'/v1/', r'/v2/']
                
                for line in response.text.split('\n'):
                    for pattern in api_patterns:
                        if pattern in line.lower():
                            # Extract path
                            if 'Disallow:' in line or 'Allow:' in line:
                                path = line.split(':', 1)[1].strip()
                                if path.startswith('/'):
                                    endpoints.append({
                                        'url': urljoin(base_url, path),
                                        'source': 'robots.txt',
                                        'type': 'api_hint'
                                    })
        
        except Exception as e:
            logger.debug(f"No robots.txt found for {base_url}: {e}")
        
        return endpoints
    
    def _check_sitemap(self, base_url):
        """Check sitemap for interesting data pages."""
        endpoints = []
        
        sitemap_urls = ['/sitemap.xml', '/sitemap_index.xml', '/sitemaps/sitemap.xml']
        
        for sitemap_path in sitemap_urls:
            try:
                sitemap_url = urljoin(base_url, sitemap_path)
                response = self.session.get(sitemap_url, timeout=10)
                
                if response.status_code == 200:
                    logger.info(f"🗺️ Found sitemap: {sitemap_url}")
                    
                    # Parse XML and look for interesting URLs
                    if 'xml' in response.headers.get('content-type', '').lower():
                        # Look for gallery, project, template, community URLs
                        interesting_patterns = [
                            r'gallery', r'projects?', r'templates?', 
                            r'community', r'showcase', r'examples?'
                        ]
                        
                        for pattern in interesting_patterns:
                            matches = re.findall(rf'<loc>([^<]*{pattern}[^<]*)</loc>', response.text, re.IGNORECASE)
                            for match in matches[:5]:  # Limit to avoid spam
                                endpoints.append({
                                    'url': match,
                                    'source': 'sitemap',
                                    'type': 'content_page'
                                })
                    break
            
            except Exception as e:
                logger.debug(f"No sitemap at {sitemap_path}: {e}")
        
        return endpoints
    
    def _analyze_main_page(self, base_url):
        """Analyze main page HTML for API calls and data sources."""
        endpoints = []
        
        try:
            response = self.session.get(base_url, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Look for JavaScript files that might contain API endpoints
                scripts = soup.find_all('script', src=True)
                
                for script in scripts[:10]:  # Limit to avoid too many requests
                    src = script.get('src')
                    if src and any(keyword in src.lower() for keyword in ['app', 'main', 'bundle', 'chunk']):
                        script_url = urljoin(base_url, src)
                        
                        try:
                            script_response = self.session.get(script_url, timeout=10)
                            if script_response.status_code == 200:
                                # Look for API endpoint patterns in JavaScript
                                api_patterns = [
                                    r'["\']\/api\/[^"\']+["\']',
                                    r'["\']https?://[^"\']*api[^"\']*["\']',
                                    r'["\']\/graphql["\']',
                                    r'["\']https?://[^"\']*graphql[^"\']*["\']'
                                ]
                                
                                for pattern in api_patterns:
                                    matches = re.findall(pattern, script_response.text)
                                    for match in matches[:3]:  # Limit results
                                        clean_url = match.strip('"\'')
                                        if clean_url.startswith('/'):
                                            clean_url = urljoin(base_url, clean_url)
                                        
                                        endpoints.append({
                                            'url': clean_url,
                                            'source': 'javascript',
                                            'type': 'api_endpoint'
                                        })
                        
                        except:
                            continue
                
                # Look for inline data or API calls
                inline_scripts = soup.find_all('script', src=False)
                for script in inline_scripts:
                    if script.string:
                        # Look for fetch() or axios calls
                        fetch_patterns = [
                            r'fetch\s*\(\s*["\']([^"\']+)["\']',
                            r'axios\.\w+\s*\(\s*["\']([^"\']+)["\']'
                        ]
                        
                        for pattern in fetch_patterns:
                            matches = re.findall(pattern, script.string)
                            for match in matches[:3]:
                                if match.startswith('/'):
                                    match = urljoin(base_url, match)
                                
                                endpoints.append({
                                    'url': match,
                                    'source': 'inline_script',
                                    'type': 'api_call'
                                })
        
        except Exception as e:
            logger.error(f"Error analyzing main page for {base_url}: {e}")
        
        return endpoints
    
    def _check_common_api_patterns(self, base_url):
        """Check common API endpoint patterns."""
        endpoints = []
        
        common_patterns = [
            # REST API patterns
            '/api/projects', '/api/v1/projects', '/api/v2/projects',
            '/api/gallery', '/api/v1/gallery', '/api/showcase',
            '/api/templates', '/api/v1/templates', '/api/community',
            '/api/public/projects', '/api/public/gallery',
            
            # GraphQL patterns
            '/graphql', '/api/graphql', '/v1/graphql',
            
            # Next.js patterns
            '/api/trpc/projects', '/_next/data',
            
            # Platform-specific patterns
            '/api/repls', '/api/community/repls',  # Replit
            '/api/components', '/api/templates',   # Subframe
            '/api/experiments', '/api/tools',      # Google Stitch
            '/api/files', '/api/community/files'   # Figma
        ]
        
        for pattern in common_patterns:
            url = urljoin(base_url, pattern)
            endpoints.append({
                'url': url,
                'source': 'common_pattern',
                'type': 'api_endpoint'
            })
        
        return endpoints
    
    def _check_graphql_endpoints(self, base_url):
        """Check for GraphQL endpoints and introspection."""
        endpoints = []
        
        graphql_paths = ['/graphql', '/api/graphql', '/v1/graphql', '/graph']
        
        for path in graphql_paths:
            url = urljoin(base_url, path)
            endpoints.append({
                'url': url,
                'source': 'graphql_check',
                'type': 'graphql_endpoint'
            })
        
        return endpoints
    
    def test_endpoints(self, platform_key, endpoints):
        """Test discovered endpoints for data availability."""
        platform = self.platforms[platform_key]
        
        logger.info(f"🧪 Testing {len(endpoints)} endpoints for {platform['name']}")
        
        working_endpoints = []
        
        for endpoint in endpoints:
            url = endpoint['url']
            
            try:
                # Try different HTTP methods
                methods_to_try = ['GET']
                
                if endpoint['type'] == 'graphql_endpoint':
                    methods_to_try.append('POST')
                
                for method in methods_to_try:
                    headers = self.session.headers.copy()
                    
                    if method == 'POST' and endpoint['type'] == 'graphql_endpoint':
                        headers['Content-Type'] = 'application/json'
                        
                        # Try introspection query
                        introspection_query = {
                            "query": "{ __schema { types { name } } }"
                        }
                        
                        response = self.session.post(url, json=introspection_query, headers=headers, timeout=10)
                    else:
                        response = self.session.get(url, headers=headers, timeout=10)
                    
                    if response.status_code == 200:
                        # Check if response contains useful data
                        content_type = response.headers.get('content-type', '').lower()
                        
                        if 'json' in content_type:
                            try:
                                data = response.json()
                                if self._is_useful_data(data):
                                    endpoint['response_size'] = len(response.text)
                                    endpoint['content_type'] = content_type
                                    endpoint['method'] = method
                                    endpoint['status'] = 'working'
                                    working_endpoints.append(endpoint)
                                    
                                    logger.info(f"✅ Working: {url} ({len(response.text)} chars)")
                                    break
                            except:
                                pass
                        
                        elif len(response.text) > 1000:  # HTML page with content
                            endpoint['response_size'] = len(response.text)
                            endpoint['content_type'] = content_type
                            endpoint['method'] = method
                            endpoint['status'] = 'html_page'
                            working_endpoints.append(endpoint)
                            
                            logger.info(f"📄 HTML Page: {url} ({len(response.text)} chars)")
                            break
                    
                    elif response.status_code in [401, 403]:
                        logger.info(f"🔒 Auth required: {url} ({response.status_code})")
                        endpoint['status'] = 'auth_required'
                        endpoint['status_code'] = response.status_code
                        working_endpoints.append(endpoint)
                        break
                    
                time.sleep(0.5)  # Rate limiting
            
            except Exception as e:
                logger.debug(f"❌ Failed: {url} - {str(e)[:50]}...")
                continue
        
        return working_endpoints
    
    def _is_useful_data(self, data):
        """Check if JSON data contains useful project/application information."""
        if not isinstance(data, (dict, list)):
            return False
        
        # Look for common patterns in useful data
        useful_keywords = [
            'projects', 'items', 'results', 'data', 'gallery',
            'templates', 'components', 'repos', 'files',
            'id', 'name', 'title', 'description', 'url'
        ]
        
        data_str = json.dumps(data).lower()
        
        # Must have multiple useful keywords and reasonable size
        keyword_count = sum(1 for keyword in useful_keywords if keyword in data_str)
        
        return keyword_count >= 3 and len(data_str) > 100
    
    def analyze_platform_architecture(self, platform_key, working_endpoints):
        """Analyze platform architecture from working endpoints."""
        platform = self.platforms[platform_key]
        
        logger.info(f"🏗️ Analyzing {platform['name']} architecture...")
        
        analysis = {
            'platform': platform['name'],
            'total_endpoints_tested': len(working_endpoints),
            'api_endpoints': [],
            'html_pages': [],
            'auth_required': [],
            'recommendations': []
        }
        
        for endpoint in working_endpoints:
            if endpoint['status'] == 'working':
                analysis['api_endpoints'].append(endpoint)
            elif endpoint['status'] == 'html_page':
                analysis['html_pages'].append(endpoint)
            elif endpoint['status'] == 'auth_required':
                analysis['auth_required'].append(endpoint)
        
        # Generate recommendations
        if analysis['api_endpoints']:
            analysis['recommendations'].append("Direct API access possible - implement API scraper")
        
        if analysis['html_pages']:
            analysis['recommendations'].append("Web scraping required - use BeautifulSoup/Selenium")
        
        if analysis['auth_required']:
            analysis['recommendations'].append("Authentication needed - investigate OAuth/API keys")
        
        if not any([analysis['api_endpoints'], analysis['html_pages'], analysis['auth_required']]):
            analysis['recommendations'].append("Platform may be private or use non-standard endpoints")
        
        return analysis
    
    def research_all_platforms(self):
        """Research all platforms comprehensively."""
        logger.info("🚀 Starting advanced platform research...")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        for platform_key in self.platforms.keys():
            logger.info(f"\n{'='*60}")
            logger.info(f"🔬 RESEARCHING: {self.platforms[platform_key]['name'].upper()}")
            logger.info(f"{'='*60}")
            
            # Discover endpoints
            endpoints = self.discover_endpoints(platform_key)
            logger.info(f"📡 Discovered {len(endpoints)} potential endpoints")
            
            # Test endpoints
            working_endpoints = self.test_endpoints(platform_key, endpoints)
            logger.info(f"✅ Found {len(working_endpoints)} working endpoints")
            
            # Analyze architecture
            analysis = self.analyze_platform_architecture(platform_key, working_endpoints)
            
            # Store results
            self.results[platform_key] = {
                'platform_info': self.platforms[platform_key],
                'discovered_endpoints': endpoints,
                'working_endpoints': working_endpoints,
                'analysis': analysis,
                'timestamp': datetime.now().isoformat()
            }
        
        # Save comprehensive results
        output_file = f"advanced_platform_research_{timestamp}.json"
        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        logger.info(f"\n💾 Results saved to: {output_file}")
        
        # Generate summary report
        self.generate_summary_report()
        
        return self.results
    
    def generate_summary_report(self):
        """Generate a summary report of the research."""
        logger.info(f"\n{'='*60}")
        logger.info("📋 ADVANCED PLATFORM RESEARCH SUMMARY")
        logger.info(f"{'='*60}")
        
        for platform_key, result in self.results.items():
            platform_name = result['platform_info']['name']
            analysis = result['analysis']
            
            logger.info(f"\n🔍 {platform_name}:")
            logger.info(f"   Working API endpoints: {len(analysis['api_endpoints'])}")
            logger.info(f"   HTML pages found: {len(analysis['html_pages'])}")
            logger.info(f"   Auth required: {len(analysis['auth_required'])}")
            
            if analysis['recommendations']:
                logger.info("   Recommendations:")
                for rec in analysis['recommendations']:
                    logger.info(f"     • {rec}")
            
            # Show best endpoints
            if analysis['api_endpoints']:
                logger.info("   Best API endpoints:")
                for endpoint in analysis['api_endpoints'][:3]:
                    logger.info(f"     • {endpoint['url']} ({endpoint['response_size']} chars)")

def main():
    """Main research function."""
    researcher = AdvancedPlatformResearcher()
    results = researcher.research_all_platforms()
    
    logger.info("\n🎉 Advanced platform research completed!")

if __name__ == "__main__":
    main()