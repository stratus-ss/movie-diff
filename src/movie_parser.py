"""Parser for owned movie collection CSV."""

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import List


@dataclass
class OwnedMovie:
    """Represents a movie in the owned collection."""
    
    filename: str
    filepath: str
    keywords: List[str]
    title: str
    
    @classmethod
    def from_csv_row(cls, row: dict) -> 'OwnedMovie':
        """
        Create OwnedMovie from CSV row.
        
        Args:
            row: Dictionary from CSV DictReader
            
        Returns:
            OwnedMovie instance
        """
        filepath = row['filename'].strip('"')
        filename = Path(filepath).name
        keywords = [k.strip() for k in row['matching_keywords'].split(';')]
        
        # Extract title from filename
        title = Path(filepath).stem
        
        return cls(
            filename=filename,
            filepath=filepath,
            keywords=keywords,
            title=title
        )


class MovieCollectionParser:
    """Parses and manages the owned movie collection."""
    
    def __init__(self, csv_path: str):
        """
        Initialize parser.
        
        Args:
            csv_path: Path to owned movies CSV file
        """
        self.csv_path = csv_path
        self.movies: List[OwnedMovie] = []
    
    def load(self) -> List[OwnedMovie]:
        """
        Load movies from CSV file.
        
        Returns:
            List of OwnedMovie objects
            
        Raises:
            FileNotFoundError: If CSV file doesn't exist
            ValueError: If CSV format is invalid
        """
        if not Path(self.csv_path).exists():
            raise FileNotFoundError(f"CSV file not found: {self.csv_path}")
        
        movies = []
        with open(self.csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            if 'filename' not in reader.fieldnames:
                raise ValueError("CSV must contain 'filename' column")
            
            for row in reader:
                try:
                    movie = OwnedMovie.from_csv_row(row)
                    movies.append(movie)
                except Exception as e:
                    print(f"Warning: Skipping invalid row: {e}")
                    continue
        
        self.movies = movies
        return movies
    
    def get_movie_count(self) -> int:
        """Get total number of movies."""
        return len(self.movies)
    
    def get_titles(self) -> List[str]:
        """Get list of all movie titles."""
        return [movie.title for movie in self.movies]

