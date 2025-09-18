# Scraper Status and Data Quality Assessment

## ✅ **High-Quality Vibe Coding Sources** (2,051 authentic apps)

### **Tier 1: Pure Vibe Coding (Prompt → App)**

#### 1. v0.dev Community (`v0_community_scraper.py`)
- **Status**: ✅ COMPLETE - 1,964 projects collected
- **Quality**: ⭐⭐⭐⭐⭐ Pure vibe coding (prompt → UI components)
- **Method**: Manual collection from v0.dev community showcase
- **Data**: UI components generated from natural language prompts
- **Value**: Authentic vibe-coded applications

#### 2. Bolt Supabase Scraper (`bolt_supabase_scraper.py`)
- **Status**: 🔄 PARTIAL - 87 of 1,227 projects collected  
- **Quality**: ⭐⭐⭐⭐⭐ Pure vibe coding (prompt → full-stack apps)
- **Method**: Direct Supabase API access with bearer token
- **Priority**: 🔥 HIGH - Expand to collect remaining 1,140 projects
- **Value**: Complete applications from text descriptions

#### 3. Lovable Community Scraper (`lovable_scraper.py`)
- **Status**: ❌ TODO - 0 of 99 projects collected
- **Quality**: ⭐⭐⭐⭐⭐ Pure vibe coding (prompt → web apps)  
- **Method**: Community API with cursor-based pagination (script ready)
- **Priority**: 🔥 HIGH - Collect all 99 prompt-to-app projects
- **Value**: Complete web applications from natural language

---

## 🔬 **Research/Experimental Sources** (793 entries - mixed quality)

### **Tier 2: Agentic Development**

#### 4. Jules PR Scraper (`jules_pr_scraper.py`)
- **Status**: 🔄 PARTIAL - 1,000 of 26,945 PRs collected
- **Quality**: ⭐⭐⭐ Agentic coding (not interactive vibe coding)
- **Method**: GitHub API search for google-labs-jules[bot] PRs  
- **Priority**: 📚 RESEARCH - Interesting for automation studies
- **Note**: Background automation, not user-driven vibe coding

### **Tier 3: AI-Assisted Development**

#### 5. GitHub AGENTS.md Search (`github_enhanced_search.py`)
- **Status**: ⏸️ PAUSED - 793 of 5,824 repositories collected
- **Quality**: ⭐⭐ Mostly AI-assisted development, NOT vibe coding
- **Method**: GitHub code search for AGENTS.md files
- **Priority**: ⏸️ LOW - Limited vibe coding value discovered
- **Issue**: Manual inspection revealed most are traditional development with AI assistance

**Examples of NON-vibe coding found:**
- `bowmanjd/nix-config` - Configuration files with AI help
- `SonsOfPHP/filesystem` - Library development with AI assistance
- `asleep-ai/asleep-sdk-react-native` - SDK development with AI docs

---

## 🚫 **BLOCKED SCRAPERS (Technical Issues)**

### 1. GitHub Enhanced Search (`github_enhanced_search.py`)
- **Status**: 🚫 BLOCKED - 401 Authentication Error
- **Target**: 6,712 AGENTS.md files from vibe-coded repositories
- **Issue**: Requires GitHub Personal Access Token for code search API
- **Solution Needed**: 
  ```bash
  export GITHUB_TOKEN="ghp_your_token_here"
  ```
- **Potential Impact**: HIGH - AGENTS.md files indicate actual vibe-coded repositories
- **Data Quality**: High - repository metadata, file contents, commit history

### 2. v0 Browser Scraper (`v0_browser_scraper.py`)
- **Status**: 🚫 BLOCKED - Chrome binary not found
- **Target**: 2,008+ v0.dev community projects
- **Issue**: Selenium requires Chrome/ChromeDriver installation
- **Solution Needed**:
  ```bash
  # macOS
  brew install --cask google-chrome
  # or install ChromeDriver manually
  ```
- **Data Quality**: Medium - project URLs, basic metadata
- **Alternative**: Manual collection already provided 1,964 v0 projects

---

## 📋 **TODO LIST**

### High Priority (Unlocks 6,712+ vibe-coded projects)
1. **GitHub API Authentication Setup**
   - Create GitHub Personal Access Token
   - Add token to environment variables
   - Test github_enhanced_search.py script for AGENTS.md files only
   - Expected yield: 6,712 legitimate vibe-coded repositories

### Medium Priority (2,008+ projects)  
2. **Chrome/Selenium Setup**
   - Install Google Chrome or Chromium
   - Install ChromeDriver via webdriver-manager
   - Test v0_browser_scraper.py script
   - Expected yield: 2,008+ v0.dev community projects

### Low Priority (Data Enhancement)
3. **Enhance Existing Data**
   - Extract prompts from README files where available
   - Parse creation dates from git history
   - Identify additional AI tools from file contents
   - Add author attribution where discoverable

### Maintenance
4. **Update Existing Scrapers**
   - Re-run bolt_supabase_scraper.py for new projects
   - Update lovable_scraper.py for new community posts
   - Monitor jules_pr_scraper.py for new bot activity

---

## 🎯 **IMPACT SUMMARY**

| Scraper | Status | Current Yield | Potential Total |
|---------|--------|---------------|-----------------|
| Manual Collection | ✅ Done | 2,051 | 2,051 |
| Bolt Supabase | 🔄 Available | 0 | 1,227 |
| Lovable Community | 🔄 Available | 0 | 99 |
| Jules GitHub PRs | ✅ Partial | 1,000 | 26,945 |
| **GitHub AGENTS.md** | 🚫 **BLOCKED** | 0 | **6,712** |
| **v0 Browser** | 🚫 **BLOCKED** | 0 | **2,008** |
| **TOTAL** | | **3,051** | **38,042** |

**Current Progress**: 3,051 / 38,042 = 8.0% complete  
**Target Goal**: ~30,000 applications = **78.9%** of total potential

## 🚀 **NEXT ACTIONS**

1. **Set up GitHub authentication** - Single biggest impact
2. **Install Chrome for browser scraping** - Second biggest impact  
3. **Run complete data integration** - Combine all sources
4. **Generate final dataset** - Export to GitHub-browsable formats

*The infrastructure is complete. Only authentication and browser setup block us from achieving the full ~15,000 app target.*