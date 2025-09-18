#!/usr/bin/env python3
"""
Simple export script to create GitHub-browsable CSV files without pandas dependency.
"""

import sqlite3
import csv
import json
from datetime import datetime
import os

def export_table_to_csv(db_path, table_name, output_file):
    """Export a database table to CSV format."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get table data
    cursor.execute(f"SELECT * FROM {table_name}")
    rows = cursor.fetchall()
    
    # Get column names
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [col[1] for col in cursor.fetchall()]
    
    conn.close()
    
    # Write CSV
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(columns)
        writer.writerows(rows)
    
    print(f"Exported {len(rows)} rows from {table_name} to {output_file}")
    return len(rows)

def export_apps_summary(db_path, output_file):
    """Export applications summary with platform information."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get applications with platform names
    cursor.execute("""
        SELECT 
            a.id,
            a.name,
            a.description,
            a.url,
            p.name as platform,
            a.created_at,
            a.updated_at
        FROM applications a
        JOIN platforms p ON a.platform_id = p.id
        ORDER BY a.created_at DESC
    """)
    
    rows = cursor.fetchall()
    columns = ['id', 'name', 'description', 'url', 'platform', 'created_at', 'updated_at']
    
    conn.close()
    
    # Write CSV
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(columns)
        writer.writerows(rows)
    
    print(f"Exported {len(rows)} applications with platform info to {output_file}")
    return len(rows)

def export_github_repos_summary(db_path, output_file):
    """Export GitHub repositories summary."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get GitHub repositories with application names
    cursor.execute("""
        SELECT 
            gr.id,
            gr.full_name,
            a.name as app_name,
            gr.html_url,
            gr.language,
            gr.stargazers_count,
            gr.forks_count,
            gr.owner_login,
            gr.created_at
        FROM github_repositories gr
        JOIN applications a ON gr.application_id = a.id
        ORDER BY gr.stargazers_count DESC
    """)
    
    rows = cursor.fetchall()
    columns = ['id', 'full_name', 'app_name', 'html_url', 'language', 'stargazers_count', 'forks_count', 'owner_login', 'created_at']
    
    conn.close()
    
    # Write CSV
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(columns)
        writer.writerows(rows)
    
    print(f"Exported {len(rows)} GitHub repositories to {output_file}")
    return len(rows)

def create_summary_stats(db_path, output_file):
    """Create summary statistics JSON file."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Platform statistics
    cursor.execute("""
        SELECT p.name, COUNT(*) as total_apps
        FROM applications a
        JOIN platforms p ON a.platform_id = p.id
        GROUP BY p.name
        ORDER BY total_apps DESC
    """)
    platform_stats = dict(cursor.fetchall())
    
    # Total counts
    cursor.execute("SELECT COUNT(*) FROM applications")
    total_apps = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM platforms")
    total_platforms = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM github_repositories")
    total_github_repos = cursor.fetchone()[0]
    
    # Top languages
    cursor.execute("""
        SELECT language, COUNT(*) as count
        FROM github_repositories 
        WHERE language IS NOT NULL AND language != ''
        GROUP BY language
        ORDER BY count DESC
        LIMIT 10
    """)
    top_languages = dict(cursor.fetchall())
    
    conn.close()
    
    stats = {
        'summary': {
            'total_applications': total_apps,
            'total_platforms': total_platforms,
            'total_github_repositories': total_github_repos,
            'last_updated': datetime.now().isoformat()
        },
        'platform_breakdown': platform_stats,
        'top_programming_languages': top_languages
    }
    
    # Write JSON
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    
    print(f"Created summary statistics in {output_file}")
    return stats

def main():
    """Main export function."""
    db_path = 'vibe_coded_apps.db'
    export_dir = 'export'
    
    # Create export directory
    os.makedirs(export_dir, exist_ok=True)
    
    print("Starting GitHub-visible data export...")
    
    # Export main tables
    export_apps_summary(db_path, f'{export_dir}/applications_summary.csv')
    export_github_repos_summary(db_path, f'{export_dir}/github_repositories_summary.csv')
    export_table_to_csv(db_path, 'platforms', f'{export_dir}/platforms.csv')
    
    # Create statistics
    stats = create_summary_stats(db_path, f'{export_dir}/database_statistics.json')
    
    print("\n=== Export Complete ===")
    print(f"Total Applications: {stats['summary']['total_applications']}")
    print(f"Total Platforms: {stats['summary']['total_platforms']}")
    print(f"Total GitHub Repositories: {stats['summary']['total_github_repositories']}")
    print("\nPlatform Breakdown:")
    for platform, count in stats['platform_breakdown'].items():
        print(f"  {platform}: {count} apps")
    
    print(f"\nFiles exported to {export_dir}/ directory for GitHub visibility")

if __name__ == "__main__":
    main()