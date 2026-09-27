"""
========================================================================
 E-COMMERCE PRODUCT SCRAPER
========================================================================
 
A beginner-friendly, command-line web scraper that extracts product
information (name, price, rating, URL, availability) from a publicly
accessible e-commerce website and saves it into a CSV file.
 
DEMO SITE:
    This scraper is pre-configured to work with:
        https://books.toscrape.com
 
    This site is a free, public "sandbox" built specifically for people
    to practice web scraping on. It does not require a login, does not
    use CAPTCHAs or anti-bot protection, and explicitly welcomes
    scraping traffic. That makes it a safe, legal, and beginner-friendly
    target to learn with.
 
    If you want to point this scraper at a different site, read the
    "HOW TO ADAPT THIS SCRAPER" section in the README first, and make
    sure you are allowed to scrape that site (check its robots.txt and
    Terms of Service).
 
RESPONSIBLE SCRAPING:
    - Only scrape publicly accessible pages.
    - This script checks robots.txt before scraping and will refuse to
      continue if the target path is disallowed.
    - A delay is added between requests to avoid hammering the server.
    - A descriptive User-Agent is sent so the site owner can identify
      the traffic.
    - This script never attempts to bypass logins, CAPTCHAs, paywalls,
      or any other access control.
========================================================================
"""
 
import sys
import time
import urllib.parse
import urllib.robotparser
 
import pandas as pd
import requests
from bs4 import BeautifulSoup
 
# ------------------------------------------------------------------------
# CONFIGURATION
# ------------------------------------------------------------------------
 
# A descriptive User-Agent so the site owner can identify our traffic.
# Replace "your_email@example.com" with your own contact info if you
# adapt this for real use.
USER_AGENT = (
    "EcommerceProductScraper/1.0 "
    "(Educational project; contact: your_email@example.com)"
)
 
# Seconds to wait between page requests. Keep this reasonably high to
# avoid putting load on the target server.
REQUEST_DELAY = 2
 
# How many seconds to wait for a server response before giving up.
REQUEST_TIMEOUT = 10
 
# Safety limit on how many pages we will ever scrape in one run,
# regardless of what the user enters.
HARD_MAX_PAGES = 20
 
# Default number of pages to scrape if the user doesn't override it.
MAX_PAGES = 5
 
# ------------------------------------------------------------------------
# CSS SELECTORS
# ------------------------------------------------------------------------
# These selectors are written for https://books.toscrape.com.
# Every real e-commerce site uses different HTML/CSS, so if you point
# this scraper at another site, this is the ONLY section you should
# need to change. Open the target page in your browser, right-click a
# product, choose "Inspect", and update the selectors below to match.
#
# Each selector is written as a CSS selector string used with
# BeautifulSoup's `.select()` / `.select_one()` methods.
SELECTORS = {
    # Selector for a single product "card" on the listing page.
    # We loop over every match of this selector.
    "product_card": "article.product_pod",
 
    # Inside each product card:
    "name": "h3 a",              # product name is in the title/text of this link
    "price": "p.price_color",    # product price text
    "rating": "p.star-rating",   # rating is stored as a CSS *class*, e.g. "star-rating Three"
    "link": "h3 a",              # href of this tag is the product URL (relative)
    "availability": "p.instock.availability",  # stock status text
 
    # Selector for the "next page" link, used for pagination.
    "next_page": "li.next a",
}
 
# Words -> numeric rating, used because books.toscrape.com encodes the
# star rating as a word in a CSS class (e.g. class="star-rating Three").
RATING_WORDS = {
    "one": "1",
    "two": "2",
    "three": "3",
    "four": "4",
    "five": "5",
}
 
# Value used whenever a field cannot be found on the page.
MISSING_VALUE = "N/A"
 
 
# ------------------------------------------------------------------------
# ROBOTS.TXT CHECK
# ------------------------------------------------------------------------
def is_allowed_by_robots(url: str, user_agent: str) -> bool:
    """
    Check the target site's robots.txt to see if we are allowed to
    fetch this specific URL. Returns True if scraping is allowed (or if
    robots.txt could not be read, in which case we proceed cautiously),
    and False if it's explicitly disallowed.
    """
    parsed = urllib.parse.urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
 
    parser = urllib.robotparser.RobotFileParser()
    parser.set_url(robots_url)
 
    try:
        parser.read()
    except Exception:
        # If robots.txt can't be read, we can't be sure either way.
        # We choose to proceed, since many small/demo sites have no
        # robots.txt at all. For production use, you may want to be
        # more conservative and refuse instead.
        print(f"Note: could not read {robots_url}; proceeding cautiously.")
        return True
 
    return parser.can_fetch(user_agent, url)
 
 
# ------------------------------------------------------------------------
# STEP 1: FETCH A PAGE
# ------------------------------------------------------------------------
def fetch_page(url: str) -> str:
    """
    Send an HTTP GET request to the given URL and return the raw HTML
    as text. Raises a RuntimeError with a clear, user-friendly message
    if anything goes wrong.
    """
    headers = {"User-Agent": USER_AGENT}
 
    try:
        response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()  # raises HTTPError for 4xx/5xx status codes
    except requests.exceptions.Timeout:
        raise RuntimeError(f"The request to {url} timed out. Please try again later.")
    except requests.exceptions.ConnectionError:
        raise RuntimeError(
            f"Could not connect to {url}. Check the URL and your internet connection."
        )
    except requests.exceptions.HTTPError as e:
        raise RuntimeError(f"The website returned an error for {url}: {e}")
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"An unexpected network error occurred: {e}")
 
    return response.text
 
 
# ------------------------------------------------------------------------
# STEP 2: EXTRACT PRODUCTS FROM A PAGE
# ------------------------------------------------------------------------
def _parse_rating(rating_tag) -> str:
    """
    Turn something like <p class="star-rating Three"> into "3".
    Returns "N/A" if no recognizable rating word is found.
    """
    if rating_tag is None:
        return MISSING_VALUE
 
    classes = rating_tag.get("class", [])
    for class_name in classes:
        word = class_name.strip().lower()
        if word in RATING_WORDS:
            return RATING_WORDS[word]
 
    return MISSING_VALUE
 
 
def extract_products(html: str, base_url: str) -> list:
    """
    Parse the given HTML and return a list of dictionaries, one per
    product found, using the selectors defined in SELECTORS.
 
    Each dictionary has the keys:
        "Product Name", "Price", "Rating", "Product URL", "Availability"
 
    Missing individual fields are filled in with MISSING_VALUE ("N/A")
    rather than crashing the whole scrape.
    """
    soup = BeautifulSoup(html, "html.parser")
    product_cards = soup.select(SELECTORS["product_card"])
 
    if not product_cards:
        # This usually means either the page has no products, or the
        # site's HTML structure doesn't match our selectors anymore.
        raise ValueError(
            "No products were found on this page. The site's HTML "
            "structure may differ from what this scraper expects. "
            "Check the SELECTORS dictionary at the top of scraper.py."
        )
 
    products = []
 
    for card in product_cards:
        # --- Product name ---
        name_tag = card.select_one(SELECTORS["name"])
        if name_tag is not None:
            # books.toscrape.com stores the full title in the "title"
            # attribute (since the visible text is often truncated).
            name = name_tag.get("title") or name_tag.get_text(strip=True)
        else:
            name = MISSING_VALUE
 
        # --- Price ---
        price_tag = card.select_one(SELECTORS["price"])
        price = price_tag.get_text(strip=True) if price_tag else MISSING_VALUE
 
        # --- Rating ---
        rating_tag = card.select_one(SELECTORS["rating"])
        rating = _parse_rating(rating_tag)
 
        # --- Product URL ---
        link_tag = card.select_one(SELECTORS["link"])
        if link_tag is not None and link_tag.get("href"):
            product_url = urllib.parse.urljoin(base_url, link_tag["href"])
        else:
            product_url = MISSING_VALUE
 
        # --- Availability ---
        availability_tag = card.select_one(SELECTORS["availability"])
        availability = (
            availability_tag.get_text(strip=True) if availability_tag else MISSING_VALUE
        )
 
        products.append(
            {
                "Product Name": name if name else MISSING_VALUE,
                "Price": price if price else MISSING_VALUE,
                "Rating": rating,
                "Product URL": product_url,
                "Availability": availability if availability else MISSING_VALUE,
            }
        )
 
    return products
 
 
def get_next_page_url(html: str, current_url: str):
    """
    Look for a "next page" link on the current page. Returns the full
    (absolute) URL of the next page, or None if there isn't one.
    """
    soup = BeautifulSoup(html, "html.parser")
    next_tag = soup.select_one(SELECTORS["next_page"])
 
    if next_tag is None or not next_tag.get("href"):
        return None
 
    return urllib.parse.urljoin(current_url, next_tag["href"])
 
 
# ------------------------------------------------------------------------
# STEP 3: CLEAN THE DATA
# ------------------------------------------------------------------------
def clean_data(products: list) -> pd.DataFrame:
    """
    Convert the list of product dictionaries into a pandas DataFrame,
    remove exact duplicate rows, and make sure missing values are
    consistently represented as "N/A".
    """
    df = pd.DataFrame(products)
 
    if df.empty:
        return df
 
    # Make sure every expected column exists, even if some products
    # were missing certain fields entirely.
    expected_columns = ["Product Name", "Price", "Rating", "Product URL", "Availability"]
    for col in expected_columns:
        if col not in df.columns:
            df[col] = MISSING_VALUE
 
    # Replace any empty strings / actual NaN values with "N/A".
    df = df.fillna(MISSING_VALUE)
    df = df.replace(r"^\s*$", MISSING_VALUE, regex=True)
 
    # Remove duplicate products. We consider a product a duplicate if
    # its Product URL matches an earlier one (URLs are unique per
    # product); fall back to full-row duplicates if URLs are missing.
    before = len(df)
    if "Product URL" in df.columns:
        df = df.drop_duplicates(subset=["Product URL"], keep="first")
    df = df.drop_duplicates(keep="first")
    removed = before - len(df)
    if removed > 0:
        print(f"Removed {removed} duplicate product(s).")
 
    return df.reset_index(drop=True)
 
 
# ------------------------------------------------------------------------
# STEP 4: SAVE TO CSV (merging with any existing records)
# ------------------------------------------------------------------------
def load_existing_data(filename: str = "products.csv") -> pd.DataFrame:
    """
    Load previously saved products from filename, if it exists, so that
    each run can be merged with earlier runs instead of wiping them out.
    Returns an empty DataFrame if the file doesn't exist yet or can't be
    read (e.g. it's empty, corrupted, or in a different format).
    """
    import os
 
    if not os.path.exists(filename):
        return pd.DataFrame()
 
    try:
        existing_df = pd.read_csv(filename, encoding="utf-8-sig")
        return existing_df
    except (pd.errors.EmptyDataError, pd.errors.ParserError):
        print(f"Note: '{filename}' exists but couldn't be read as CSV; starting fresh.")
        return pd.DataFrame()
    except OSError:
        return pd.DataFrame()
 
 
def save_to_csv(df: pd.DataFrame, filename: str = "products.csv") -> None:
    """
    Save the DataFrame to a CSV file, MERGING it with whatever is
    already in that file (rather than overwriting it), so records from
    previous runs are kept. Duplicate products (matched by Product URL)
    are removed, keeping the newest version of each.
 
    Raises a RuntimeError with a clear message if writing the file
    fails (e.g. permissions issue), and a ValueError if there is
    nothing at all to save.
    """
    if df.empty:
        raise ValueError("There is no data to save. The DataFrame is empty.")
 
    existing_df = load_existing_data(filename)
 
    if not existing_df.empty:
        before = len(existing_df) + len(df)
        # Put new data first with keep="first" so newly scraped info
        # (e.g. an updated price) wins over old rows for the same URL.
        combined_df = pd.concat([df, existing_df], ignore_index=True)
        if "Product URL" in combined_df.columns:
            combined_df = combined_df.drop_duplicates(subset=["Product URL"], keep="first")
        combined_df = combined_df.drop_duplicates(keep="first").reset_index(drop=True)
        added = len(combined_df) - len(existing_df)
        print(f"Merged with {len(existing_df)} existing record(s) already in '{filename}'.")
        print(f"Added {max(added, 0)} new product(s); {len(combined_df)} total after merging.")
        df = combined_df
 
    try:
        df.to_csv(filename, index=False, encoding="utf-8-sig")
    except PermissionError:
        raise RuntimeError(
            f"Could not write to '{filename}'. Is the file open in another "
            "program (like Excel)? Close it and try again."
        )
    except OSError as e:
        raise RuntimeError(f"Could not write to '{filename}': {e}")
 
    return df
 
 
# ------------------------------------------------------------------------
# INPUT VALIDATION HELPERS
# ------------------------------------------------------------------------
def is_valid_url(url: str) -> bool:
    """Basic sanity check that the URL has a scheme and a domain."""
    try:
        parsed = urllib.parse.urlparse(url)
        return bool(parsed.scheme in ("http", "https") and parsed.netloc)
    except Exception:
        return False
 
 
def ask_for_url() -> str:
    """Prompt the user for a URL and keep asking until it's valid."""
    default_url = "https://books.toscrape.com/catalogue/category/books_1/index.html"
 
    print("Enter product/category URL:")
    print(f"(press Enter to use the demo site: {default_url})")
    url = input("> ").strip()
 
    if not url:
        return default_url
 
    while not is_valid_url(url):
        print("That doesn't look like a valid URL. It should start with http:// or https://")
        url = input("> ").strip()
 
    return url
 
 
def ask_for_max_pages() -> int:
    """Prompt the user for how many pages to scrape, with a safe default and cap."""
    raw = input(f"Maximum pages to scrape [default {MAX_PAGES}]: ").strip()
 
    if not raw:
        return MAX_PAGES
 
    try:
        value = int(raw)
    except ValueError:
        print(f"Not a number, using default of {MAX_PAGES}.")
        return MAX_PAGES
 
    if value < 1:
        print("Must be at least 1. Using 1.")
        return 1
 
    if value > HARD_MAX_PAGES:
        print(f"That's a lot of pages! Capping at {HARD_MAX_PAGES} to be respectful of the server.")
        return HARD_MAX_PAGES
 
    return value
 
 
# ------------------------------------------------------------------------
# MAIN PROGRAM
# ------------------------------------------------------------------------
def main():
    print("=" * 40)
    print("      E-COMMERCE PRODUCT SCRAPER")
    print("=" * 40)
    print()
 
    start_url = ask_for_url()
    max_pages = ask_for_max_pages()
    print()
 
    # --- Respect robots.txt before we do anything else ---
    if not is_allowed_by_robots(start_url, USER_AGENT):
        print(
            "This site's robots.txt disallows scraping this page with our "
            "User-Agent. Stopping, out of respect for the site's rules."
        )
        sys.exit(1)
 
    all_products = []
    current_url = start_url
    page_number = 1
 
    while current_url and page_number <= max_pages:
        print(f"Scraping page {page_number}...")
 
        try:
            html = fetch_page(current_url)
        except RuntimeError as e:
            print(f"Error: {e}")
            break
 
        try:
            page_products = extract_products(html, current_url)
        except ValueError as e:
            print(f"Error: {e}")
            break
 
        all_products.extend(page_products)
        print(f"Found {len(page_products)} products.")
 
        current_url = get_next_page_url(html, current_url)
        page_number += 1
 
        # Be polite: wait before making the next request (but not after
        # the very last page, since there's no point waiting then).
        if current_url and page_number <= max_pages:
            time.sleep(REQUEST_DELAY)
 
    print()
 
    if not all_products:
        print("No products were extracted. Nothing to save.")
        sys.exit(1)
 
    df = clean_data(all_products)
    print(f"Total products extracted this run: {len(df)}")
    print()
 
    try:
        final_df = save_to_csv(df, "products.csv")
    except (RuntimeError, ValueError) as e:
        print(f"Error saving CSV: {e}")
        sys.exit(1)
 
    print()
    print(f"Total products now stored in products.csv: {len(final_df)}")
    print("Data saved successfully to:")
    print("products.csv")
 
 
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nScraping cancelled by user.")
        sys.exit(1)