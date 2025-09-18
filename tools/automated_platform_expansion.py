#!/usr/bin/env python3
"""
Automated Platform Expansion Script

Coordinates scraping from new platforms and GitHub discovery.
Runs all new scrapers and integrates results into the main database.
"""

import os
import sys
import json
import sqlite3
import logging
import subprocess
from datetime import datetime
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PlatformExpansion:
    def __init__(self):
        """Initialize platform expansion coordinator."""
        self.project_root = project_root
        self.scrapers_dir = self.project_root / "working-scrapers"
        self.tools_dir = self.project_root / "tools"
        self.db_path = self.project_root / "vibe_coded_apps.db"
        
        self.new_scrapers = [
            ("replit", "scrape_replit.py"),
            ("stitch", "scrape_stitch.py"),
            ("figma_make", "scrape_figma_make.py"),
            ("subframe", "scrape_subframe.py")
        ]
        
        self.discovery_tools = [
            ("lovable_github", "discover_lovable_github.py")
        ]
        
        self.results = {}
    
    def run_scraper(self, platform_name, script_name):
        """Run a specific scraper and capture results."""
        logger.info(f"🚀 Running {platform_name} scraper...")
        
        script_path = self.scrapers_dir / script_name
        
        if not script_path.exists():
            logger.error(f"❌ Scraper not found: {script_path}")
            return None
        
        try:
            # Change to scrapers directory for relative imports
            os.chdir(self.scrapers_dir)
            
            # Run the scraper
            result = subprocess.run(
                [sys.executable, str(script_path)],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                logger.info(f"✅ {platform_name} scraper completed successfully")
                
                # Find the output file (should be newest JSON file with platform name)
                output_files = list(Path('.').glob(f"{platform_name}_projects_*.json"))
                if output_files:
                    latest_file = max(output_files, key=lambda p: p.stat().st_mtime)
                    
                    with open(latest_file, 'r') as f:
                        data = json.load(f)
                    
                    self.results[platform_name] = {
                        'success': True,
                        'file': str(latest_file),
                        'data': data,
                        'projects_count': len(data.get('projects', [])),
                        'stdout': result.stdout,
                        'stderr': result.stderr
                    }
                    
                    logger.info(f"📊 {platform_name}: Found {len(data.get('projects', []))} projects")
                    return data
                else:
                    logger.warning(f"⚠️ No output file found for {platform_name}")
            else:
                logger.error(f"❌ {platform_name} scraper failed with code {result.returncode}")
                logger.error(f"Error output: {result.stderr}")
                
                self.results[platform_name] = {
                    'success': False,
                    'error': result.stderr,
                    'stdout': result.stdout,
                    'return_code': result.returncode
                }
        
        except subprocess.TimeoutExpired:
            logger.error(f"❌ {platform_name} scraper timed out")
            self.results[platform_name] = {
                'success': False,
                'error': 'Timeout after 5 minutes'
            }
        except Exception as e:
            logger.error(f"❌ Error running {platform_name} scraper: {e}")
            self.results[platform_name] = {
                'success': False,
                'error': str(e)
            }
        
        finally:
            # Return to project root
            os.chdir(self.project_root)
        
        return None
    
    def run_discovery_tool(self, tool_name, script_name):
        """Run a discovery tool."""
        logger.info(f"🔍 Running {tool_name} discovery...")
        
        script_path = self.tools_dir / script_name
        
        if not script_path.exists():
            logger.error(f"❌ Discovery tool not found: {script_path}")
            return None
        
        try:
            os.chdir(self.tools_dir)
            
            result = subprocess.run(
                [sys.executable, str(script_path)],
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout for GitHub API
            )
            
            if result.returncode == 0:
                logger.info(f"✅ {tool_name} discovery completed")
                
                # Find output file
                output_files = list(Path('.').glob(f"{tool_name}_*.json"))
                if output_files:
                    latest_file = max(output_files, key=lambda p: p.stat().st_mtime)
                    
                    with open(latest_file, 'r') as f:
                        data = json.load(f)
                    
                    self.results[tool_name] = {
                        'success': True,
                        'file': str(latest_file),
                        'data': data,
                        'discoveries_count': len(data.get('likely_lovable_repositories', [])),
                        'stdout': result.stdout,
                        'stderr': result.stderr
                    }
                    
                    return data
            else:
                logger.error(f"❌ {tool_name} failed: {result.stderr}")
                self.results[tool_name] = {
                    'success': False,
                    'error': result.stderr,
                    'return_code': result.returncode
                }
        
        except Exception as e:
            logger.error(f"❌ Error running {tool_name}: {e}")
            self.results[tool_name] = {
                'success': False,
                'error': str(e)
            }
        
        finally:
            os.chdir(self.project_root)
        
        return None
    
    def integrate_results_to_database(self):
        """Integrate all scraped results into the main database."""
        logger.info("🗄️ Integrating results into database...")
        
        if not self.db_path.exists():
            logger.error("❌ Database not found!")
            return
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        total_new_projects = 0
        
        for platform_name, result in self.results.items():
            if not result.get('success'):
                continue
            
            data = result.get('data', {})
            projects = data.get('projects', [])
            
            if not projects:
                continue
            
            logger.info(f"📥 Integrating {len(projects)} projects from {platform_name}...")
            
            # Check if platform exists
            cursor.execute("SELECT id FROM platforms WHERE name = ?", (platform_name,))
            platform_row = cursor.fetchone()
            
            if not platform_row:
                # Add new platform
                cursor.execute("""
                    INSERT INTO platforms (name, url, description) 
                    VALUES (?, ?, ?)
                """, (
                    platform_name,
                    self._get_platform_url(platform_name),
                    f"Projects from {platform_name} platform"
                ))
                platform_id = cursor.lastrowid
                logger.info(f"➕ Added new platform: {platform_name}")
            else:
                platform_id = platform_row[0]
            
            # Insert projects
            new_count = 0
            for project in projects:
                try:
                    # Check if project already exists
                    cursor.execute("""
                        SELECT id FROM applications 
                        WHERE (url = ? OR title = ?) AND platform_id = ?
                    """, (project.get('url', ''), project.get('title', ''), platform_id))
                    
                    if cursor.fetchone():
                        continue  # Skip duplicates
                    
                    # Insert new project
                    cursor.execute("""
                        INSERT INTO applications (
                            title, description, url, github_url, platform_id,
                            created_at, author, is_featured, discovery_method
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        project.get('title', ''),
                        project.get('description', ''),
                        project.get('url', ''),
                        None,  # No GitHub URL from these platforms
                        platform_id,
                        project.get('created_at'),
                        project.get('author', ''),
                        project.get('is_featured', False),
                        project.get('discovery_method', 'api_scrape')
                    ))
                    
                    new_count += 1
                
                except Exception as e:
                    logger.error(f"Error inserting project {project.get('title', 'Unknown')}: {e}")
            
            total_new_projects += new_count
            logger.info(f"✅ Added {new_count} new projects from {platform_name}")
        
        conn.commit()
        conn.close()
        
        logger.info(f"🎉 Database integration complete! Added {total_new_projects} new projects")
        return total_new_projects
    
    def _get_platform_url(self, platform_name):
        """Get the base URL for a platform."""
        urls = {
            'replit': 'https://replit.com',
            'stitch': 'https://stitch.withgoogle.com',
            'figma_make': 'https://www.figma.com/make',
            'subframe': 'https://app.subframe.com'
        }
        return urls.get(platform_name, '')
    
    def generate_summary_report(self):
        """Generate a summary report of the expansion."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"platform_expansion_report_{timestamp}.json"
        
        summary = {
            'timestamp': datetime.now().isoformat(),
            'expansion_results': self.results,
            'total_platforms_attempted': len(self.new_scrapers) + len(self.discovery_tools),
            'successful_platforms': sum(1 for r in self.results.values() if r.get('success')),
            'total_projects_found': sum(
                r.get('projects_count', 0) for r in self.results.values() 
                if r.get('success') and 'projects_count' in r
            ),
            'total_discoveries': sum(
                r.get('discoveries_count', 0) for r in self.results.values()
                if r.get('success') and 'discoveries_count' in r
            )
        }
        
        with open(report_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"📋 Summary report saved to {report_file}")
        
        # Log summary
        logger.info("📊 PLATFORM EXPANSION SUMMARY:")
        logger.info(f"   Platforms attempted: {summary['total_platforms_attempted']}")
        logger.info(f"   Successful: {summary['successful_platforms']}")
        logger.info(f"   Projects found: {summary['total_projects_found']}")
        logger.info(f"   GitHub discoveries: {summary['total_discoveries']}")
        
        return summary
    
    def run_expansion(self):
        """Run complete platform expansion."""
        logger.info("🚀 Starting automated platform expansion...")
        
        # Run all new platform scrapers
        for platform_name, script_name in self.new_scrapers:
            self.run_scraper(platform_name, script_name)
        
        # Run discovery tools
        for tool_name, script_name in self.discovery_tools:
            self.run_discovery_tool(tool_name, script_name)
        
        # Integrate results into database
        new_projects = self.integrate_results_to_database()
        
        # Generate summary report
        summary = self.generate_summary_report()
        
        logger.info("🎉 Platform expansion completed!")
        return summary

def main():
    """Main expansion function."""
    expander = PlatformExpansion()
    summary = expander.run_expansion()
    
    print(f"\n🎯 Platform expansion completed!")
    print(f"   Found {summary['total_projects_found']} new projects")
    print(f"   Found {summary['total_discoveries']} GitHub discoveries")
    print(f"   Success rate: {summary['successful_platforms']}/{summary['total_platforms_attempted']}")

if __name__ == "__main__":
    main()