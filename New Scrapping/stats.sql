-- 1️⃣ Total number of scraped projects
SELECT COUNT(*) AS total_projects FROM Combined;

-- 2️⃣ List all platforms scraped
SELECT DISTINCT name FROM Combined;

-- 3️⃣ Count of projects per platform
SELECT name AS platform, COUNT(*) AS total_projects
FROM Combined
GROUP BY name
ORDER BY total_projects DESC;

-- 4️⃣ Check for duplicate links
SELECT Link, COUNT(*) AS occurrences
FROM Combined
GROUP BY Link
HAVING COUNT(*) > 1;

-- 5️⃣ Create a reusable summary view
CREATE VIEW platform_statistics AS
SELECT name AS platform,
       COUNT(*) AS total_projects,
       COUNT(DISTINCT Link) AS unique_links
FROM Combined
GROUP BY name
ORDER BY total_projects DESC;

-- 6️⃣ See the summary
SELECT * FROM platform_statistics;