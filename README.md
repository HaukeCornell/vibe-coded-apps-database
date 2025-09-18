# Vibe Coded Apps Database

A comprehensive database for tracking AI-assisted applications across multiple vibe coding platforms, designed for academic research and industry analysis.

## Overview

This database collects and organizes data about applications created using AI-powered development tools (also known as "vibe coding" platforms). It includes apps from GitHub repositories, v0.dev community, Lovable, Bolt, and other AI-assisted development platforms.

## Features

- **Unified Database Schema**: SQLite database with normalized tables for apps, platforms, GitHub repos, and AI tools
- **Multi-Platform Support**: GitHub, v0.dev, Lovable, Bolt, Replit, and more
- **Automatic Data Processing**: Scripts to import and normalize data from different sources
- **Update Automation**: Continuous data collection with rate limiting and error handling
- **Academic Citations**: Auto-generated BibTeX entries and LaTeX tables for research papers
- **Comprehensive Statistics**: Platform analytics, AI tool usage, and growth metrics

## Quick Start

### Prerequisites

- Python 3.7 or higher
- pip package manager
- Optional: GitHub token for better rate limits

### One-Run Setup

```bash
# Clone the repository
git clone https://github.com/your-username/vibe-coded-apps-database.git
cd vibe-coded-apps-database

# Install dependencies
pip install requests

# Set GitHub token (optional but recommended)
export GITHUB_TOKEN="your_github_token_here"

# Run complete setup in one command
python setup_database.py
```

This will:
1. Create the SQLite database with schema
2. Process existing scraped data
3. Update with fresh data from APIs
4. Generate statistics and citations
5. Create LaTeX files for academic papers

## Current Data

Based on the initial scrape, the database contains:

- **GitHub/Agents**: 6,712 repositories with AGENTS.md files
- **GitHub/Claude**: 7,500 repositories mentioning Claude AI
- **v0.dev**: 2,008+ community applications  
- **GitHub/Gemini**: 1,200 repositories with Gemini AI references
- **Total**: 17,420+ AI-assisted applications tracked

## Database Schema

### Core Tables

- `platforms`: Supported AI coding platforms
- `applications`: Main app registry with URLs and metadata
- `github_repositories`: Detailed GitHub repository information
- `community_apps`: Platform-specific community data
- `ai_tools`: AI technologies used in development
- `application_ai_tools`: Many-to-many relationships

### Views and Analytics

- `platform_statistics`: Apps per platform with time series
- `ai_tool_usage`: Technology adoption metrics
- `github_repository_stats`: Language and popularity analysis

## Usage Examples

### Basic Database Queries

```python
from process_data import VibeCodedAppsDB

db = VibeCodedAppsDB()
db.connect()

# Get platform statistics
cursor = db.conn.cursor()
cursor.execute("SELECT * FROM platform_statistics")
stats = cursor.fetchall()

for row in stats:
    print(f"{row[0]}: {row[1]} apps")
```

### Update Data

```bash
# Update with fresh data from all platforms
python update_data.py
```

### Generate Citations

```bash
# Create LaTeX citations and statistics
python generate_citations.py
```

## Academic Usage

### Citation

The database automatically generates proper academic citations:

```latex
@misc{vibecodedapps2025,
    title={Vibe Coded Apps Database: A Comprehensive Collection of AI-Assisted Applications},
    author={Vibe Coded Apps Research Project},
    year={2025},
    note={Database containing 17,420+ AI-assisted applications across 8 platforms including github.com, v0.dev, claude.ai...},
    url={https://github.com/your-username/vibe-coded-apps-database},
    howpublished={GitHub Repository}
}
```

### LaTeX Table

```latex
\\begin{table}[htbp]
\\centering
\\caption{Vibe Coded Apps Database: Platform Statistics}
\\begin{tabular}{lrrr}
\\toprule
Platform & Total Apps & Last 30 Days & Last 7 Days \\\\
\\midrule
github.com & 15,412 & 234 & 45 \\\\
v0.dev & 2,008 & 156 & 23 \\\\
\\bottomrule
\\end{tabular}
\\end{table}
```

## Data Collection Methods

### GitHub Search API
- Searches for specific file patterns (AGENTS.md, claude.md, etc.)
- Collects repository metadata and file information
- Respects rate limits (5000/hour with token, 60/hour without)

### Community APIs
- v0.dev community showcase scraping
- Bolt Supabase API integration
- Lovable platform data collection

### File Structure

```
vibe-coded-apps-database/
├── First-Scrape/           # Initial scraped data
│   ├── agents_md.json      # GitHub AGENTS.md search results
│   ├── claude.json         # GitHub Claude-related repos
│   ├── v0.json            # v0.dev community URLs
│   └── gemini_md.json     # GitHub Gemini-related repos
├── database_schema.sql     # SQLite schema definition
├── process_data.py        # Data import and normalization
├── update_data.py         # Automated data collection
├── generate_citations.py  # Statistics and LaTeX generation
├── setup_database.py      # One-run setup script
└── commands.md           # API commands used for scraping
```

## Platform Coverage

### Currently Supported
- **GitHub**: Repositories using AI development tools
- **v0.dev**: Vercel's AI web app generator community
- **Claude AI**: Anthropic's AI assistant projects
- **Gemini AI**: Google's AI development projects

### Planned Additions
- **Lovable**: Full-stack AI development platform
- **Bolt**: StackBlitz AI-powered IDE
- **Replit**: AI coding assistant projects
- **Jules**: Google's code assistant
- **Stitch**: Google's development tool
- **Figma Make**: Visual component generator

## Development

### Adding New Platforms

1. Add platform to `platforms` table in schema
2. Create processor class in `process_data.py`
3. Add scraper class in `update_data.py`
4. Update statistics views as needed

### Environment Variables

```bash
export GITHUB_TOKEN="ghp_your_token_here"        # GitHub API access
export LOVABLE_API_KEY="your_lovable_key"       # Lovable API
export BOLT_SUPABASE_KEY="your_supabase_key"    # Bolt data access
```

## Research Applications

This database enables research into:

- **AI-Assisted Development Trends**: Track adoption of different AI tools
- **Platform Comparison**: Analyze strengths of different vibe coding tools
- **Technology Evolution**: Monitor new AI development technologies
- **Community Growth**: Study how AI coding communities develop
- **Code Quality Analysis**: Compare traditionally vs AI-coded applications

## Contributing

1. Fork the repository
2. Add your platform scraper or data processor
3. Update documentation and tests
4. Submit a pull request

## License

This project is open source under the MIT License. The data collected is used for academic and research purposes following each platform's terms of service.

## Acknowledgments

- Thanks to all the vibe coding platforms for making AI-assisted development accessible
- GitHub API for providing comprehensive repository data
- The open source community for sharing their AI-assisted projects

## Support

For questions, issues, or collaboration:
- Open an issue on GitHub
- Email: your-email@domain.com
- Twitter: @yourusername

---

**Note**: This database is for research purposes. Please respect the terms of service of all platforms when using this data.