# Bolt
curl 'https://ksyayehmkytbjiphildq.supabase.co/rest/v1/gallery_projects' \\ -H 'accept: */*' \\ -H 'accept-language: en-US,en;q=0.9' \\ -H 'accept-profile: public' \\ -H 'apikey: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtzeWF5ZWhta3l0YmppcGhpbGRxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDgyNTIyNDMsImV4cCI6MjA2MzgyODI0M30.n4zBbct5kPTvpfS\_TwsYUaSZRTdA2JWRf27dPNL4TtQ' \\ -H 'authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtzeWF5ZWhta3l0YmppcGhpbGRxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDgyNTIyNDMsImV4cCI6MjA2MzgyODI0M30.n4zBbct5kPTvpfS\_TwsYUaSZRTdA2JWRf27dPNL4TtQ' \\ -H 'dnt: 1' \\ -H 'origin: https://bolt.new' \\ -H 'priority: u=1, i' \\ -H 'referer: https://bolt.new/' \\ -H 'sec-ch-ua: "Not=A?Brand";v="24", "Chromium";v="140"' \\ -H 'sec-ch-ua-mobile: ?0' \\ -H 'sec-ch-ua-platform: "macOS"' \\ -H 'sec-fetch-dest: empty' \\ -H 'sec-fetch-mode: cors' \\ -H 'sec-fetch-site: cross-site' \\ -H 'user-agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10\_15\_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36' \\ -H 'x-client-info: supabase-js-web/2.53.0'


# Lovable
curl 'https://lovable-api.com/projects/community?limit=32&order_by=recent' \  
-H 'accept: */*' \  
-H 'accept-language: en-US,en;q=0.9' \  
-H 'content-type: application/json' \  
-H 'dnt: 1' \  
-H 'origin: https://lovable.dev' \  
-H 'priority: u=1, i' \  
-H 'referer: https://lovable.dev/' \  
-H 'sec-ch-ua: "Not=A?Brand";v="24", "Chromium";v="140"' \  
-H 'sec-ch-ua-mobile: ?0' \  
-H 'sec-ch-ua-platform: "macOS"' \  
-H 'sec-fetch-dest: empty' \  
-H 'sec-fetch-mode: cors' \  
-H 'sec-fetch-site: cross-site' \  
-H 'sec-fetch-storage-access: active' \  
-H 'user-agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36'  


# Google Jules
https://github.com/search?q=jules&type=pullrequests you would need to filter for google-labs-jules as the author but i'm guessting this is on the order of 15-20 thousand pull requests from jule's bot


# Claude

7500 claude.md files for claude code (presumably some ammount of AI usage for each but you can't really speculate) seeing what kinds of things people want to enforce should be interesting. can use the github api. here's the command with gh cli which makes the api easy to use
gh api -X GET search/code -f q='claude extension:md filename:claude' > claude.json


# v0
const data = [...document.querySelectorAll('a[tabindex="-1"].absolute.inset-0.hidden.sm\:block[href^="/community/"]')].map(a=>a.href)

but that one's a bit hard because you actually have to scroll in the browser
again automatable with playwright/puppeteer but I prefer to see what you can just get with requests


# Gemini
gh api -X GET search/code -f q='claude extension:md filename:gemini' > gemini_md.json

# Agents
6700 AGENTS.md gh api -X GET search/code -f q='filename:AGENTS.md' > agents_md.json
