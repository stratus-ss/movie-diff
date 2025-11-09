"""GUI interface for Movie Diff application."""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, simpledialog
from pathlib import Path
import threading
from typing import Optional

from src.movie_parser import MovieCollectionParser
from src.amazon_product_scraper import AmazonProductScraper, AmazonMovie
from src.comparator import MovieComparator
from src.reporter import ReportGenerator


class MovieDiffGUI:
    """Graphical user interface for Movie Diff."""
    
    def __init__(self, default_owned_csv: str = "found_christmas_movies.csv"):
        """
        Initialize GUI.
        
        Args:
            default_owned_csv: Default path to owned movies CSV
        """
        self.default_owned_csv = default_owned_csv
        self.root = tk.Tk()
        self.root.title("Movie Diff - Amazon Product Comparison")
        self.root.geometry("900x700")
        
        self._setup_ui()
        self._center_window()
    
    def _center_window(self):
        """Center the window on screen."""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def _setup_ui(self):
        """Setup the user interface components."""
        # Title
        title_frame = ttk.Frame(self.root, padding="10")
        title_frame.pack(fill=tk.X)
        
        title_label = ttk.Label(
            title_frame,
            text="🎬 Movie Collection Comparison Tool",
            font=("Arial", 16, "bold")
        )
        title_label.pack()
        
        subtitle_label = ttk.Label(
            title_frame,
            text="Compare Amazon movie collections against your owned movies",
            font=("Arial", 10)
        )
        subtitle_label.pack()
        
        # Input section
        input_frame = ttk.LabelFrame(self.root, text="Input", padding="10")
        input_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Owned movies file
        owned_frame = ttk.Frame(input_frame)
        owned_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(owned_frame, text="Owned Movies CSV:", width=20).pack(side=tk.LEFT)
        self.owned_entry = ttk.Entry(owned_frame, width=50)
        self.owned_entry.insert(0, self.default_owned_csv)
        self.owned_entry.pack(side=tk.LEFT, padx=5)
        
        # Amazon URL
        url_frame = ttk.Frame(input_frame)
        url_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(url_frame, text="Amazon URL:", width=20).pack(side=tk.LEFT)
        self.url_entry = ttk.Entry(url_frame, width=50)
        self.url_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            url_frame,
            text="📋 Paste URL",
            command=self._paste_url
        ).pack(side=tk.LEFT, padx=2)
        
        # Action buttons
        button_frame = ttk.Frame(self.root, padding="10")
        button_frame.pack(fill=tk.X)
        
        self.compare_btn = ttk.Button(
            button_frame,
            text="🔍 Compare Movies",
            command=self._start_comparison,
            style="Accent.TButton"
        )
        self.compare_btn.pack(side=tk.LEFT, padx=5)
        
        self.clear_btn = ttk.Button(
            button_frame,
            text="🗑️ Clear Results",
            command=self._clear_results
        )
        self.clear_btn.pack(side=tk.LEFT, padx=5)
        
        # Progress bar
        self.progress = ttk.Progressbar(
            self.root,
            mode='indeterminate',
            length=300
        )
        self.progress.pack(pady=5)
        
        # Status label
        self.status_label = ttk.Label(
            self.root,
            text="Ready. Enter Amazon product URL to begin.",
            font=("Arial", 10)
        )
        self.status_label.pack(pady=5)
        
        # Results section
        results_frame = ttk.LabelFrame(
            self.root,
            text="Results",
            padding="10"
        )
        results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Scrolled text widget for results
        self.results_text = scrolledtext.ScrolledText(
            results_frame,
            wrap=tk.WORD,
            font=("Courier", 10),
            height=25,
            width=100
        )
        self.results_text.pack(fill=tk.BOTH, expand=True)
        
        # Configure text tags for formatting
        self.results_text.tag_configure("header", font=("Courier", 10, "bold"))
        self.results_text.tag_configure("owned", foreground="green")
        self.results_text.tag_configure("missing", foreground="red")
        self.results_text.tag_configure("uncertain", foreground="orange")
    
    def _paste_url(self):
        """Paste URL from clipboard."""
        try:
            clipboard_content = self.root.clipboard_get()
            self.url_entry.delete(0, tk.END)
            self.url_entry.insert(0, clipboard_content)
            self.status_label.config(text="URL pasted from clipboard")
        except tk.TclError:
            messagebox.showwarning("Paste Error", "Clipboard is empty or invalid")
    
    def _clear_results(self):
        """Clear the results text area."""
        self.results_text.delete(1.0, tk.END)
        self.status_label.config(text="Results cleared. Ready for new comparison.")
    
    def _update_status(self, message: str):
        """Update status label."""
        self.status_label.config(text=message)
        self.root.update_idletasks()
    
    def _show_results(self, summary: str):
        """Display results in the text widget."""
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(1.0, summary)
        
        # Scroll to top
        self.results_text.see(1.0)
    
    def _start_comparison(self):
        """Start the comparison process in a background thread."""
        url = self.url_entry.get().strip()
        owned_csv = self.owned_entry.get().strip()
        
        if not url:
            messagebox.showerror("Input Error", "Please enter an Amazon product URL")
            return
        
        if not Path(owned_csv).exists():
            messagebox.showerror(
                "File Error",
                f"Owned movies CSV not found: {owned_csv}"
            )
            return
        
        # Disable button and start progress
        self.compare_btn.config(state=tk.DISABLED)
        self.progress.start()
        self._update_status("Starting comparison...")
        
        # Run in background thread to keep UI responsive
        thread = threading.Thread(
            target=self._run_comparison,
            args=(url, owned_csv),
            daemon=True
        )
        thread.start()
    
    def _run_comparison(self, url: str, owned_csv: str):
        """
        Run the comparison process.
        
        Args:
            url: Amazon product URL
            owned_csv: Path to owned movies CSV
        """
        try:
            # Step 1: Load owned movies
            self._update_status("Loading owned movies...")
            parser = MovieCollectionParser(owned_csv)
            owned_movies = parser.load()
            
            # Step 2: Scrape Amazon page
            self._update_status(f"Scraping Amazon page (found {len(owned_movies)} owned movies)...")
            scraper = AmazonProductScraper(headless=True, verbose=False)
            
            try:
                product = scraper.scrape_product(url)
                
                if not product.movies:
                    self.root.after(0, lambda: messagebox.showwarning(
                        "No Movies Found",
                        "No movies were found on this Amazon page.\n\n"
                        "This could mean:\n"
                        "• The page structure has changed\n"
                        "• The product description doesn't list movies\n"
                        "• The URL is incorrect"
                    ))
                    return
                
                # Convert to AmazonMovie format
                amazon_movies = [
                    AmazonMovie(title=title, year=None, link=url)
                    for title in product.movies
                ]
                
            finally:
                scraper._close_driver()
            
            # Step 3: Compare
            self._update_status(f"Comparing {len(amazon_movies)} movies...")
            comparator = MovieComparator(owned_movies)
            results = comparator.compare_all(amazon_movies)
            statistics = comparator.get_statistics(results)
            
            # Step 4: Generate report
            self._update_status("Generating report...")
            reporter = ReportGenerator()
            summary = reporter.generate_text_summary(results, statistics)
            
            # Also save to file
            csv_path = reporter.generate_csv_report(results)
            txt_path = reporter.save_text_report(results, statistics)
            
            # Step 5: Display results
            self.root.after(0, lambda: self._show_results(summary))
            self.root.after(0, lambda: self._update_status(
                f"✅ Complete! Found {statistics['total']} movies: "
                f"{statistics['owned']} owned ({statistics['owned_pct']:.1f}%), "
                f"{statistics['missing']} missing ({statistics['missing_pct']:.1f}%), "
                f"{statistics['uncertain']} uncertain ({statistics['uncertain_pct']:.1f}%) | "
                f"Reports: {csv_path}"
            ))
            
        except FileNotFoundError as e:
            self.root.after(0, lambda: messagebox.showerror(
                "File Error",
                str(e)
            ))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror(
                "Error",
                f"An error occurred:\n\n{str(e)}"
            ))
        finally:
            # Re-enable button and stop progress
            self.root.after(0, self.progress.stop)
            self.root.after(0, lambda: self.compare_btn.config(state=tk.NORMAL))
    
    def run(self):
        """Run the GUI application."""
        # Show URL input dialog on startup
        self.root.after(100, self._prompt_for_url)
        self.root.mainloop()
    
    def _prompt_for_url(self):
        """Prompt user for Amazon URL on startup."""
        url = simpledialog.askstring(
            "Enter Amazon URL",
            "Please enter the Amazon product page URL:\n"
            "(You can also paste it in the main window)",
            parent=self.root
        )
        
        if url:
            self.url_entry.delete(0, tk.END)
            self.url_entry.insert(0, url)
            self.status_label.config(text="URL entered. Click 'Compare Movies' to start.")


def launch_gui(default_owned_csv: str = "found_christmas_movies.csv"):
    """
    Launch the GUI application.
    
    Args:
        default_owned_csv: Default path to owned movies CSV
    """
    app = MovieDiffGUI(default_owned_csv)
    app.run()

