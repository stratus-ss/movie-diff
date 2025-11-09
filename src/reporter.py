"""Report generation for comparison results."""

import csv
from pathlib import Path
from typing import List
from datetime import datetime

from src.comparator import ComparisonResult, MatchStatus


class ReportGenerator:
    """Generates reports from comparison results."""
    
    def __init__(self, output_dir: str = "output"):
        """
        Initialize reporter.
        
        Args:
            output_dir: Directory for output files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def generate_csv_report(
        self,
        results: List[ComparisonResult],
        filename: str = None
    ) -> str:
        """
        Generate CSV report.
        
        Args:
            results: List of comparison results
            filename: Output filename (auto-generated if None)
            
        Returns:
            Path to generated CSV file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"comparison_report_{timestamp}.csv"
        
        output_path = self.output_dir / filename
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Write header
            writer.writerow([
                'Title',
                'Year',
                'Status',
                'Confidence',
                'Matched File',
                'Amazon Link'
            ])
            
            # Write data
            for result in results:
                matched_file = ""
                if result.matched_movie:
                    matched_file = result.matched_movie.filepath
                
                writer.writerow([
                    result.title,
                    result.year or '',
                    result.status.value,
                    f"{result.confidence:.1f}",
                    matched_file,
                    result.link
                ])
        
        return str(output_path)
    
    def generate_text_summary(
        self,
        results: List[ComparisonResult],
        statistics: dict
    ) -> str:
        """
        Generate text summary of results.
        
        Args:
            results: List of comparison results
            statistics: Statistics dictionary
            
        Returns:
            Formatted text summary
        """
        lines = []
        lines.append("=" * 70)
        lines.append("MOVIE COMPARISON REPORT")
        lines.append("=" * 70)
        lines.append("")
        
        # Summary statistics
        lines.append("SUMMARY")
        lines.append("-" * 70)
        
        # Add source URL (get from first result since they're all from same source)
        if results:
            source_url = results[0].link
            lines.append(f"Source URL:               {source_url}")
        
        lines.append(f"Total movies in list:     {statistics['total']}")
        lines.append(f"Already owned:            {statistics['owned']} ({statistics['owned_pct']:.1f}%)")
        lines.append(f"Missing from collection:  {statistics['missing']} ({statistics['missing_pct']:.1f}%)")
        lines.append(f"Uncertain matches:        {statistics['uncertain']} ({statistics['uncertain_pct']:.1f}%)")
        lines.append("")
        
        # Movies already owned
        owned = [r for r in results if r.status == MatchStatus.OWNED]
        if owned:
            lines.append("ALREADY OWNED")
            lines.append("-" * 70)
            for result in owned:
                lines.append(f"✓ {result.title} (confidence: {result.confidence:.1f})")
                if result.matched_movie:
                    lines.append(f"  → {result.matched_movie.filename}")
            lines.append("")
        
        # Movies to purchase
        missing = [r for r in results if r.status == MatchStatus.MISSING]
        if missing:
            lines.append("MISSING FROM COLLECTION")
            lines.append("-" * 70)
            for result in missing:
                year_str = f" ({result.year})" if result.year else ""
                lines.append(f"✗ {result.title}{year_str}")
            lines.append("")
        
        # Uncertain matches
        uncertain = [r for r in results if r.status == MatchStatus.UNCERTAIN]
        if uncertain:
            lines.append("UNCERTAIN MATCHES (Manual Review Needed)")
            lines.append("-" * 70)
            for result in uncertain:
                lines.append(f"? {result.title} (confidence: {result.confidence:.1f})")
                if result.matched_movie:
                    lines.append(f"  → Possible match: {result.matched_movie.filename}")
            lines.append("")
        
        lines.append("=" * 70)
        
        return "\n".join(lines)
    
    def save_text_report(
        self,
        results: List[ComparisonResult],
        statistics: dict,
        filename: str = None
    ) -> str:
        """
        Save text report to file.
        
        Args:
            results: List of comparison results
            statistics: Statistics dictionary
            filename: Output filename (auto-generated if None)
            
        Returns:
            Path to saved report
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"summary_report_{timestamp}.txt"
        
        output_path = self.output_dir / filename
        summary = self.generate_text_summary(results, statistics)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(summary)
        
        return str(output_path)

