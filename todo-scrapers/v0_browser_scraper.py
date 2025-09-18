#!/usr/bin/env python3
"""
v0.dev Browser Scraper
Based on commands.md specifications for v0 data collection.

This scraper uses Selenium to navigate v0.dev community projects
and collect comprehensive data through scroll-based pagination.
"""

import json
import time
import logging
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class V0BrowserScraper:
    """Scraper for v0.dev community projects using browser automation."""
    
    def __init__(self, headless=True, delay=2):
        self.headless = headless
        self.delay = delay
        self.driver = None
        self.projects = []
        
    def setup_driver(self):
        """Set up Chrome WebDriver with optimized options."""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        logger.info("Chrome WebDriver initialized")
        
    def scroll_to_load_more(self, max_scrolls=50):
        """Scroll down to trigger loading of more projects."""
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        scrolls = 0
        
        while scrolls < max_scrolls:
            # Scroll down to bottom
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(self.delay)
            
            # Calculate new scroll height and compare with last scroll height
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            
            if new_height == last_height:
                logger.info(f"No more content to load after {scrolls} scrolls")
                break
                
            last_height = new_height
            scrolls += 1
            
            if scrolls % 10 == 0:
                logger.info(f"Completed {scrolls} scrolls, found {len(self.get_project_elements())} projects so far")
        
        return scrolls
    
    def get_project_elements(self):
        """Get all project card elements currently loaded on the page."""
        try:
            # Common selectors for project cards on v0.dev
            selectors = [
                '[data-testid*="project"]',
                '.project-card',
                '[class*="project"]',
                '[class*="card"]',
                'a[href*="/chat/"]',
                'div[role="button"]',
                'article',
            ]
            
            elements = []
            for selector in selectors:
                try:
                    found = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if found:
                        elements.extend(found)
                        logger.info(f"Found {len(found)} elements with selector: {selector}")
                        break
                except:
                    continue
                    
            return elements
        except Exception as e:
            logger.error(f"Error getting project elements: {e}")
            return []
    
    def extract_project_data(self, element):
        """Extract data from a single project element."""
        try:
            project_data = {
                'source': 'v0.dev',
                'platform': 'v0',
                'scraped_at': time.strftime('%Y-%m-%d %H:%M:%S'),
            }
            
            # Try to extract project URL
            try:
                link = element.find_element(By.TAG_NAME, 'a')
                project_data['url'] = link.get_attribute('href')
                project_data['project_id'] = project_data['url'].split('/')[-1] if project_data['url'] else None
            except:
                pass
            
            # Try to extract title/name
            try:
                title_selectors = ['h1', 'h2', 'h3', '[class*="title"]', '[class*="name"]']
                for selector in title_selectors:
                    try:
                        title_elem = element.find_element(By.CSS_SELECTOR, selector)
                        project_data['name'] = title_elem.text.strip()
                        break
                    except:
                        continue
            except:
                pass
            
            # Try to extract description
            try:
                desc_selectors = ['p', '[class*="description"]', '[class*="summary"]']
                for selector in desc_selectors:
                    try:
                        desc_elem = element.find_element(By.CSS_SELECTOR, selector)
                        desc_text = desc_elem.text.strip()
                        if len(desc_text) > 10:  # Filter out very short descriptions
                            project_data['description'] = desc_text
                            break
                    except:
                        continue
            except:
                pass
            
            # Try to extract image/thumbnail
            try:
                img = element.find_element(By.TAG_NAME, 'img')
                project_data['image_url'] = img.get_attribute('src')
            except:
                pass
            
            # Try to extract tags/categories
            try:
                tag_selectors = ['[class*="tag"]', '[class*="badge"]', '[class*="chip"]']
                tags = []
                for selector in tag_selectors:
                    try:
                        tag_elems = element.find_elements(By.CSS_SELECTOR, selector)
                        for tag_elem in tag_elems:
                            tag_text = tag_elem.text.strip()
                            if tag_text and len(tag_text) < 50:
                                tags.append(tag_text)
                    except:
                        continue
                if tags:
                    project_data['tags'] = tags
            except:
                pass
            
            # Only return if we have at least URL or name
            if project_data.get('url') or project_data.get('name'):
                return project_data
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error extracting project data: {e}")
            return None
    
    def scrape_community_projects(self, base_url="https://v0.dev/community", max_projects=5000):
        """Scrape v0.dev community projects."""
        logger.info(f"Starting v0.dev community scraping from {base_url}")
        
        try:
            self.setup_driver()
            self.driver.get(base_url)
            
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            logger.info("Page loaded, starting to scroll and collect projects")
            
            # Scroll to load all projects
            scrolls_completed = self.scroll_to_load_more()
            
            # Get all project elements
            project_elements = self.get_project_elements()
            logger.info(f"Found {len(project_elements)} project elements after {scrolls_completed} scrolls")
            
            # Extract data from each project
            unique_projects = {}
            for i, element in enumerate(project_elements):
                try:
                    project_data = self.extract_project_data(element)
                    if project_data:
                        # Use URL or name as unique key to avoid duplicates
                        key = project_data.get('url') or project_data.get('name', f"unknown_{i}")
                        if key not in unique_projects:
                            unique_projects[key] = project_data
                            
                    if len(unique_projects) % 100 == 0:
                        logger.info(f"Extracted data from {len(unique_projects)} unique projects")
                        
                    if len(unique_projects) >= max_projects:
                        logger.info(f"Reached maximum projects limit: {max_projects}")
                        break
                        
                except Exception as e:
                    logger.error(f"Error processing project element {i}: {e}")
                    continue
            
            self.projects = list(unique_projects.values())
            logger.info(f"Successfully scraped {len(self.projects)} unique v0.dev projects")
            
        except Exception as e:
            logger.error(f"Error during scraping: {e}")
        finally:
            if self.driver:
                self.driver.quit()
        
        return self.projects
    
    def save_to_json(self, filename="v0_projects.json"):
        """Save scraped projects to JSON file."""
        filepath = f"/Users/hgs52/Documents/Github/vibe-coded-apps-database/data/{filename}"
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.projects, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved {len(self.projects)} projects to {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Error saving to JSON: {e}")
            return None

def main():
    """Main execution function."""
    scraper = V0BrowserScraper(headless=True, delay=2)
    
    logger.info("Starting v0.dev browser scraping...")
    projects = scraper.scrape_community_projects(max_projects=5000)
    
    if projects:
        logger.info(f"Scraping completed successfully! Found {len(projects)} projects")
        
        # Save to JSON
        filepath = scraper.save_to_json()
        
        # Print sample data
        if len(projects) > 0:
            logger.info("Sample project data:")
            logger.info(json.dumps(projects[0], indent=2))
            
        # Print statistics
        logger.info(f"\nv0.dev Scraping Statistics:")
        logger.info(f"Total projects: {len(projects)}")
        logger.info(f"Projects with URLs: {sum(1 for p in projects if p.get('url'))}")
        logger.info(f"Projects with descriptions: {sum(1 for p in projects if p.get('description'))}")
        logger.info(f"Projects with tags: {sum(1 for p in projects if p.get('tags'))}")
    else:
        logger.error("No projects were scraped!")

if __name__ == "__main__":
    main()