"""Movie comparison engine."""

from dataclasses import dataclass
from typing import List, Optional
from enum import Enum

from src.movie_parser import OwnedMovie
from src.amazon_product_scraper import AmazonMovie
from src.utils import MovieMatcher


class MatchStatus(Enum):
    """Status of movie match."""
    OWNED = "owned"
    MISSING = "missing"
    UNCERTAIN = "uncertain"


@dataclass
class ComparisonResult:
    """Result of comparing an Amazon movie against owned collection."""
    
    amazon_movie: AmazonMovie
    status: MatchStatus
    confidence: float
    matched_movie: Optional[OwnedMovie] = None
    
    @property
    def title(self) -> str:
        """Get movie title."""
        return self.amazon_movie.title
    
    @property
    def year(self) -> Optional[int]:
        """Get movie year."""
        return self.amazon_movie.year
    
    @property
    def link(self) -> str:
        """Get Amazon link."""
        return self.amazon_movie.link


class MovieComparator:
    """Compares Amazon movies against owned collection."""
    
    def __init__(
        self,
        owned_movies: List[OwnedMovie],
        match_threshold: int = 80,
        uncertain_threshold: int = 60,
        use_distinctive_matching: bool = True
    ):
        """
        Initialize comparator.
        
        Args:
            owned_movies: List of owned movies
            match_threshold: Score for confident match (0-100)
            uncertain_threshold: Score for uncertain match (0-100)
            use_distinctive_matching: Use improved matching that ignores common words
        """
        self.owned_movies = owned_movies
        self.match_threshold = match_threshold
        self.uncertain_threshold = uncertain_threshold
        self.matcher = MovieMatcher(threshold=match_threshold, use_distinctive_matching=use_distinctive_matching)
    
    def compare_single(self, amazon_movie: AmazonMovie) -> ComparisonResult:
        """
        Compare single Amazon movie against collection.
        
        Args:
            amazon_movie: Movie from Amazon list
            
        Returns:
            ComparisonResult with match status
        """
        best_match = None
        best_score = 0.0
        
        for owned in self.owned_movies:
            score = self.matcher.calculate_similarity(
                amazon_movie.title,
                owned.title
            )
            
            if score > best_score:
                best_score = score
                best_match = owned
        
        # Determine status based on score
        if best_score >= self.match_threshold:
            status = MatchStatus.OWNED
        elif best_score >= self.uncertain_threshold:
            status = MatchStatus.UNCERTAIN
        else:
            status = MatchStatus.MISSING
        
        return ComparisonResult(
            amazon_movie=amazon_movie,
            status=status,
            confidence=best_score,
            matched_movie=best_match if status != MatchStatus.MISSING else None
        )
    
    def compare_all(
        self,
        amazon_movies: List[AmazonMovie]
    ) -> List[ComparisonResult]:
        """
        Compare all Amazon movies against collection.
        
        Args:
            amazon_movies: List of movies from Amazon
            
        Returns:
            List of ComparisonResult objects
        """
        results = []
        
        for amazon_movie in amazon_movies:
            result = self.compare_single(amazon_movie)
            results.append(result)
        
        return results
    
    def get_statistics(self, results: List[ComparisonResult]) -> dict:
        """
        Calculate statistics from comparison results.
        
        Args:
            results: List of comparison results
            
        Returns:
            Dictionary with statistics
        """
        total = len(results)
        owned = sum(1 for r in results if r.status == MatchStatus.OWNED)
        missing = sum(1 for r in results if r.status == MatchStatus.MISSING)
        uncertain = sum(1 for r in results if r.status == MatchStatus.UNCERTAIN)
        
        return {
            'total': total,
            'owned': owned,
            'missing': missing,
            'uncertain': uncertain,
            'owned_pct': (owned / total * 100) if total > 0 else 0,
            'missing_pct': (missing / total * 100) if total > 0 else 0,
            'uncertain_pct': (uncertain / total * 100) if total > 0 else 0,
        }

