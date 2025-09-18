#!/bin/bash
# GitHub Authentication Setup for Vibe Coded Apps Database
# This script helps set up GitHub Personal Access Token for API access

echo "🔑 GitHub Authentication Setup"
echo "=============================="
echo ""
echo "To unlock 15,412+ GitHub-hosted vibe coding projects, you need a GitHub Personal Access Token."
echo ""
echo "📋 Steps to create a GitHub token:"
echo "1. Go to: https://github.com/settings/tokens"
echo "2. Click 'Generate new token (classic)'"
echo "3. Give it a name: 'Vibe Apps Database'"
echo "4. Select scopes: ✅ public_repo (or repo for private repos)"
echo "5. Click 'Generate token'"
echo "6. Copy the token (starts with 'ghp_')"
echo ""
echo "💡 GitHub Code Search API requires authentication for:"
echo "   • 6,712 AGENTS.md files"
echo "   • 7,500 CLAUDE.md files" 
echo "   • 1,200 GEMINI.md files"
echo "   • Total: 15,412 vibe-coded projects!"
echo ""

# Check if token is already set
if [ -n "$GITHUB_TOKEN" ]; then
    echo "✅ GITHUB_TOKEN is already set in environment"
    echo "Token preview: ${GITHUB_TOKEN:0:8}..."
    echo ""
    echo "Testing GitHub API access..."
    response=$(curl -s -w "%{http_code}" -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user -o /dev/null)
    if [ "$response" = "200" ]; then
        echo "✅ GitHub API access confirmed!"
        echo ""
        echo "🚀 Ready to run enhanced GitHub search:"
        echo "   cd /Users/hgs52/Documents/Github/vibe-coded-apps-database"
        echo "   source venv/bin/activate"
        echo "   python todo-scrapers/github_enhanced_search.py"
    else
        echo "❌ GitHub API access failed (HTTP $response)"
        echo "   Your token may be invalid or expired"
    fi
else
    echo "❌ GITHUB_TOKEN not found in environment"
    echo ""
    echo "🔧 To set your GitHub token:"
    echo ""
    echo "Option 1 - Temporary (current session):"
    echo "   export GITHUB_TOKEN='ghp_your_token_here'"
    echo ""
    echo "Option 2 - Permanent (add to ~/.zshrc or ~/.bashrc):"
    echo "   echo 'export GITHUB_TOKEN=\"ghp_your_token_here\"' >> ~/.zshrc"
    echo "   source ~/.zshrc"
    echo ""
    echo "Option 3 - Interactive setup:"
    read -p "Enter your GitHub token now (or press Enter to skip): " token
    if [ -n "$token" ]; then
        export GITHUB_TOKEN="$token"
        echo "✅ Token set for current session"
        echo ""
        echo "Testing GitHub API access..."
        response=$(curl -s -w "%{http_code}" -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user -o /dev/null)
        if [ "$response" = "200" ]; then
            echo "✅ GitHub API access confirmed!"
            echo ""
            echo "💾 To make permanent, add to your shell profile:"
            echo "   echo 'export GITHUB_TOKEN=\"$GITHUB_TOKEN\"' >> ~/.zshrc"
        else
            echo "❌ GitHub API access failed (HTTP $response)"
            echo "   Please check your token"
        fi
    fi
fi

echo ""
echo "📚 Next steps:"
echo "1. Set GITHUB_TOKEN (if not done above)"  
echo "2. Run: python todo-scrapers/github_enhanced_search.py"
echo "3. Install Chrome for v0 scraping: brew install --cask google-chrome"
echo "4. Run: python todo-scrapers/v0_browser_scraper.py"
echo ""
echo "🎯 Target: Unlock 15,412+ additional vibe-coded applications!"