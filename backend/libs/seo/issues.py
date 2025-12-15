"""
Issue Detection for AI Indexing.

Detects issues specific to AI bot indexing and llms.txt.
"""


class AIIndexingIssueDetector:
    """
    Detect AI indexing specific issues.
    
    Checks for:
    - Missing llms.txt
    - Missing sitemap.xml
    - Blocked AI bots in robots.txt
    """
    
    def detect_issues(
        self,
        robots_parser,
        llms_response: dict,
        sitemap_response: dict,
    ) -> tuple[list[dict], list[dict]]:
        """
        Detect AI indexing issues.
        
        Args:
            robots_parser: Parsed robots.txt
            llms_response: Response from llms.txt fetch
            sitemap_response: Response from sitemap.xml fetch
            
        Returns:
            Tuple of (issues, recommendations) lists
        """
        issues = []
        recommendations = []
        
        # Check llms.txt
        if llms_response.get("status") != 200:
            issues.append({
                "severity": "medium",
                "category": "ai_indexing",
                "code": "NO_LLMS_TXT",
                "message": "No llms.txt file found for AI/LLM indexing optimization"
            })
            recommendations.append({
                "priority": 2,
                "category": "ai_indexing",
                "action": "Create /llms.txt file to help AI models understand your site structure"
            })
        
        # Check sitemap
        if sitemap_response.get("status") != 200:
            issues.append({
                "severity": "medium",
                "category": "technical",
                "code": "NO_SITEMAP",
                "message": "No sitemap.xml found"
            })
            recommendations.append({
                "priority": 2,
                "category": "technical",
                "action": "Create sitemap.xml for better crawling and indexing"
            })
        
        # Check blocked AI bots
        ai_status = robots_parser.get_ai_bot_status()
        blocked = [
            bot for bot, status in ai_status.items() 
            if 'blocked' in status
        ]
        
        if blocked:
            issues.append({
                "severity": "low",
                "category": "ai_indexing",
                "code": "AI_BOTS_BLOCKED",
                "message": f"Some AI bots are blocked: {', '.join(blocked[:5])}"
            })
        
        return issues, recommendations
