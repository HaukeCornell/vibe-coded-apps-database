-- Vibe Coded Apps Database Schema
-- Unified structure for tracking AI-assisted applications across multiple platforms

-- Main platforms table
CREATE TABLE platforms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(50) UNIQUE NOT NULL,
    url VARCHAR(255),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert known platforms
INSERT INTO platforms (name, url, description) VALUES
('v0.dev', 'https://v0.dev', 'Vercel v0 AI web app generator'),
('lovable.dev', 'https://lovable.dev', 'Lovable AI app development platform'),
('bolt.new', 'https://bolt.new', 'StackBlitz AI-powered development environment'),
('replit.com', 'https://replit.com', 'Replit AI-assisted coding platform'),
('subframe.com', 'https://subframe.com', 'Subframe visual development platform'),
('github.com', 'https://github.com', 'GitHub repositories with AI tools'),
('claude.ai', 'https://claude.ai', 'Anthropic Claude AI assistant'),
('gemini.ai', 'https://gemini.google.com', 'Google Gemini AI'),
('jules.google.com', 'https://jules.google.com', 'Google Jules code assistant'),
('stitch.google.com', 'https://stitch.google.com', 'Google Stitch development tool'),
('figma.com', 'https://figma.com', 'Figma Make visual development');

-- Main applications table
CREATE TABLE applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    platform_id INTEGER NOT NULL,
    external_id VARCHAR(255), -- Platform-specific ID (repo ID, app ID, etc.)
    name VARCHAR(255) NOT NULL,
    url VARCHAR(500) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    
    FOREIGN KEY (platform_id) REFERENCES platforms(id),
    UNIQUE(platform_id, external_id)
);

-- Indexes for applications table
CREATE INDEX idx_applications_platform_id ON applications(platform_id);
CREATE INDEX idx_applications_url ON applications(url);
CREATE INDEX idx_applications_created_at ON applications(created_at);

-- GitHub-specific metadata (for repos from agents_md, claude.json, gemini_md)
CREATE TABLE github_repositories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    application_id INTEGER NOT NULL,
    repo_id INTEGER NOT NULL,
    node_id VARCHAR(100),
    full_name VARCHAR(255) NOT NULL,
    private BOOLEAN DEFAULT FALSE,
    owner_login VARCHAR(255),
    owner_id INTEGER,
    owner_type VARCHAR(50), -- 'User' or 'Organization'
    html_url VARCHAR(500),
    git_url VARCHAR(500),
    clone_url VARCHAR(500),
    ssh_url VARCHAR(500),
    default_branch VARCHAR(100),
    language VARCHAR(100),
    size_kb INTEGER,
    stargazers_count INTEGER DEFAULT 0,
    watchers_count INTEGER DEFAULT 0,
    forks_count INTEGER DEFAULT 0,
    open_issues_count INTEGER DEFAULT 0,
    has_issues BOOLEAN DEFAULT TRUE,
    has_projects BOOLEAN DEFAULT TRUE,
    has_wiki BOOLEAN DEFAULT TRUE,
    has_pages BOOLEAN DEFAULT FALSE,
    archived BOOLEAN DEFAULT FALSE,
    disabled BOOLEAN DEFAULT FALSE,
    pushed_at TIMESTAMP,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    
    FOREIGN KEY (application_id) REFERENCES applications(id) ON DELETE CASCADE,
    UNIQUE(repo_id)
);

-- Indexes for github_repositories table
CREATE INDEX idx_github_repositories_repo_id ON github_repositories(repo_id);
CREATE INDEX idx_github_repositories_full_name ON github_repositories(full_name);
CREATE INDEX idx_github_repositories_owner_login ON github_repositories(owner_login);
CREATE INDEX idx_github_repositories_stargazers_count ON github_repositories(stargazers_count);

-- Files found in repositories (for AGENTS.md, claude.md, etc.)
CREATE TABLE repository_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    github_repo_id INTEGER NOT NULL,
    name VARCHAR(255) NOT NULL,
    path VARCHAR(500) NOT NULL,
    sha VARCHAR(40),
    size_bytes INTEGER,
    file_url VARCHAR(500),
    git_url VARCHAR(500),
    html_url VARCHAR(500),
    download_url VARCHAR(500),
    file_type VARCHAR(50), -- 'agents_md', 'claude_md', 'gemini_md', etc.
    content_snippet TEXT,
    
    FOREIGN KEY (github_repo_id) REFERENCES github_repositories(id) ON DELETE CASCADE,
    UNIQUE(github_repo_id, path)
);

-- Indexes for repository_files table  
CREATE INDEX idx_repository_files_file_type ON repository_files(file_type);
CREATE INDEX idx_repository_files_name ON repository_files(name);

-- Platform-specific metadata for community URLs (v0.dev, etc.)
CREATE TABLE community_apps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    application_id INTEGER NOT NULL,
    community_url VARCHAR(500) NOT NULL,
    community_id VARCHAR(255), -- extracted from URL if available
    title VARCHAR(255),
    author VARCHAR(255),
    tags TEXT, -- JSON array of tags
    thumbnail_url VARCHAR(500),
    live_demo_url VARCHAR(500),
    source_code_url VARCHAR(500),
    creation_date TIMESTAMP,
    
    FOREIGN KEY (application_id) REFERENCES applications(id) ON DELETE CASCADE,
    UNIQUE(community_url)
);

-- Indexes for community_apps table
CREATE INDEX idx_community_apps_community_id ON community_apps(community_id);
CREATE INDEX idx_community_apps_author ON community_apps(author);

-- AI tools and technologies used
CREATE TABLE ai_tools (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) UNIQUE NOT NULL,
    category VARCHAR(50), -- 'llm', 'code_generator', 'assistant', etc.
    provider VARCHAR(100),
    description TEXT
);

-- Insert known AI tools
INSERT INTO ai_tools (name, category, provider, description) VALUES
('Claude', 'llm', 'Anthropic', 'Claude AI assistant for coding and development'),
('GPT-4', 'llm', 'OpenAI', 'GPT-4 language model'),
('Gemini', 'llm', 'Google', 'Google Gemini AI'),
('v0', 'code_generator', 'Vercel', 'AI-powered React component generator'),
('Lovable', 'platform', 'Lovable', 'Full-stack AI development platform'),
('Bolt', 'ide', 'StackBlitz', 'AI-powered development environment'),
('Replit Agent', 'assistant', 'Replit', 'AI coding assistant for Replit'),
('Jules', 'assistant', 'Google', 'Google Jules code assistant'),
('Stitch', 'tool', 'Google', 'Google Stitch development tool'),
('Figma Make', 'generator', 'Figma', 'Visual component generator');

-- Junction table for apps and AI tools used
CREATE TABLE application_ai_tools (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    application_id INTEGER NOT NULL,
    ai_tool_id INTEGER NOT NULL,
    confidence_score FLOAT DEFAULT 0.5, -- 0.0 to 1.0, how confident we are this tool was used
    detection_method VARCHAR(100), -- 'filename', 'content_analysis', 'platform_detection', etc.
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (application_id) REFERENCES applications(id) ON DELETE CASCADE,
    FOREIGN KEY (ai_tool_id) REFERENCES ai_tools(id) ON DELETE CASCADE,
    UNIQUE(application_id, ai_tool_id)
);

-- Indexes for application_ai_tools table
CREATE INDEX idx_application_ai_tools_confidence_score ON application_ai_tools(confidence_score);

-- Scraping jobs and status tracking
CREATE TABLE scraping_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    platform_id INTEGER NOT NULL,
    job_type VARCHAR(50) NOT NULL, -- 'github_search', 'community_scrape', 'api_fetch'
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'running', 'completed', 'failed'
    query_params TEXT, -- JSON of search parameters
    items_found INTEGER DEFAULT 0,
    items_processed INTEGER DEFAULT 0,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    next_run_at TIMESTAMP,
    
    FOREIGN KEY (platform_id) REFERENCES platforms(id)
);

-- Indexes for scraping_jobs table
CREATE INDEX idx_scraping_jobs_status ON scraping_jobs(status);
CREATE INDEX idx_scraping_jobs_next_run_at ON scraping_jobs(next_run_at);
CREATE INDEX idx_scraping_jobs_platform_job_type ON scraping_jobs(platform_id, job_type);

-- Statistics and aggregation views
CREATE VIEW platform_statistics AS
SELECT 
    p.name as platform_name,
    COUNT(a.id) as total_apps,
    COUNT(CASE WHEN a.created_at >= datetime('now', '-30 days') THEN 1 END) as apps_last_30_days,
    COUNT(CASE WHEN a.created_at >= datetime('now', '-7 days') THEN 1 END) as apps_last_7_days,
    MIN(a.created_at) as first_app_date,
    MAX(a.created_at) as latest_app_date
FROM platforms p
LEFT JOIN applications a ON p.id = a.platform_id AND a.is_active = TRUE
GROUP BY p.id, p.name
ORDER BY total_apps DESC;

CREATE VIEW ai_tool_usage AS
SELECT 
    at.name as ai_tool_name,
    at.category,
    at.provider,
    COUNT(aat.application_id) as apps_using_tool,
    AVG(aat.confidence_score) as avg_confidence,
    COUNT(CASE WHEN aat.confidence_score >= 0.8 THEN 1 END) as high_confidence_apps
FROM ai_tools at
LEFT JOIN application_ai_tools aat ON at.id = aat.ai_tool_id
GROUP BY at.id, at.name, at.category, at.provider
ORDER BY apps_using_tool DESC;

CREATE VIEW github_repository_stats AS
SELECT 
    gr.language,
    COUNT(*) as repo_count,
    AVG(gr.stargazers_count) as avg_stars,
    AVG(gr.forks_count) as avg_forks,
    SUM(gr.stargazers_count) as total_stars,
    SUM(gr.forks_count) as total_forks
FROM github_repositories gr
JOIN applications a ON gr.application_id = a.id
WHERE a.is_active = TRUE
GROUP BY gr.language
HAVING repo_count > 0
ORDER BY repo_count DESC;

-- Full-text search indexes for better search capabilities
CREATE VIRTUAL TABLE applications_fts USING fts5(
    name, 
    description, 
    url,
    content='applications',
    content_rowid='id'
);

-- Triggers to keep FTS index updated
CREATE TRIGGER applications_fts_insert AFTER INSERT ON applications BEGIN
    INSERT INTO applications_fts(rowid, name, description, url) 
    VALUES (new.id, new.name, new.description, new.url);
END;

CREATE TRIGGER applications_fts_delete AFTER DELETE ON applications BEGIN
    DELETE FROM applications_fts WHERE rowid = old.id;
END;

CREATE TRIGGER applications_fts_update AFTER UPDATE ON applications BEGIN
    DELETE FROM applications_fts WHERE rowid = old.id;
    INSERT INTO applications_fts(rowid, name, description, url) 
    VALUES (new.id, new.name, new.description, new.url);
END;