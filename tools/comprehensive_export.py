#!/usr/bin/env python3
"""
Comprehensive Database Export System

Exports the enhanced vibe-coded apps database to multiple formats:
- CSV for data analysis
- JSON for API consumption  
- README with statistics
- Platform-specific breakdowns

Includes all metadata: platforms, discovery methods, featured status, etc.
"""

import sqlite3
import csv
import json
import logging
from datetime import datetime
from pathlib import Path
import sys

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseExporter:
    def __init__(self):
        """Initialize database exporter."""
        self.project_root = project_root
        self.db_path = self.project_root / "vibe_coded_apps.db"
        self.export_dir = self.project_root / "exports"
        self.export_dir.mkdir(exist_ok=True)
        
        # Export metadata
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.export_info = {
            'export_date': datetime.now().isoformat(),
            'database_path': str(self.db_path),
            'total_applications': 0,
            'platforms': {},
            'discovery_methods': {},
            'featured_breakdown': {}
        }
    
    def connect_db(self):
        """Connect to the database."""
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found: {self.db_path}")
        
        return sqlite3.connect(self.db_path)
    
    def get_comprehensive_data(self):
        """Get comprehensive application data with all metadata."""
        logger.info("📊 Extracting comprehensive database...")
        
        conn = self.connect_db()
        cursor = conn.cursor()
        
        # Get all applications with platform information
        query = """
        SELECT 
            a.id,
            a.name,
            a.description,
            a.url,
            a.external_id,
            a.created_at,
            a.updated_at,
            a.last_scraped_at,
            a.is_active,
            a.is_featured,
            a.discovery_method,
            p.name as platform_name,
            p.url as platform_url,
            p.description as platform_description
        FROM applications a
        JOIN platforms p ON a.platform_id = p.id
        WHERE a.is_active = 1
        ORDER BY p.name, a.name
        """
        
        cursor.execute(query)
        columns = [description[0] for description in cursor.description]
        rows = cursor.fetchall()
        
        # Convert to list of dictionaries
        applications = []
        for row in rows:
            app_data = dict(zip(columns, row))
            
            # Convert boolean values
            app_data['is_active'] = bool(app_data['is_active'])
            app_data['is_featured'] = bool(app_data['is_featured'])
            
            applications.append(app_data)
        
        conn.close()
        
        self.export_info['total_applications'] = len(applications)
        logger.info(f"✅ Extracted {len(applications)} applications")
        
        return applications
    
    def generate_statistics(self, applications):
        """Generate comprehensive statistics."""
        logger.info("📈 Generating statistics...")
        
        # Platform breakdown
        platform_stats = {}
        discovery_stats = {}
        featured_stats = {'featured': 0, 'not_featured': 0}
        
        for app in applications:
            platform = app['platform_name']
            discovery = app['discovery_method']
            
            # Platform stats
            if platform not in platform_stats:
                platform_stats[platform] = {
                    'total': 0,
                    'featured': 0,
                    'discovery_methods': {}
                }
            
            platform_stats[platform]['total'] += 1
            
            if app['is_featured']:
                platform_stats[platform]['featured'] += 1
                featured_stats['featured'] += 1
            else:
                featured_stats['not_featured'] += 1
            
            # Discovery method stats
            if discovery not in platform_stats[platform]['discovery_methods']:
                platform_stats[platform]['discovery_methods'][discovery] = 0
            platform_stats[platform]['discovery_methods'][discovery] += 1
            
            # Global discovery stats
            if discovery not in discovery_stats:
                discovery_stats[discovery] = 0
            discovery_stats[discovery] += 1
        
        self.export_info['platforms'] = platform_stats
        self.export_info['discovery_methods'] = discovery_stats
        self.export_info['featured_breakdown'] = featured_stats
        
        return platform_stats, discovery_stats, featured_stats
    
    def export_to_csv(self, applications):
        """Export applications to CSV format."""
        logger.info("📄 Exporting to CSV...")
        
        csv_file = self.export_dir / f"vibe_coded_apps_{self.timestamp}.csv"
        
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            if applications:
                fieldnames = applications[0].keys()
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(applications)
        
        logger.info(f"✅ CSV exported: {csv_file}")
        return csv_file
    
    def export_to_json(self, applications):
        """Export applications to JSON format."""
        logger.info("📄 Exporting to JSON...")
        
        json_file = self.export_dir / f"vibe_coded_apps_{self.timestamp}.json"
        
        export_data = {
            'metadata': self.export_info,
            'applications': applications
        }
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ JSON exported: {json_file}")
        return json_file
    
    def export_platform_specific(self, applications):
        """Export platform-specific files."""
        logger.info("📁 Creating platform-specific exports...")
        
        platform_dir = self.export_dir / "platforms"
        platform_dir.mkdir(exist_ok=True)
        
        # Group by platform
        platforms = {}
        for app in applications:
            platform = app['platform_name']
            if platform not in platforms:
                platforms[platform] = []
            platforms[platform].append(app)
        
        platform_files = {}
        
        for platform_name, platform_apps in platforms.items():
            # Clean platform name for filename
            clean_name = platform_name.lower().replace('.', '_').replace(' ', '_')
            
            # JSON export
            json_file = platform_dir / f"{clean_name}_{self.timestamp}.json"
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'platform': platform_name,
                    'total_apps': len(platform_apps),
                    'applications': platform_apps
                }, f, indent=2, ensure_ascii=False)
            
            # CSV export
            csv_file = platform_dir / f"{clean_name}_{self.timestamp}.csv"
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                if platform_apps:
                    fieldnames = platform_apps[0].keys()
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(platform_apps)
            
            platform_files[platform_name] = {
                'json': json_file,
                'csv': csv_file,
                'count': len(platform_apps)
            }
        
        logger.info(f"✅ Platform exports created for {len(platforms)} platforms")
        return platform_files
    
    def generate_readme(self, applications, platform_stats, discovery_stats, featured_stats):
        """Generate comprehensive README with statistics."""
        logger.info("📝 Generating README...")
        
        readme_file = self.export_dir / f"README_{self.timestamp}.md"
        
        readme_content = f"""# Vibe-Coded Apps Database Export

**Export Date**: {datetime.now().strftime('%B %d, %Y at %H:%M:%S')}  
**Total Applications**: {len(applications):,}  
**Database Version**: Enhanced with GitHub discovery and metadata  

## 🎯 Overview

This database contains the most comprehensive collection of authentic vibe-coded applications - projects created through prompt-to-app platforms where users describe what they want and AI generates the complete application.

## 📊 Platform Statistics

| Platform | Total Apps | Featured | Primary Discovery Method |
|----------|------------|----------|-------------------------|
"""
        
        for platform, stats in sorted(platform_stats.items(), key=lambda x: x[1]['total'], reverse=True):
            primary_method = max(stats['discovery_methods'].items(), key=lambda x: x[1])[0]
            readme_content += f"| **{platform}** | {stats['total']:,} | {stats['featured']} | {primary_method} |\n"
        
        readme_content += f"""
## 🔍 Discovery Methods

| Method | Applications | Description |
|--------|--------------|-------------|
| **api_gallery** | {discovery_stats.get('api_gallery', 0):,} | Official platform galleries and showcases |
| **github_search** | {discovery_stats.get('github_search', 0):,} | GitHub repositories discovered via search patterns |
| **api_projects** | {discovery_stats.get('api_projects', 0):,} | Platform project APIs |

## ⭐ Quality Classification

- **Featured Applications**: {featured_stats['featured']:,} (curated/moderated)
- **Discovered Applications**: {featured_stats['not_featured']:,} (community/search discovered)

## 🏗️ Authentic Vibe-Coding Platforms

### v0.dev (Vercel)
- **Focus**: React/Next.js web applications
- **Method**: Prompt → Component → Full app
- **Apps**: {platform_stats.get('v0.dev', {}).get('total', 0):,}

### Bolt (StackBlitz)
- **Focus**: Full-stack applications
- **Method**: Prompt → Complete codebase
- **Apps**: {platform_stats.get('Bolt', {}).get('total', 0):,}

### Lovable (formerly GPT Engineer)
- **Focus**: Web applications with backend
- **Method**: Conversation → Production app
- **Apps**: {platform_stats.get('Lovable', {}).get('total', 0):,}

### GitHub (AGENTS.md projects)
- **Focus**: AI-assisted development markers
- **Method**: Repository analysis for vibe-coding indicators
- **Apps**: {platform_stats.get('GitHub', {}).get('total', 0):,}

## 📁 File Structure

```
exports/
├── vibe_coded_apps_{self.timestamp}.csv       # Complete dataset (CSV)
├── vibe_coded_apps_{self.timestamp}.json      # Complete dataset (JSON)
├── README_{self.timestamp}.md                 # This documentation
└── platforms/                                 # Platform-specific exports
    ├── v0_dev_{self.timestamp}.json
    ├── bolt_{self.timestamp}.json
    ├── lovable_{self.timestamp}.json
    └── github_{self.timestamp}.json
```

## 🔬 Research Methodology

1. **Platform API Discovery**: Systematic exploration of official APIs
2. **GitHub Pattern Matching**: Search for vibe-coding indicators in repositories
3. **Quality Classification**: Distinction between featured vs discovered applications
4. **Metadata Enhancement**: Platform attribution and discovery method tracking

## 📈 Growth & Discovery

This database represents a **{len(applications):,}x increase** from initial collections through:
- Comprehensive platform coverage
- GitHub repository discovery (added {discovery_stats.get('github_search', 0):,} projects)
- Enhanced metadata and classification

## 🔄 Data Schema

Each application includes:
- **Basic Info**: name, description, URL
- **Platform**: source platform and metadata
- **Discovery**: how the app was found
- **Quality**: featured status and curation level
- **Timestamps**: creation, update, and scraping dates

## 🎯 Usage

This dataset is valuable for:
- **Research**: Understanding AI-assisted development trends
- **Analysis**: Platform comparison and feature analysis  
- **Discovery**: Finding examples of prompt-to-app capabilities
- **Benchmarking**: Measuring vibe-coding ecosystem growth

---

*Generated by Vibe-Coded Apps Database Exporter*  
*Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        
        with open(readme_file, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        logger.info(f"✅ README generated: {readme_file}")
        return readme_file
    
    def run_comprehensive_export(self):
        """Run complete export process."""
        logger.info("🚀 Starting comprehensive database export...")
        
        # Get data
        applications = self.get_comprehensive_data()
        
        # Generate statistics
        platform_stats, discovery_stats, featured_stats = self.generate_statistics(applications)
        
        # Export to different formats
        csv_file = self.export_to_csv(applications)
        json_file = self.export_to_json(applications)
        platform_files = self.export_platform_specific(applications)
        readme_file = self.generate_readme(applications, platform_stats, discovery_stats, featured_stats)
        
        # Summary
        logger.info(f"\n🎉 EXPORT COMPLETED!")
        logger.info(f"   📊 Applications exported: {len(applications):,}")
        logger.info(f"   📁 Files created: {len(platform_files) * 2 + 3}")
        logger.info(f"   📍 Export directory: {self.export_dir}")
        
        export_summary = {
            'timestamp': self.timestamp,
            'total_applications': len(applications),
            'platforms_count': len(platform_stats),
            'files_created': {
                'main_csv': str(csv_file),
                'main_json': str(json_file),
                'readme': str(readme_file),
                'platform_files': platform_files
            },
            'statistics': {
                'platforms': platform_stats,
                'discovery_methods': discovery_stats,
                'featured_breakdown': featured_stats
            }
        }
        
        return export_summary

def main():
    """Main export function."""
    exporter = DatabaseExporter()
    summary = exporter.run_comprehensive_export()
    
    print(f"\n✨ Database export completed successfully!")
    print(f"📈 Exported {summary['total_applications']:,} applications")
    print(f"🏢 Across {summary['platforms_count']} platforms")

if __name__ == "__main__":
    main()