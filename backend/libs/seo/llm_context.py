"""
LLM Context Generator.

Generates context summaries and prompts for LLM analysis.
"""

from utils.language import get_language_context_for_ai


class LLMContextGenerator:
    """
    Generate context and prompts for LLM-based analysis.
    
    Creates structured summaries that can be used by AI models
    to provide improvement suggestions.
    """
    
    def generate_context(self, result: dict) -> dict:
        """
        Generate a summary context for LLM analysis.
        
        Args:
            result: Full analysis result dictionary
            
        Returns:
            Condensed context dictionary for LLM consumption
        """
        return {
            "summary": f"SEO analysis for {result['url']}",
            "overall_score": result["scores"]["overall"],
            "critical_issues_count": len(
                [i for i in result["issues"] if i["severity"] == "high"]
            ),
            "total_issues_count": len(result["issues"]),
            "key_metrics": self._extract_key_metrics(result),
            "top_keywords": [
                k["keyword"] 
                for k in result["content"]["keywords_frequency"][:5]
            ],
            "prompt_for_improvement": self.generate_improvement_prompt(result),
        }
    
    def _extract_key_metrics(self, result: dict) -> dict:
        """Extract key metrics from analysis result."""
        language_info = result.get("language", {})
        return {
            "has_title": result["metadata"]["title"]["value"] is not None,
            "has_meta_description": result["metadata"]["description"]["value"] is not None,
            "has_h1": result["headings"]["h1"]["count"] == 1,
            "word_count": result["content"]["word_count"],
            "has_schema": len(result["structured_data"]["json_ld"]) > 0,
            "has_og_tags": len(result["structured_data"]["open_graph"]) > 0,
            "is_https": result["technical"]["https"],
            "has_llms_txt": result["ai_indexing"]["llms_txt"]["present"],
            "has_sitemap": result["ai_indexing"]["sitemap_xml"]["present"],
            "language_code": language_info.get("code"),
            "language_name": language_info.get("name"),
            "language_confidence": language_info.get("confidence"),
            "is_multilingual": len(language_info.get("alternatives", [])) > 0,
        }
    
    def generate_improvement_prompt(self, result: dict) -> str:
        """
        Generate a prompt for LLM to provide improvement suggestions.
        
        Args:
            result: Full analysis result dictionary
            
        Returns:
            Formatted prompt string
        """
        issues_summary = "\n".join([
            f"- [{i['severity'].upper()}] {i['message']}"
            for i in result["issues"][:10]
        ])
        
        top_keywords = ", ".join([
            k["keyword"] 
            for k in result["content"]["keywords_frequency"][:5]
        ])
        
        # Get language context
        language_info = result.get("language", {})
        language_context = get_language_context_for_ai(language_info)
        
        return f"""Analyze this SEO report and provide specific improvement recommendations:

URL: {result['url']}
Overall Score: {result['scores']['overall']}/100
{language_context}

Current Issues:
{issues_summary}

Key Metrics:
- Word Count: {result['content']['word_count']}
- Has Structured Data: {len(result['structured_data']['json_ld']) > 0}
- AI Indexing Ready: {result['ai_indexing']['llms_txt']['present']}
- Top Keywords: {top_keywords}

Please provide:
1. Priority fixes for critical SEO issues
2. Content optimization suggestions based on keywords
3. Structured data recommendations
4. AI indexing optimization tips
5. Language-specific SEO recommendations (if applicable)
"""
