#!/usr/bin/env python3
"""
Vibe Coded Apps Database - Statistics and Citation Generator
Generate comprehensive statistics and LaTeX bibliography entries
"""

import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Tuple
import logging
from process_data import VibeCodedAppsDB

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class StatisticsGenerator:
    def __init__(self, db: VibeCodedAppsDB):
        self.db = db
        
    def get_platform_statistics(self) -> List[Dict]:
        """Get comprehensive platform statistics"""
        cursor = self.db.conn.cursor()
        
        # Use the view created in schema
        cursor.execute("SELECT * FROM platform_statistics ORDER BY total_apps DESC")
        stats = cursor.fetchall()
        
        result = []
        for row in stats:
            result.append({
                'platform_name': row[0],
                'total_apps': row[1],
                'apps_last_30_days': row[2],
                'apps_last_7_days': row[3],
                'first_app_date': row[4],
                'latest_app_date': row[5]
            })
        
        return result
    
    def get_ai_tool_statistics(self) -> List[Dict]:
        """Get AI tool usage statistics"""
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT * FROM ai_tool_usage ORDER BY apps_using_tool DESC")
        stats = cursor.fetchall()
        
        result = []
        for row in stats:
            result.append({
                'ai_tool_name': row[0],
                'category': row[1],
                'provider': row[2],
                'apps_using_tool': row[3],
                'avg_confidence': row[4],
                'high_confidence_apps': row[5]
            })
        
        return result
    
    def get_github_statistics(self) -> List[Dict]:
        """Get GitHub repository statistics"""
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT * FROM github_repository_stats ORDER BY repo_count DESC")
        stats = cursor.fetchall()
        
        result = []
        for row in stats:
            result.append({
                'language': row[0],
                'repo_count': row[1],
                'avg_stars': row[2],
                'avg_forks': row[3],
                'total_stars': row[4],
                'total_forks': row[5]
            })
        
        return result
    
    def get_total_statistics(self) -> Dict:
        """Get overall database statistics"""
        cursor = self.db.conn.cursor()
        
        stats = {}
        
        # Total applications
        cursor.execute("SELECT COUNT(*) FROM applications WHERE is_active = TRUE")
        stats['total_active_apps'] = cursor.fetchone()[0]
        
        # Total platforms with data
        cursor.execute("""
            SELECT COUNT(DISTINCT p.id) 
            FROM platforms p 
            JOIN applications a ON p.id = a.platform_id 
            WHERE a.is_active = TRUE
        """)
        stats['platforms_with_data'] = cursor.fetchone()[0]
        
        # Total GitHub repositories
        cursor.execute("SELECT COUNT(*) FROM github_repositories")
        stats['total_github_repos'] = cursor.fetchone()[0]
        
        # Total community apps
        cursor.execute("SELECT COUNT(*) FROM community_apps")
        stats['total_community_apps'] = cursor.fetchone()[0]
        
        # Total stars across all GitHub repos
        cursor.execute("SELECT SUM(stargazers_count) FROM github_repositories")
        result = cursor.fetchone()[0]
        stats['total_github_stars'] = result if result else 0
        
        # Most popular language
        cursor.execute("""
            SELECT language, COUNT(*) as count 
            FROM github_repositories 
            WHERE language IS NOT NULL 
            GROUP BY language 
            ORDER BY count DESC 
            LIMIT 1
        """)
        result = cursor.fetchone()
        stats['most_popular_language'] = result[0] if result else 'Unknown'
        stats['most_popular_language_count'] = result[1] if result else 0
        
        # Date range
        cursor.execute("SELECT MIN(created_at), MAX(created_at) FROM applications")
        result = cursor.fetchone()
        stats['earliest_app'] = result[0]
        stats['latest_app'] = result[1]
        
        return stats
    
    def generate_comprehensive_report(self) -> Dict:
        """Generate a comprehensive statistics report"""
        logger.info("Generating comprehensive statistics report")
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'total_statistics': self.get_total_statistics(),
            'platform_statistics': self.get_platform_statistics(),
            'ai_tool_statistics': self.get_ai_tool_statistics(),
            'github_statistics': self.get_github_statistics()
        }
        
        return report
    
    def save_report(self, report: Dict, filename: str = None):
        """Save report to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"vibe_coded_apps_report_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Report saved to {filename}")
        return filename

class LaTeXCitationGenerator:
    def __init__(self, db: VibeCodedAppsDB):
        self.db = db
        
    def generate_bibliography_entry(self, report: Dict) -> str:
        """Generate LaTeX bibliography entry for the database"""
        
        total_stats = report['total_statistics']
        platform_stats = report['platform_statistics']
        
        # Count platforms with data
        platforms_with_data = [p for p in platform_stats if p['total_apps'] > 0]
        platform_names = [p['platform_name'] for p in platforms_with_data[:5]]  # Top 5
        
        # Generate citation
        current_date = datetime.now()
        
        # BibTeX entry
        bibtex = f"""@misc{{vibecodedapps{current_date.year},
    title={{Vibe Coded Apps Database: A Comprehensive Collection of AI-Assisted Applications}},
    author={{Vibe Coded Apps Research Project}},
    year={{{current_date.year}}},
    month={{{current_date.strftime('%B').lower()}}},
    note={{Database containing {total_stats['total_active_apps']:,} AI-assisted applications across {len(platforms_with_data)} platforms including {', '.join(platform_names[:3])}{'...' if len(platform_names) > 3 else ''}}},
    url={{https://github.com/your-username/vibe-coded-apps-database}},
    urldate={{{current_date.strftime('%Y-%m-%d')}}},
    howpublished={{GitHub Repository}}
}}"""
        
        return bibtex
    
    def generate_latex_table(self, report: Dict) -> str:
        """Generate LaTeX table with platform statistics"""
        
        platform_stats = report['platform_statistics']
        
        # Filter platforms with data
        platforms_with_data = [p for p in platform_stats if p['total_apps'] > 0]
        
        latex_table = """\\begin{table}[htbp]
\\centering
\\caption{Vibe Coded Apps Database: Platform Statistics}
\\label{tab:vibe-coded-apps-stats}
\\begin{tabular}{lrrr}
\\toprule
Platform & Total Apps & Last 30 Days & Last 7 Days \\\\
\\midrule
"""
        
        total_apps = 0
        for platform in platforms_with_data:
            latex_table += f"{platform['platform_name']} & {platform['total_apps']:,} & {platform['apps_last_30_days']} & {platform['apps_last_7_days']} \\\\\\\\\n"
            total_apps += platform['total_apps']
        
        latex_table += f"""\\midrule
\\textbf{{Total}} & \\textbf{{{total_apps:,}}} & & \\\\
\\bottomrule
\\end{{tabular}}
\\end{{table}}"""
        
        return latex_table
    
    def generate_citation_text(self, report: Dict) -> str:
        """Generate text for citing the database in papers"""
        
        total_stats = report['total_statistics']
        platform_stats = report['platform_statistics']
        
        platforms_with_data = [p for p in platform_stats if p['total_apps'] > 0]
        platform_count = len(platforms_with_data)
        
        citation_text = f"""The Vibe Coded Apps Database \\cite{{vibecodedapps{datetime.now().year}}} contains {total_stats['total_active_apps']:,} AI-assisted applications collected from {platform_count} platforms, including popular vibe coding tools such as v0.dev, Lovable, Bolt, and GitHub repositories utilizing AI development assistants."""
        
        return citation_text

def generate_full_citation_package(db_path: str = "vibe_coded_apps.db") -> Dict[str, str]:
    """Generate complete citation package with statistics and LaTeX entries"""
    
    # Initialize database and generators
    db = VibeCodedAppsDB(db_path)
    db.connect()
    
    try:
        stats_gen = StatisticsGenerator(db)
        latex_gen = LaTeXCitationGenerator(db)
        
        # Generate comprehensive report
        report = stats_gen.generate_comprehensive_report()
        
        # Save report
        report_file = stats_gen.save_report(report)
        
        # Generate LaTeX components
        bibtex_entry = latex_gen.generate_bibliography_entry(report)
        latex_table = latex_gen.generate_latex_table(report)
        citation_text = latex_gen.generate_citation_text(report)
        
        # Create citation package
        citation_package = {
            'report_file': report_file,
            'bibtex_entry': bibtex_entry,
            'latex_table': latex_table,
            'citation_text': citation_text,
            'total_apps': report['total_statistics']['total_active_apps'],
            'platforms_count': len([p for p in report['platform_statistics'] if p['total_apps'] > 0])
        }
        
        return citation_package
        
    finally:
        db.close()

def save_citation_files(citation_package: Dict[str, str]):
    """Save citation components to files"""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save BibTeX entry
    bibtex_file = f"vibe_coded_apps_{timestamp}.bib"
    with open(bibtex_file, 'w') as f:
        f.write(citation_package['bibtex_entry'])
    
    # Save LaTeX table
    latex_file = f"vibe_coded_apps_table_{timestamp}.tex"
    with open(latex_file, 'w') as f:
        f.write(citation_package['latex_table'])
    
    # Save citation text
    citation_file = f"vibe_coded_apps_citation_{timestamp}.tex"
    with open(citation_file, 'w') as f:
        f.write(citation_package['citation_text'])
    
    # Save README with usage instructions
    readme_content = f"""# Vibe Coded Apps Database Citation Package

Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Statistics Summary
- **Total Applications**: {citation_package['total_apps']:,}
- **Platforms Covered**: {citation_package['platforms_count']}

## Files Included

### 1. BibTeX Entry (`{bibtex_file}`)
Add this entry to your bibliography file (`.bib`) for referencing the database.

### 2. LaTeX Table (`{latex_file}`)
Include this table in your paper to show platform statistics.

### 3. Citation Text (`{citation_file}`)
Use this pre-written citation text in your paper.

### 4. Full Report (`{citation_package['report_file']}`)
Complete JSON report with all statistics and metadata.

## Usage Example

```latex
\\documentclass{{article}}
\\usepackage{{booktabs}}

\\begin{{document}}

{citation_package['citation_text']}

\\input{{{latex_file}}}

\\bibliography{{your_references}}
\\end{{document}}
```

## GitHub Repository
The database and all code is available at: https://github.com/your-username/vibe-coded-apps-database

Please update the GitHub URL to your actual repository location.
"""
    
    readme_file = f"README_citation_{timestamp}.md"
    with open(readme_file, 'w') as f:
        f.write(readme_content)
    
    logger.info(f"Citation package saved:")
    logger.info(f"  - BibTeX: {bibtex_file}")
    logger.info(f"  - LaTeX Table: {latex_file}")
    logger.info(f"  - Citation Text: {citation_file}")
    logger.info(f"  - README: {readme_file}")
    logger.info(f"  - Full Report: {citation_package['report_file']}")
    
    return {
        'bibtex_file': bibtex_file,
        'latex_file': latex_file,
        'citation_file': citation_file,
        'readme_file': readme_file,
        'report_file': citation_package['report_file']
    }

def main():
    """Main function to generate statistics and citations"""
    logger.info("Generating statistics and citation package")
    
    try:
        # Generate citation package
        citation_package = generate_full_citation_package()
        
        # Save all files
        files = save_citation_files(citation_package)
        
        # Print summary
        print("\\n" + "="*60)
        print("VIBE CODED APPS DATABASE - CITATION PACKAGE GENERATED")
        print("="*60)
        print(f"Total Applications: {citation_package['total_apps']:,}")
        print(f"Platforms Covered: {citation_package['platforms_count']}")
        print("\\nFiles generated:")
        for file_type, filename in files.items():
            print(f"  - {filename}")
        
        print("\\n" + "="*60)
        print("BIBTEX ENTRY:")
        print("="*60)
        print(citation_package['bibtex_entry'])
        
        print("\\n" + "="*60)
        print("CITATION TEXT:")
        print("="*60)
        print(citation_package['citation_text'])
        
        logger.info("Citation package generation completed successfully")
        
    except Exception as e:
        logger.error(f"Error generating citation package: {e}")
        raise

if __name__ == "__main__":
    main()