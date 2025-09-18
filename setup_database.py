#!/usr/bin/env python3
"""
Vibe Coded Apps Database - One-Run Setup
Complete database creation, data processing, and citation generation in one command
"""

import os
import sys
import subprocess
import logging
from datetime import datetime
from process_data import main as process_main
from update_data import run_update_cycle
from generate_citations import main as citation_main

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_dependencies():
    """Check if required dependencies are available"""
    logger.info("Checking dependencies...")
    
    required_packages = ['requests', 'sqlite3']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        logger.error(f"Missing required packages: {', '.join(missing_packages)}")
        logger.info("Install with: pip install requests")
        return False
    
    logger.info("All dependencies satisfied")
    return True

def check_data_files():
    """Check if initial data files exist"""
    logger.info("Checking for initial data files...")
    
    data_dir = "First-Scrape"
    required_files = ["agents_md.json", "claude.json", "v0.json", "gemini_md.json"]
    
    missing_files = []
    existing_files = []
    
    for filename in required_files:
        filepath = os.path.join(data_dir, filename)
        if os.path.exists(filepath):
            # Check if file has content
            try:
                with open(filepath, 'r') as f:
                    content = f.read().strip()
                    if content and len(content) > 10:  # More than just empty brackets
                        existing_files.append(filename)
                    else:
                        missing_files.append(f"{filename} (empty)")
            except:
                missing_files.append(f"{filename} (unreadable)")
        else:
            missing_files.append(f"{filename} (not found)")
    
    logger.info(f"Data files found: {', '.join(existing_files)}")
    if missing_files:
        logger.warning(f"Data files missing/empty: {', '.join(missing_files)}")
    
    return len(existing_files) > 0

def setup_database():
    """Set up the database and process initial data"""
    logger.info("Setting up database and processing initial data...")
    
    try:
        # Run the main data processing
        process_main()
        logger.info("Initial data processing completed")
        return True
    except Exception as e:
        logger.error(f"Database setup failed: {e}")
        return False

def update_database():
    """Update database with fresh data"""
    logger.info("Updating database with fresh data...")
    
    try:
        # Check for GitHub token
        github_token = os.getenv('GITHUB_TOKEN')
        if not github_token:
            logger.warning("GITHUB_TOKEN not set. GitHub API requests will be rate-limited.")
            logger.info("Set GITHUB_TOKEN environment variable for better rate limits")
        
        # Run update cycle
        run_update_cycle()
        logger.info("Database update completed")
        return True
    except Exception as e:
        logger.error(f"Database update failed: {e}")
        logger.info("Continuing with existing data...")
        return False

def generate_statistics():
    """Generate statistics and citations"""
    logger.info("Generating statistics and citations...")
    
    try:
        citation_main()
        logger.info("Citation generation completed")
        return True
    except Exception as e:
        logger.error(f"Citation generation failed: {e}")
        return False

def print_final_summary():
    """Print final summary of what was created"""
    print("\\n" + "="*80)
    print("VIBE CODED APPS DATABASE - SETUP COMPLETE")
    print("="*80)
    
    # Check what files were created
    files_created = []
    
    # Database file
    if os.path.exists("vibe_coded_apps.db"):
        files_created.append("✓ vibe_coded_apps.db - Main database file")
    
    # Citation files (find most recent)
    import glob
    
    bib_files = glob.glob("vibe_coded_apps_*.bib")
    if bib_files:
        latest_bib = max(bib_files, key=os.path.getctime)
        files_created.append(f"✓ {latest_bib} - BibTeX citation")
    
    tex_files = glob.glob("vibe_coded_apps_table_*.tex")
    if tex_files:
        latest_tex = max(tex_files, key=os.path.getctime)
        files_created.append(f"✓ {latest_tex} - LaTeX table")
    
    citation_files = glob.glob("vibe_coded_apps_citation_*.tex")
    if citation_files:
        latest_citation = max(citation_files, key=os.path.getctime)
        files_created.append(f"✓ {latest_citation} - Citation text")
    
    readme_files = glob.glob("README_citation_*.md")
    if readme_files:
        latest_readme = max(readme_files, key=os.path.getctime)
        files_created.append(f"✓ {latest_readme} - Usage instructions")
    
    report_files = glob.glob("vibe_coded_apps_report_*.json")
    if report_files:
        latest_report = max(report_files, key=os.path.getctime)
        files_created.append(f"✓ {latest_report} - Full statistics report")
    
    print("\\nFiles Created:")
    for file_desc in files_created:
        print(f"  {file_desc}")
    
    print("\\nNext Steps:")
    print("  1. Review the README_citation_*.md file for usage instructions")
    print("  2. Add the .bib file to your LaTeX project bibliography")
    print("  3. Use the citation text in your academic papers")
    print("  4. Include the LaTeX table for platform statistics")
    print("  5. Set up automation with: python update_data.py")
    
    print("\\nDatabase Schema:")
    print("  - Applications table: Main app registry")
    print("  - GitHub repositories: Detailed repo metadata")
    print("  - Community apps: Platform-specific data")
    print("  - AI tools: Technology tracking")
    print("  - Platform statistics: Auto-generated views")
    
    print("\\n" + "="*80)

def main():
    """Main orchestration function"""
    start_time = datetime.now()
    
    print("="*80)
    print("VIBE CODED APPS DATABASE - ONE-RUN SETUP")
    print("="*80)
    print(f"Started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Step 1: Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Step 2: Check data files
    has_data = check_data_files()
    if not has_data:
        logger.warning("No initial data files found, will create empty database")
    
    # Step 3: Setup database
    if not setup_database():
        logger.error("Failed to setup database")
        sys.exit(1)
    
    # Step 4: Update database (optional, may fail due to rate limits)
    update_success = update_database()
    if not update_success:
        logger.info("Continuing with existing data due to update issues")
    
    # Step 5: Generate statistics and citations
    if not generate_statistics():
        logger.error("Failed to generate citations")
        sys.exit(1)
    
    # Step 6: Print final summary
    end_time = datetime.now()
    duration = end_time - start_time
    
    print_final_summary()
    print(f"\\nCompleted in: {duration.total_seconds():.1f} seconds")
    print(f"Finished at: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()