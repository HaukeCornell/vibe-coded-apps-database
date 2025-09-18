# Vibe Coded Apps Database

A comprehensive database of AI-generated web applications and tools collected from various vibe coding platforms.

## 📊 Current Dataset (September 2025)

**🎯 Authentic Vibe-Coded Apps**: 2,376 prompt-to-app projects  
**🔬 Research/Experimental Data**: 880 AI-assisted repositories  
**📦 Total Database Entries**: 3,256 applications
**🔗 GitHub Repositories**: 949 linked repositories  

### 🏆 **Platform Breakdown (Authentic Vibe Coding)**
- **v0.dev**: 1,964 UI component generations ⭐⭐⭐⭐⭐
- **Bolt**: 343 full-stack applications ⭐⭐⭐⭐⭐
- **Lovable**: 69 web applications ⭐⭐⭐⭐⭐

### ✅ **Collection Status: COMPLETE**
All major vibe coding platforms have been fully scraped with 2,376 authentic prompt-to-app projects collected!

## 🗂️ Data Tables (GitHub-browsable)

### Core Data
- **[applications_summary.csv](export/applications_summary.csv)** - All 3,256 applications with platform info
- **[platforms.csv](export/platforms.csv)** - 14 platforms (authentic vibe coding + research platforms)
- **[github_repositories_summary.csv](export/github_repositories_summary.csv)** - GitHub repo metadata for 949 projects

### Summary & Statistics
- **[database_statistics.json](export/database_statistics.json)** - Complete breakdown: 2,376 authentic + 880 research

## 🚀 Data Sources

### ✅ **Complete Collection: Authentic Vibe Coding** (2,376 apps)
- **v0.dev Community**: 1,964 prompt-to-UI component projects ⭐⭐⭐⭐⭐
- **Bolt Platform**: 343 prompt-to-fullstack projects ⭐⭐⭐⭐⭐ 
- **Lovable Platform**: 69 prompt-to-webapp projects ⭐⭐⭐⭐⭐

### 🔬 **Research/Experimental Data** (880 entries)
- **GitHub AGENTS.md**: 793 repositories (⚠️ **mostly AI-assisted coding, not vibe coding**)
- **GitHub (other)**: 87 repositories

### 🎯 **Mission Status: COMPLETE!**
All major true vibe coding platforms have been fully collected. The database contains **2,376 authentic prompt-to-app projects** representing the most comprehensive collection of vibe-coded applications available.

## 🛠️ Repository Structure

```
vibe-coded-apps-database/
├── export/                    # GitHub-browsable data tables (CSV/JSON)
├── working-scrapers/          # Proven scraping scripts
├── todo-scrapers/             # Blocked by auth/setup issues  
├── tools/                     # Database utilities
├── docs/                      # Documentation and schemas
├── First-Scrape/             # Reference data (manual collection)
├── data/                     # Raw scraped data
└── vibe_coded_apps.db        # SQLite database
```

## 🎯 Project Goal

**Target**: ~30,000 vibe-coded applications  
**Current**: 2,051 (7% complete)  
**Blocked**: 29,186+ apps waiting for GitHub API auth & platform integration

## 📈 Next Steps

1. **GitHub Authentication** - Unlock 6,712 AGENTS.md vibe-coded repositories
2. **Bolt Integration** - Collect 1,227 projects from bolt.new platform  
3. **Lovable Integration** - Collect 99 projects from lovable.dev platform
4. **Jules Enhancement** - Expand from 1,000 to full 26,945 Google Jules PRs
5. **Data Enhancement** - Extract prompts, authors, creation dates where available

## 🔍 Data Fields

Each application record includes:
- **Basic Info**: name, URL, description, platform
- **Metadata**: creation date, last update, activity status
- **Source**: external ID, community URL, GitHub repository
- **AI Tools**: detected AI assistants used (Claude, GPT, etc.)
- **Extended**: author, tags, thumbnails, demo links (where available)

---

## Academic Research Setup (Legacy Instructions)

Based on the initial scrape, the database contains:

- **GitHub/AGENTS.md**: 6,712 repositories with vibe-coded AGENTS.md files  
- **Bolt Platform**: 1,227 projects from bolt.new AI development platform
- **v0.dev Platform**: 2,008+ community applications from Vercel's AI generator
- **Lovable Platform**: 99 projects from lovable.dev AI development platform  
- **Jules Bot**: 26,945 pull requests from Google's AI code assistant
- **Total**: 31,051+ legitimate vibe-coded applications tracked

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