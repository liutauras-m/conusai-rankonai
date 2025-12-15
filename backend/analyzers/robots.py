"""
Robots.txt parser and analyzer.

Parses robots.txt files and checks AI bot permissions.
"""

from typing import Optional

from utils.constants import AI_BOTS


class RobotsParser:
    """
    Parse robots.txt and check AI bot permissions.
    
    Features:
    - Parse robots.txt directives
    - Check status of AI crawler bots
    - Extract sitemap URLs
    
    Example:
        parser = RobotsParser(robots_txt_content)
        ai_status = parser.get_ai_bot_status()
        sitemaps = parser.get_sitemap_urls()
    """
    
    def __init__(self, content: Optional[str]):
        """
        Initialize with robots.txt content.
        
        Args:
            content: Raw robots.txt file content (or None)
        """
        self.content = content or ""
        self.rules = self._parse()
    
    def _parse(self) -> dict[str, dict[str, list[str]]]:
        """
        Parse robots.txt into structured rules.
        
        Returns:
            Dictionary mapping user-agents to their allow/disallow rules
        """
        rules: dict[str, dict[str, list[str]]] = {
            "*": {"allow": [], "disallow": []}
        }
        current_agent = "*"
        
        for line in self.content.split("\n"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
                
            if ":" not in line:
                continue
                
            key, value = line.split(":", 1)
            key = key.strip().lower()
            value = value.strip()
            
            if key == "user-agent":
                current_agent = value
                if current_agent not in rules:
                    rules[current_agent] = {"allow": [], "disallow": []}
            elif key == "allow":
                rules[current_agent]["allow"].append(value)
            elif key == "disallow":
                rules[current_agent]["disallow"].append(value)
                
        return rules
    
    def get_ai_bot_status(self) -> dict[str, str]:
        """
        Check status of each known AI bot.
        
        Returns:
            Dictionary mapping bot names to their status:
            - "blocked": Explicitly blocked
            - "allowed": Explicitly allowed
            - "partially_blocked": Some paths blocked
            - "blocked_by_wildcard": Blocked by wildcard rule
            - "allowed_by_default": No specific rules, allowed
            - "not_specified": No rules at all
        """
        status: dict[str, str] = {}
        
        for bot_name in AI_BOTS.keys():
            if bot_name in self.rules:
                # Bot has specific rules
                bot_rules = self.rules[bot_name]
                if "/" in bot_rules["disallow"]:
                    status[bot_name] = "blocked"
                elif bot_rules["allow"] or not bot_rules["disallow"]:
                    status[bot_name] = "allowed"
                else:
                    status[bot_name] = "partially_blocked"
            elif "*" in self.rules:
                # Fall back to wildcard rules
                wildcard = self.rules["*"]
                if "/" in wildcard["disallow"]:
                    status[bot_name] = "blocked_by_wildcard"
                else:
                    status[bot_name] = "allowed_by_default"
            else:
                status[bot_name] = "not_specified"
                
        return status
    
    def get_sitemap_urls(self) -> list[str]:
        """
        Extract sitemap URLs from robots.txt.
        
        Returns:
            List of sitemap URLs declared in the file
        """
        sitemaps = []
        for line in self.content.split("\n"):
            if line.lower().startswith("sitemap:"):
                sitemaps.append(line.split(":", 1)[1].strip())
        return sitemaps
    
    def is_path_allowed(self, path: str, user_agent: str = "*") -> bool:
        """
        Check if a path is allowed for a user agent.
        
        Args:
            path: URL path to check
            user_agent: User agent to check (default: *)
            
        Returns:
            True if path is allowed, False otherwise
        """
        # Get rules for specific agent or fall back to wildcard
        rules = self.rules.get(user_agent, self.rules.get("*", {}))
        
        # Check disallow rules
        for disallow in rules.get("disallow", []):
            if path.startswith(disallow):
                # Check if there's an allow rule that's more specific
                for allow in rules.get("allow", []):
                    if path.startswith(allow) and len(allow) > len(disallow):
                        return True
                return False
                
        return True
