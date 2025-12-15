"""
SEO Score Calculator.

Handles score calculation logic based on analysis results.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from analyzers import HTMLAnalyzer, RobotsParser
    from utils import ContentAnalyzer


@dataclass
class ScoreWeights:
    """Configurable score weights and deductions."""
    
    high_severity: int = 15
    medium_severity: int = 8
    low_severity: int = 3
    
    min_word_count_good: int = 500
    min_word_count_ok: int = 300
    low_content_penalty: int = 20
    medium_content_penalty: int = 10
    
    no_llms_penalty: int = 20
    blocked_bot_penalty: int = 5
    
    # Social sharing penalties
    no_og_penalty: int = 15
    no_twitter_card_penalty: int = 10
    no_social_image_penalty: int = 10


class ScoreCalculator:
    """
    Calculate SEO scores based on analysis results.
    
    Separates scoring logic from the main analyzer for:
    - Easier testing
    - Configurable scoring weights
    - Reusability
    
    Example:
        calculator = ScoreCalculator()
        scores = calculator.calculate(
            html_analyzer=html_analyzer,
            content_analyzer=content_analyzer,
            robots_parser=robots_parser,
            llms_response=llms_response
        )
    """
    
    def __init__(self, weights: ScoreWeights | None = None):
        """
        Initialize with optional custom weights.
        
        Args:
            weights: Custom scoring weights (uses defaults if None)
        """
        self.weights = weights or ScoreWeights()
    
    def calculate(
        self,
        html_analyzer: "HTMLAnalyzer",
        content_analyzer: "ContentAnalyzer",
        robots_parser: "RobotsParser",
        llms_response: dict,
    ) -> dict[str, int]:
        """
        Calculate all SEO scores.
        
        Args:
            html_analyzer: Analyzed HTML results
            content_analyzer: Analyzed content results
            robots_parser: Parsed robots.txt
            llms_response: Response from llms.txt fetch
            
        Returns:
            Dictionary with scores for each category and overall
        """
        scores = {
            "technical": 100,
            "on_page": 100,
            "content": 100,
            "structured_data": 100,
            "ai_readiness": 100,
            "social_sharing": 100,
        }
        
        # Deduct based on issues
        scores = self._apply_issue_deductions(scores, html_analyzer.issues)
        
        # Content score
        scores["content"] = self._calculate_content_score(
            scores["content"], 
            content_analyzer.get_word_count()
        )
        
        # AI readiness score
        scores["ai_readiness"] = self._calculate_ai_readiness_score(
            scores["ai_readiness"],
            llms_response,
            robots_parser
        )
        
        # Social sharing score (from HTML analyzer's social metadata analysis)
        social_metadata = html_analyzer.analyze_social_metadata()
        scores["social_sharing"] = self._calculate_social_sharing_score(
            scores["social_sharing"],
            social_metadata
        )
        
        # Ensure non-negative
        scores = {k: max(0, v) for k, v in scores.items()}
        
        # Overall average
        scores["overall"] = round(sum(scores.values()) / len(scores))
        
        return scores
    
    def _apply_issue_deductions(
        self, 
        scores: dict[str, int], 
        issues: list
    ) -> dict[str, int]:
        """Apply score deductions based on issues found."""
        for issue in issues:
            category = issue.category
            if category in scores:
                if issue.severity == "high":
                    scores[category] -= self.weights.high_severity
                elif issue.severity == "medium":
                    scores[category] -= self.weights.medium_severity
                else:
                    scores[category] -= self.weights.low_severity
        return scores
    
    def _calculate_content_score(self, base_score: int, word_count: int) -> int:
        """Calculate content score based on word count."""
        if word_count < self.weights.min_word_count_ok:
            return base_score - self.weights.low_content_penalty
        elif word_count < self.weights.min_word_count_good:
            return base_score - self.weights.medium_content_penalty
        return base_score
    
    def _calculate_ai_readiness_score(
        self,
        base_score: int,
        llms_response: dict,
        robots_parser: "RobotsParser"
    ) -> int:
        """Calculate AI readiness score."""
        score = base_score
        
        if llms_response.get("status") != 200:
            score -= self.weights.no_llms_penalty
        
        ai_bots = robots_parser.get_ai_bot_status()
        blocked_bots = sum(1 for status in ai_bots.values() if 'blocked' in status)
        if blocked_bots > 0:
            score -= blocked_bots * self.weights.blocked_bot_penalty
        
        return score
    
    def _calculate_social_sharing_score(
        self,
        base_score: int,
        social_metadata: dict,
    ) -> int:
        """
        Calculate social sharing readiness score.
        
        Args:
            base_score: Starting score
            social_metadata: Social metadata analysis from HTML analyzer
            
        Returns:
            Adjusted social sharing score
        """
        score = base_score
        
        og = social_metadata.get("open_graph", {})
        twitter = social_metadata.get("twitter_card", {})
        images = social_metadata.get("social_images", [])
        
        # Penalize missing Open Graph
        if not og.get("present"):
            score -= self.weights.no_og_penalty
        else:
            # Penalize missing required OG tags
            missing_required = og.get("missing_required", [])
            score -= len(missing_required) * 5
        
        # Penalize missing Twitter Card
        if not twitter.get("present"):
            score -= self.weights.no_twitter_card_penalty
        else:
            # Penalize missing required Twitter tags
            missing_required = twitter.get("missing_required", [])
            score -= len(missing_required) * 3
        
        # Penalize missing social images
        if not images:
            score -= self.weights.no_social_image_penalty
        
        return max(0, score)
