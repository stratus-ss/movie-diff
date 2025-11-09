# Movie Diff - Christmas Movie Collection Manager

Compare your owned Christmas movie collection against Amazon product pages to identify which movies you already own and which are new.

## Features

- 🎬 **GUI Mode** - Easy-to-use graphical interface with URL dialog
- 💻 **CLI Mode** - Command-line interface for automation
- 🔍 **Fuzzy Matching** - Intelligent title comparison with distinctive word matching
- 📊 **Report Generation** - CSV and text reports automatically saved
- 🎯 **Product Page Scraping** - Specialized Amazon product page parser
- ✨ **Default Settings** - Assumes `found_christmas_movies.csv` by default

## Quick Start

### GUI Mode (Recommended)

```bash
# Install dependencies
./setup-light.sh

# Install tkinter (required for GUI)
sudo pacman -S tk            # Arch Linux
# or
sudo apt install python3-tk  # Ubuntu/Debian
# or
sudo dnf install python3-tkinter  # Fedora/RHEL

# Launch GUI
python movie_diff.py --gui
```

The GUI will:
1. Prompt you for an Amazon product page URL
2. Use `found_christmas_movies.csv` by default
3. Display results in a scrollable window
4. Save reports automatically to `output/` directory

### CLI Mode

```bash
# Basic usage (uses found_christmas_movies.csv by default)
python movie_diff.py --amazon "https://www.amazon.com/.../dp/B0B8TLXLVX"

# With custom CSV file
python movie_diff.py --owned my_movies.csv --amazon "URL" --verbose

# Adjust matching threshold
python movie_diff.py --amazon "URL" --threshold 85
```

## Installation

```bash
# Clone repository
git clone <your-repo-url>
cd movie-diff

# Run setup script
./setup-light.sh

# For GUI mode, install tkinter
sudo pacman -S tk            # Arch Linux
# or
sudo apt install python3-tk  # Ubuntu/Debian
```

### Manual Installation

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements-light.txt

# For GUI: install tkinter (system package)
sudo pacman -S tk            # Arch Linux
# or
sudo apt install python3-tk  # Ubuntu/Debian
# or
sudo dnf install python3-tkinter  # Fedora/RHEL
```

## Requirements

### Core Dependencies (3 packages)
- `selenium` - Browser automation for Amazon scraping
- `rapidfuzz` - Fuzzy string matching for movie titles
- `webdriver-manager` - Automatic ChromeDriver management

### GUI Requirements (Optional)
- `tkinter` - GUI framework (system package, install via OS package manager)

## Usage

### GUI Mode

```bash
python movie_diff.py --gui
```

Features:
- URL input dialog on startup
- Paste URL from clipboard
- Real-time progress indicator
- Scrollable results window
- Automatic report saving
- Visual formatting (colors for owned/missing/uncertain)

### CLI Mode

```bash
# Basic comparison
python movie_diff.py --amazon "https://www.amazon.com/.../dp/..."

# Custom options
python movie_diff.py \
  --owned my_collection.csv \
  --amazon "URL" \
  --threshold 85 \
  --uncertain 60 \
  --output reports/ \
  --verbose
```

## Options

```
--gui                    Launch graphical user interface
--owned CSV_FILE         Path to owned movies CSV (default: found_christmas_movies.csv)
--amazon URL             Amazon product page URL
--threshold N            Match confidence threshold 0-100 (default: 80)
--uncertain N            Uncertain match threshold 0-100 (default: 60)
--output DIR             Output directory for reports (default: output)
--no-headless            Show browser when scraping (for debugging)
--verbose                Show detailed progress messages
```

## Output

The tool generates two report files in the `output/` directory:

1. **CSV Report** (`comparison_report_TIMESTAMP.csv`)
   - Detailed comparison data
   - Includes confidence scores
   - Matched file paths
   - Amazon links

2. **Text Summary** (`summary_report_TIMESTAMP.txt`)
   - Human-readable summary
   - Statistics (owned/missing/uncertain counts)
   - Source URL
   - Categorized movie lists

## Input File Format

Your owned movies CSV should have these columns:
```csv
filename,matching_keywords
"/path/to/Movie_Title.mkv","keyword1;keyword2"
```

## How It Works

1. **Load Collection** - Parses your owned movies CSV
2. **Scrape Amazon** - Extracts movie titles from product page
3. **Compare Titles** - Uses fuzzy matching with distinctive word algorithm
4. **Generate Reports** - Creates CSV and text summary reports
5. **Display Results** - Shows in GUI or console

## Why Selenium?

Amazon product pages are JavaScript-heavy and dynamically loaded. Simple HTTP requests (`requests` + `BeautifulSoup`) won't work because:
- Product descriptions load via AJAX
- Amazon detects and blocks bot scrapers
- Content is generated client-side after page load

Selenium launches a real Chrome browser to:
- Execute JavaScript and render dynamic content
- Bypass anti-bot detection measures
- Get the full page content as a human would see it

## Project Structure

```
movie-diff/
├── movie_diff.py              # Main entry point (CLI and GUI modes)
├── requirements-light.txt     # Python dependencies (3 packages)
├── setup-light.sh             # Setup script
├── src/
│   ├── __init__.py
│   ├── amazon_product_scraper.py  # Amazon page scraper
│   ├── comparator.py              # Comparison logic
│   ├── movie_parser.py            # CSV parser
│   ├── reporter.py                # Report generation
│   ├── utils.py                   # Title matching utilities
│   └── gui.py                     # GUI implementation
└── output/                    # Generated reports
```

## Troubleshooting

### GUI won't start
```bash
# Install tkinter (choose based on your OS)
sudo pacman -S tk                  # Arch Linux
sudo apt install python3-tk        # Ubuntu/Debian
sudo dnf install python3-tkinter   # Fedora/RHEL
sudo zypper install python3-tk     # openSUSE
```

Verify tkinter is installed:
```bash
python3 -c "import tkinter; print('✅ Tkinter installed')"
```

### ChromeDriver issues
The `webdriver-manager` package automatically downloads the correct ChromeDriver version. If you have issues:
```bash
# Make sure Chrome/Chromium is installed
which google-chrome
which chromium-browser
```

### No movies found
- Verify the URL is a product page (contains `/dp/` or `/gp/product/`)
- Try with `--no-headless` to see what the scraper sees
- Amazon may have changed their page structure

## License

MIT License - see LICENSE file

## Contributing

Contributions welcome! This is a focused tool for comparing movie collections against Amazon product pages.

## Credits

Built with:
- Selenium for browser automation
- RapidFuzz for fuzzy string matching
- Tkinter for GUI

