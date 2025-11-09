#!/usr/bin/env python3
"""
Movie Diff - Christmas Movie Collection Manager

Main entry point for comparing owned movies against Amazon lists.
Supports both GUI and CLI modes.
"""

import argparse
import sys
from pathlib import Path

from src.movie_parser import MovieCollectionParser
from src.amazon_product_scraper import AmazonProductScraper
from src.comparator import MovieComparator
from src.reporter import ReportGenerator


class MovieDiffCLI:
    """Command-line interface for Movie Diff."""
    
    def __init__(self):
        """Initialize CLI."""
        self.parser = self._create_parser()
    
    def _create_parser(self) -> argparse.ArgumentParser:
        """Create argument parser."""
        parser = argparse.ArgumentParser(
            description='Compare owned Christmas movies against Amazon lists',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Launch GUI mode (interactive)
  python movie_diff.py --gui
  
  # CLI mode with Amazon product page
  python movie_diff.py --amazon "https://amazon.com/.../dp/..."
  
  # CLI with custom CSV file
  python movie_diff.py --owned my_movies.csv --amazon "URL" --verbose
  
  # Adjust matching threshold
  python movie_diff.py --amazon "URL" --threshold 85 --verbose
            """
        )
        
        # Mode selection
        parser.add_argument(
            '--gui',
            action='store_true',
            help='Launch graphical user interface (requires tkinter)'
        )
        
        # Required arguments (not required in GUI mode)
        parser.add_argument(
            '--owned',
            default='found_christmas_movies.csv',
            help='Path to CSV file with owned movies (default: found_christmas_movies.csv)'
        )
        
        # Source argument
        parser.add_argument(
            '--amazon',
            help='Amazon product page URL to scrape (e.g., /dp/... URLs)'
        )
        
        # Optional arguments
        parser.add_argument(
            '--threshold',
            type=int,
            default=80,
            help='Match confidence threshold (0-100, default: 80)'
        )
        parser.add_argument(
            '--uncertain',
            type=int,
            default=60,
            help='Uncertain match threshold (0-100, default: 60)'
        )
        parser.add_argument(
            '--output',
            default='output',
            help='Output directory for reports (default: output)'
        )
        parser.add_argument(
            '--no-headless',
            action='store_true',
            help='Show browser when scraping (for debugging)'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show progress messages and detailed output'
        )
        
        return parser
    
    def run(self, args=None):
        """
        Run the application (GUI or CLI mode).
        
        Args:
            args: Command-line arguments (uses sys.argv if None)
        """
        args = self.parser.parse_args(args)
        
        # GUI mode
        if args.gui:
            try:
                from src.gui import launch_gui
                launch_gui(default_owned_csv=args.owned)
                return 0
            except ImportError as e:
                print("❌ Error: GUI mode requires tkinter", file=sys.stderr)
                print("Install tkinter with: sudo apt install python3-tk", file=sys.stderr)
                return 1
            except Exception as e:
                print(f"❌ GUI Error: {e}", file=sys.stderr)
                return 1
        
        # CLI mode - require amazon URL
        if not args.amazon:
            print("❌ Error: --amazon URL is required in CLI mode", file=sys.stderr)
            print("Use --gui for graphical interface, or provide --amazon URL", file=sys.stderr)
            self.parser.print_help()
            return 1
        
        try:
            verbose = args.verbose
            
            # Step 1: Load owned movies
            if verbose:
                print(f"📂 Loading owned movies from: {args.owned}")
            parser = MovieCollectionParser(args.owned)
            owned_movies = parser.load()
            if verbose:
                print(f"✓ Loaded {len(owned_movies)} owned movies")
                print()
            
            # Step 2: Scrape Amazon product page
            if verbose:
                print(f"🌐 Scraping Amazon product page: {args.amazon}")
                print("⏳ This may take a minute...")
            
            scraper = AmazonProductScraper(headless=not args.no_headless, verbose=verbose)
            try:
                product = scraper.scrape_product(args.amazon)
                if verbose:
                    print(f"✓ Product: {product.title}")
                    print(f"✓ Found {len(product.movies)} movies in product description")
                
                # Convert to AmazonMovie format for comparison
                from src.amazon_product_scraper import AmazonMovie
                amazon_movies = [
                    AmazonMovie(title=title, year=None, link=args.amazon)
                    for title in product.movies
                ]
            finally:
                scraper._close_driver()
            
            if not amazon_movies:
                print("❌ Error: No movies found in source")
                return 1
            
            if verbose:
                print()
            
            # Step 3: Compare movies
            if verbose:
                print("🔍 Comparing movies...")
            comparator = MovieComparator(
                owned_movies,
                match_threshold=args.threshold,
                uncertain_threshold=args.uncertain
            )
            results = comparator.compare_all(amazon_movies)
            statistics = comparator.get_statistics(results)
            if verbose:
                print("✓ Comparison complete")
                print()
            
            # Step 4: Generate reports
            if verbose:
                print("📊 Generating reports...")
            reporter = ReportGenerator(output_dir=args.output)
            
            csv_path = reporter.generate_csv_report(results)
            if verbose:
                print(f"✓ CSV report: {csv_path}")
            
            txt_path = reporter.save_text_report(results, statistics)
            if verbose:
                print(f"✓ Summary report: {txt_path}")
                print()
            
            # Step 5: Display summary
            summary = reporter.generate_text_summary(results, statistics)
            print(summary)
            
            return 0
            
        except FileNotFoundError as e:
            print(f"❌ Error: {e}", file=sys.stderr)
            return 1
        except Exception as e:
            print(f"❌ Unexpected error: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            return 1


def main():
    """Main entry point."""
    cli = MovieDiffCLI()
    sys.exit(cli.run())


if __name__ == '__main__':
    main()

