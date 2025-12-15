"""
Text analysis utilities.

Provides keyword extraction, readability analysis, and text processing.
"""

import re
from collections import Counter

import textstat

from .constants import STOP_WORDS

# Optional: scikit-learn for TF-IDF
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False


class ContentAnalyzer:
    """
    Analyze text content for keywords, readability, and structure.
    
    Features:
    - Word count and frequency analysis
    - Readability scores (Flesch, Gunning Fog, etc.)
    - Keyword extraction (frequency-based and TF-IDF)
    - N-gram phrase extraction
    
    Example:
        analyzer = ContentAnalyzer("Your text content here...")
        keywords = analyzer.extract_keywords_simple(top_n=10)
        readability = analyzer.get_readability()
    """
    
    def __init__(self, text: str):
        """
        Initialize with text content.
        
        Args:
            text: The text content to analyze
        """
        self.text = text
        self.words = self._extract_words()
        
    def _extract_words(self) -> list[str]:
        """Extract clean words from text."""
        # Remove extra whitespace and convert to lowercase
        clean_text = re.sub(r'\s+', ' ', self.text.lower())
        # Extract words (letters only, minimum 3 characters)
        words = re.findall(r'\b[a-z]{3,}\b', clean_text)
        return words
    
    def get_word_count(self) -> int:
        """Get total word count."""
        return len(self.words)
    
    def get_readability(self) -> dict[str, float]:
        """
        Calculate readability scores.
        
        Returns:
            Dictionary with various readability metrics:
            - flesch_reading_ease: Higher = easier (0-100)
            - flesch_kincaid_grade: US grade level
            - gunning_fog: Years of formal education needed
            - smog_index: Years of education needed
            - automated_readability_index: US grade level
            - reading_time_minutes: Estimated reading time
        """
        if not self.text.strip():
            return {
                "flesch_reading_ease": 0,
                "flesch_kincaid_grade": 0,
                "gunning_fog": 0,
                "smog_index": 0,
                "automated_readability_index": 0,
                "reading_time_minutes": 0,
            }
            
        return {
            "flesch_reading_ease": round(textstat.flesch_reading_ease(self.text), 1),
            "flesch_kincaid_grade": round(textstat.flesch_kincaid_grade(self.text), 1),
            "gunning_fog": round(textstat.gunning_fog(self.text), 1),
            "smog_index": round(textstat.smog_index(self.text), 1),
            "automated_readability_index": round(
                textstat.automated_readability_index(self.text), 1
            ),
            "reading_time_minutes": round(
                textstat.reading_time(self.text, ms_per_char=14.69) / 60, 1
            ),
        }
    
    def extract_keywords_simple(self, top_n: int = 20) -> list[dict]:
        """
        Extract keywords using frequency analysis.
        
        Args:
            top_n: Number of top keywords to return
            
        Returns:
            List of dictionaries with keyword, count, and density
        """
        # Filter out stop words
        filtered_words = [
            w for w in self.words 
            if w not in STOP_WORDS and len(w) > 2
        ]
        word_freq = Counter(filtered_words)
        
        total_words = len(filtered_words) or 1
        keywords = []
        
        for word, count in word_freq.most_common(top_n):
            density = round((count / total_words) * 100, 2)
            keywords.append({
                "keyword": word,
                "count": count,
                "density_percent": density
            })
            
        return keywords
    
    def extract_keywords_tfidf(self, top_n: int = 20) -> list[dict]:
        """
        Extract keywords using TF-IDF (requires sklearn).
        
        Falls back to simple extraction if sklearn is not available.
        
        Args:
            top_n: Number of top keywords to return
            
        Returns:
            List of dictionaries with keyword, tfidf_score, and count
        """
        if not HAS_SKLEARN or not self.text.strip():
            return self.extract_keywords_simple(top_n)
        
        try:
            vectorizer = TfidfVectorizer(
                max_features=100,
                stop_words='english',
                ngram_range=(1, 2),
                min_df=1,
                max_df=0.95
            )
            
            # TF-IDF needs multiple documents, so split into sentences
            sentences = re.split(r'[.!?]+', self.text)
            sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
            
            if len(sentences) < 2:
                return self.extract_keywords_simple(top_n)
            
            tfidf_matrix = vectorizer.fit_transform(sentences)
            feature_names = vectorizer.get_feature_names_out()
            
            # Sum TF-IDF scores across all sentences
            tfidf_scores = tfidf_matrix.sum(axis=0).A1
            
            # Create keyword list with scores
            keywords = []
            for idx in tfidf_scores.argsort()[::-1][:top_n]:
                keyword = feature_names[idx]
                score = round(tfidf_scores[idx], 3)
                count = len(
                    re.findall(r'\b' + re.escape(keyword) + r'\b', self.text.lower())
                )
                keywords.append({
                    "keyword": keyword,
                    "tfidf_score": score,
                    "count": count
                })
                
            return keywords
            
        except Exception:
            return self.extract_keywords_simple(top_n)
    
    def extract_phrases(self, n: int = 2, top_k: int = 10) -> list[dict]:
        """
        Extract common n-gram phrases.
        
        Args:
            n: N-gram size (2 for bigrams, 3 for trigrams, etc.)
            top_k: Number of top phrases to return
            
        Returns:
            List of dictionaries with phrase and count
        """
        if len(self.words) < n:
            return []
            
        ngrams = []
        for i in range(len(self.words) - n + 1):
            ngram = " ".join(self.words[i:i+n])
            ngrams.append(ngram)
            
        phrase_freq = Counter(ngrams)
        
        # Filter out phrases that appear only once
        phrases = [
            {"phrase": phrase, "count": count}
            for phrase, count in phrase_freq.most_common(top_k)
            if count > 1
        ]
        
        return phrases
