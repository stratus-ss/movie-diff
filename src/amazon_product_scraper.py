"""Enhanced Amazon product page scraper for movie collections."""

import re
import time
from typing import List, Dict, Optional
from dataclasses import dataclass

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager


@dataclass
class AmazonMovie:
    """Represents a movie from Amazon listing."""
    
    title: str
    year: Optional[int]
    link: str
    price: Optional[str] = None
    
    def __str__(self):
        year_str = f" ({self.year})" if self.year else ""
        return f"{self.title}{year_str}"


@dataclass
class ProductInfo:
    """Information about an Amazon product."""
    
    title: str
    url: str
    description: str
    movies: List[str]


class AmazonProductScraper:
    """Scrapes movie collections from Amazon product pages."""
    
    def __init__(self, headless: bool = True, verbose: bool = False):
        """
        Initialize scraper.
        
        Args:
            headless: Run browser in headless mode
            verbose: Print debug information
        """
        self.headless = headless
        self.verbose = verbose
        self.driver = None
    
    def _init_driver(self):
        """Initialize Selenium WebDriver."""
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument('--headless=new')
        
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Disable automation flags
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Remove webdriver property
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    def _close_driver(self):
        """Close WebDriver."""
        if self.driver:
            self.driver.quit()
            self.driver = None
    
    def _log(self, message: str):
        """Print debug message if verbose."""
        if self.verbose:
            print(f"[DEBUG] {message}")
    
    def scrape_product(self, url: str) -> ProductInfo:
        """
        Scrape a single Amazon product page.
        
        Args:
            url: Amazon product URL
            
        Returns:
            ProductInfo object
        """
        try:
            if not self.driver:
                self._init_driver()
            
            self._log(f"Loading URL: {url}")
            self.driver.get(url)
            
            # Wait for page to load
            time.sleep(3)
            
            # Get page title
            title = self._get_title()
            self._log(f"Title: {title}")
            
            # Get product description
            description = self._get_description()
            self._log(f"Description length: {len(description)} chars")
            
            # Extract movie titles from description
            movies = self._extract_movies_from_text(description)
            
            # Also try extracting from product title as supplement
            # Many collections list movies in the title like "Movie 1/ Movie 2/ Movie 3"
            if '/' in title:
                self._log("Checking product title for additional movies...")
                title_movies = self._extract_from_title(title)
                # Add any movies not already found
                for movie in title_movies:
                    if movie not in movies:
                        movies.append(movie)
                        self._log(f"Added from title: {movie}")
            
            # Final deduplication: remove duplicates where one has year and one doesn't
            # e.g., "Movie (2019)" and "Movie" should only keep one
            deduplicated = []
            seen_normalized = set()
            for movie in movies:
                # Normalize: remove year and lowercase for comparison
                normalized = re.sub(r'\s*\(?\d{4}\)?\s*', '', movie).lower().strip()
                if normalized not in seen_normalized:
                    seen_normalized.add(normalized)
                    deduplicated.append(movie)
                    self._log(f"Keeping: {movie}")
                else:
                    self._log(f"Removing duplicate: {movie} (same as existing)")
            
            movies = deduplicated
            self._log(f"Found {len(movies)} movies total after deduplication")
            
            return ProductInfo(
                title=title,
                url=url,
                description=description,
                movies=movies
            )
            
        except Exception as e:
            self._log(f"Error scraping {url}: {e}")
            raise
    
    def scrape_multiple_products(self, urls: List[str]) -> List[ProductInfo]:
        """
        Scrape multiple Amazon product pages.
        
        Args:
            urls: List of Amazon product URLs
            
        Returns:
            List of ProductInfo objects
        """
        try:
            self._init_driver()
            products = []
            
            for i, url in enumerate(urls, 1):
                print(f"Scraping product {i}/{len(urls)}...")
                try:
                    product = self.scrape_product(url)
                    products.append(product)
                    time.sleep(2)  # Be nice to Amazon
                except Exception as e:
                    print(f"  Warning: Failed to scrape {url}: {e}")
                    continue
            
            return products
            
        finally:
            self._close_driver()
    
    def _get_title(self) -> str:
        """Extract product title from page."""
        selectors = [
            '#productTitle',
            'h1.a-size-large',
            'span#productTitle',
        ]
        
        for selector in selectors:
            try:
                element = self.driver.find_element(By.CSS_SELECTOR, selector)
                title = element.text.strip()
                if title:
                    return title
            except:
                continue
        
        return "Unknown Product"
    
    def _get_description(self) -> str:
        """Extract product description from page."""
        text_parts = []
        
        # Priority 1: Product Description section (most reliable for movie collections)
        try:
            desc = self.driver.find_element(By.CSS_SELECTOR, '#productDescription')
            text = desc.text.strip()
            if text and len(text) > 50:  # Must have substantial content
                self._log(f"Found product description: {len(text)} chars")
                text_parts.append(text)
        except:
            self._log("No #productDescription found")
            pass
        
        # Priority 2: Feature bullets (often lists movies)
        try:
            bullets_container = self.driver.find_element(By.CSS_SELECTOR, '#feature-bullets')
            bullets = bullets_container.find_elements(By.CSS_SELECTOR, 'li span.a-list-item')
            for bullet in bullets:
                text = bullet.text.strip()
                if text and len(text) > 10:  # Filter out empty/short items
                    text_parts.append(text)
                    self._log(f"Found bullet: {text[:50]}")
        except:
            self._log("No feature bullets found")
            pass
        
        # Priority 3: From the manufacturer section
        try:
            manufacturer = self.driver.find_element(By.CSS_SELECTOR, '#aplus')
            text = manufacturer.text.strip()
            if text and len(text) > 100:
                self._log(f"Found manufacturer section: {len(text)} chars")
                text_parts.append(text)
        except:
            self._log("No manufacturer section found")
            pass
        
        return "\n".join(text_parts)
    
    def _extract_from_title(self, title: str) -> List[str]:
        """
        Extract movie titles from product title.
        Many collections format as "Collection (Movie1/ Movie2/ Movie3)"
        """
        movies = []
        
        # Look for movies separated by slashes in parentheses
        paren_match = re.search(r'\((.*?)\)', title)
        if paren_match:
            content = paren_match.group(1)
            # Split by / and clean up
            parts = content.split('/')
            for part in parts:
                part = part.strip()
                # Remove leading articles and clean
                if len(part) > 5 and not re.match(r'^\d', part):  # Not just a number
                    movies.append(part)
                    self._log(f"Extracted from title: {part}")
        
        return movies
    
    def _extract_movies_from_text(self, text: str) -> List[str]:
        """
        Extract movie titles from description text.
        
        This looks for common patterns:
        - "Movie Title (YEAR)" format (most reliable)
        - "Movie Title:" followed by description
        - Numbered lists (1. Movie, 2. Movie)
        - Titles in quotes
        """
        movies = []
        
        # Pattern 1: Title (Year) – Description format (most common in Hallmark descriptions)
        # Matches full lines like: "Christmas Under Wraps (2014) – A doctor finds..."
        # This captures titles with any characters including apostrophes
        bullet_pattern = r'^(.+?)\s*\((\d{4})\)\s*[–—\-]\s*[A-Z]'
        for line in text.split('\n'):
            match = re.search(bullet_pattern, line.strip())
            if match:
                title = match.group(1).strip()
                year = match.group(2)
                # Skip if it's likely a specification or header
                skip_terms = ['format', 'audio', 'video', 'edition', 'version', 'region', 'rating', 
                             'highlights', 'runtime', 'minutes', 'discs', 'approx']
                if not any(skip in title.lower() for skip in skip_terms):
                    if 5 <= len(title) <= 80:
                        movies.append(f"{title} ({year})")
                        self._log(f"Found movie (bullet format): {title} ({year})")
        
        # Pattern 2: Simple Title (Year) format - backup
        # Matches: "Snow Bride (2017)", "Christmas Land (2015)"
        year_pattern = r'([A-Z][A-Za-z\s\'-]{3,60}?)\s*\((\d{4})\)'
        year_matches = re.findall(year_pattern, text)
        for title, year in year_matches:
            title = title.strip()
            # Skip if already found or is a specification
            if any(f"{title} ({year})" == m or f"{title} ({year})" in m for m in movies):
                continue
            skip_terms = ['format', 'audio', 'video', 'edition', 'version', 'region', 'rating', 
                         'highlights', 'runtime', 'minutes', 'discs', 'approx']
            if not any(skip in title.lower() for skip in skip_terms):
                if 5 <= len(title) <= 60:
                    movies.append(f"{title} ({year})")
                    self._log(f"Found movie (year pattern): {title} ({year})")
        
        # Pattern 3: "Title:" format (common in product descriptions)
        # Matches: "A Christmas Detour:", "Where Are You, Christmas?:", "Checkin' It Twice:"
        # Split by periods or look for sentence patterns to find movie titles
        # Look for patterns like "Title: Description" where description starts with capital
        for line in text.split('.'):
            # Find title followed by colon and description
            match = re.search(r"([A-Z][A-Za-z\s,'?!-]{4,60}):\s*([A-Z][a-z])", line.strip())
            if match:
                title = match.group(1).strip().rstrip('?!')
                # Filter out generic headers
                skip_terms = ['product', 'featuring', 'starring', 'director', 'studio', 'format', 
                             'audio', 'runtime', 'playback', 'genre', 'sub-genre', 'actors', 
                             'country', 'rating', 'discs', 'media', 'key features', 'why',
                             'release date', 'language', 'number of', 'mpaa', 'origin']
                if not any(skip.lower() in title.lower() for skip in skip_terms):
                    if 5 <= len(title) <= 80 and title not in [m for m in movies if isinstance(m, str) and not '(' in m]:
                        movies.append(title)
                        self._log(f"Found movie (colon pattern): {title}")
        
        # Pattern 3: Numbered lists (1. Movie, 2. Movie)
        numbered = re.findall(r'\d+[.)]\s+([A-Z][A-Za-z\s\'-]+?)(?:\s*\(?\d{4}\)?)?(?:\n|\r|:|–|—|$)', text)
        for match in numbered:
            title = match.strip()
            if 5 <= len(title) <= 80:
                movies.append(title)
                self._log(f"Found movie (numbered): {title}")
        
        # Pattern 4: Titles in quotes
        quoted = re.findall(r'"([^"]+)"', text)
        for title in quoted:
            if 5 <= len(title) <= 80 and not title.lower().startswith('http'):
                movies.append(title)
                self._log(f"Found movie (quoted): {title}")
        
        # Clean up and deduplicate
        cleaned_movies = []
        seen = set()
        
        for movie in movies:
            # Clean the title
            movie = movie.strip()
            movie = re.sub(r'\s+', ' ', movie)
            
            # Remove trailing punctuation
            movie = movie.rstrip('.,;:')
            
            # Skip if too short
            if len(movie) < 5:
                continue
            
            # Skip generic/noise words and specifications
            noise_words = ['dvd', 'blu-ray', 'movies', 'collection', 'featuring', 'runtime', 
                          'audio', 'playback', 'region', 'genre', 'rating', 'actors', 'minutes',
                          'discs', 'format', 'highlights', 'features', 'product', 'country',
                          'media', 'approx', 'import', 'ntsc']
            if any(noise in movie.lower() for noise in noise_words):
                self._log(f"Filtered out noise: {movie}")
                continue
            
            # Normalize for deduplication: remove year and lowercase
            # This prevents "Movie (2019)" and "Movie" from both being added
            normalized = movie.lower()
            normalized = re.sub(r'\s*\(?\d{4}\)?\s*', '', normalized).strip()
            
            # Skip duplicates (comparing normalized versions)
            if normalized not in seen:
                seen.add(normalized)
                cleaned_movies.append(movie)
                self._log(f"Added to final list: {movie}")
            else:
                self._log(f"Skipping duplicate: {movie} (normalized: {normalized})")
        
        return cleaned_movies


def extract_all_movies(products: List[ProductInfo]) -> List[str]:
    """
    Extract all unique movies from multiple products.
    
    Args:
        products: List of ProductInfo objects
        
    Returns:
        Deduplicated list of movie titles
    """
    all_movies = []
    seen = set()
    
    for product in products:
        for movie in product.movies:
            movie_lower = movie.lower()
            if movie_lower not in seen:
                seen.add(movie_lower)
                all_movies.append(movie)
    
    return all_movies

