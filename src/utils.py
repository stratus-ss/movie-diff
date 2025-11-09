"""Utility functions for movie title normalization and matching."""

import re
from typing import Optional


class TitleNormalizer:
    """Handles movie title normalization and cleaning."""
    
    def __init__(self):
        self.common_patterns = [
            r'\.\w{3,4}$',  # File extensions
            r'\d{3,4}p',     # Resolution (1080p, 720p)
            r'[xh]\.?26[45]',  # Video codecs
            r'BluRay|BDRip|DVDRip|WEB-?DL',  # Source
            r'AC3|AAC|DTS',  # Audio codecs
        ]
    
    def normalize(self, title: str) -> str:
        """
        Normalize a movie title for comparison.
        
        Args:
            title: Raw movie title or filename
            
        Returns:
            Normalized title string
        """
        # Extract filename from path
        if '/' in title:
            title = title.split('/')[-1]
        
        # Remove file extension
        title = re.sub(r'\.\w{3,4}$', '', title)
        
        # Remove common video patterns
        for pattern in self.common_patterns:
            title = re.sub(pattern, '', title, flags=re.IGNORECASE)
        
        # Replace separators with spaces
        title = re.sub(r'[._\-]+', ' ', title)
        
        # Remove extra whitespace
        title = ' '.join(title.split())
        
        return title.strip()
    
    def extract_year(self, title: str) -> Optional[int]:
        """
        Extract year from movie title.
        
        Args:
            title: Movie title
            
        Returns:
            Year as integer or None if not found
        """
        match = re.search(r'\b(19|20)\d{2}\b', title)
        if match:
            return int(match.group(0))
        return None
    
    def remove_year(self, title: str) -> str:
        """Remove year from title."""
        return re.sub(r'\s*\(?(?:19|20)\d{2}\)?\s*', ' ', title).strip()


class MovieMatcher:
    """Handles fuzzy matching between movie titles."""
    
    def __init__(self, threshold: int = 80, use_distinctive_matching: bool = True):
        """
        Initialize matcher.
        
        Args:
            threshold: Minimum similarity score (0-100) for match
            use_distinctive_matching: Use improved matching that ignores common words
        """
        self.threshold = threshold
        self.use_distinctive_matching = use_distinctive_matching
        self.normalizer = TitleNormalizer()
        
        # Common words to ignore when matching (don't contribute to score)
        self.common_words = {
            'a', 'an', 'the', 'and', 'or', 'for', 'in', 'on', 'at', 'to', 'of',
            'christmas', 'holiday', 'with', 'my', 'your', 'his', 'her'
        }
    
    def _get_distinctive_words(self, title: str) -> set:
        """Extract distinctive words from title (excluding common words)."""
        norm = self.normalizer.normalize(title).lower()
        # Remove years before extracting words
        norm = self.normalizer.remove_year(norm)
        words = norm.split()
        # Filter out common words and keep distinctive ones  
        # Also filter out numbers (years, etc.)
        distinctive = {w for w in words if w not in self.common_words and len(w) > 2 and not w.isdigit()}
        return distinctive
    
    def calculate_similarity(self, title1: str, title2: str) -> float:
        """
        Calculate similarity score between two titles.
        
        Args:
            title1: First movie title
            title2: Second movie title
            
        Returns:
            Similarity score (0-100)
        """
        from rapidfuzz import fuzz
        
        # Normalize both titles and remove years
        # (filenames often don't include years, but Amazon titles do)
        norm1 = self.normalizer.normalize(title1).lower()
        norm1 = self.normalizer.remove_year(norm1).lower()
        
        norm2 = self.normalizer.normalize(title2).lower()
        norm2 = self.normalizer.remove_year(norm2).lower()
        
        if self.use_distinctive_matching:
            # Get distinctive words
            words1 = self._get_distinctive_words(title1)
            words2 = self._get_distinctive_words(title2)
            
            # If no distinctive words, fall back to regular matching
            if not words1 or not words2:
                return fuzz.token_sort_ratio(norm1, norm2)
            
            # Calculate word-level matching
            # How many distinctive words from title1 are in title2?
            common = words1.intersection(words2)
            
            if not common:
                # No distinctive words in common = very low score
                return 0.0
            
            # Calculate Jaccard similarity for distinctive words
            union = words1.union(words2)
            word_score = (len(common) / len(union)) * 100
            
            # Also calculate fuzzy match on the distinctive words only
            distinctive_text1 = ' '.join(sorted(words1))
            distinctive_text2 = ' '.join(sorted(words2))
            fuzzy_score = fuzz.ratio(distinctive_text1, distinctive_text2)
            
            # Combine word matching (70%) and fuzzy matching (30%)
            score = (word_score * 0.7) + (fuzzy_score * 0.3)
            
            return score
        else:
            # Original fuzzy matching
            score = fuzz.token_sort_ratio(norm1, norm2)
            return score
    
    def is_match(self, title1: str, title2: str) -> bool:
        """
        Determine if two titles are a match.
        
        Args:
            title1: First movie title
            title2: Second movie title
            
        Returns:
            True if titles match above threshold
        """
        return self.calculate_similarity(title1, title2) >= self.threshold

