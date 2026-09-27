# 🛒 E-Commerce Product Scraper

A beginner-friendly Python command-line application that extracts product information from a publicly accessible e-commerce website and stores the collected data in a structured CSV file.

The project is configured to work with **Books to Scrape**, a free website created specifically for practicing web scraping.

## 📌 Project Overview

This project demonstrates how Python can be used to automatically collect product information from web pages.

The scraper extracts:

* Product Name
* Price
* Rating
* Availability
* Product URL

The collected information is cleaned and stored in `products.csv`.

## ✨ Features

* Scrapes product information using Python
* Extracts product name, price, rating, availability, and URL
* Supports multiple pages through pagination
* Removes duplicate products
* Handles missing information using `N/A`
* Saves data in CSV format
* Preserves previously collected data across multiple runs
* Uses request delays for responsible scraping
* Checks `robots.txt` before scraping
* Provides clear error messages
* Easy-to-modify CSS selectors
* Beginner-friendly command-line interface

## 🛠️ Technologies Used

| Technology         | Purpose                        |
| ------------------ | ------------------------------ |
| Python 3           | Main programming language      |
| Requests           | Sending HTTP requests          |
| BeautifulSoup4     | Parsing HTML pages             |
| Pandas             | Data cleaning and CSV handling |
| urllib.robotparser | Checking `robots.txt`          |
| time               | Adding delays between requests |

## 📂 Project Structure

```text
ecommerce-scraper/
│
├── scraper.py
├── requirements.txt
├── products.csv
└── README.md
```

### File Description

**`scraper.py`**
Contains the complete scraping logic.

**`requirements.txt`**
Contains the Python libraries required by the project.

**`products.csv`**
Stores the scraped product information.

**`README.md`**
Contains project documentation and instructions.

## ⚙️ Installation

### 1. Install Python

Download and install Python from:

https://www.python.org/downloads/

During installation, enable:

```text
Add Python to PATH
```

### 2. Open the Project in VS Code

Open the `ecommerce-scraper` folder in Visual Studio Code.

### 3. Create a Virtual Environment

Open the VS Code terminal and run:

```bash
python -m venv venv
```

Activate it on Windows:

```bash
venv\Scripts\activate
```

You should see:

```text
(venv)
```

at the beginning of your terminal.

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

## ▶️ How to Run

Run the following command:

```bash
python scraper.py
```

The program will ask for a product or category URL.

You can press **Enter** to use the default Books to Scrape website.

Example:

```text
========================================
      E-COMMERCE PRODUCT SCRAPER
========================================

Enter product/category URL:
(press Enter to use the demo site)

>

Maximum pages to scrape [default 5]: 3
```

The scraper will process the requested pages and save the results to:

```text
products.csv
```

## 📊 Example Output

The generated CSV file contains columns such as:

```text
Product Name,Price,Rating,Product URL,Availability
A Light in the Attic,£51.77,3,https://books.toscrape.com/...,In stock
Tipping the Velvet,£53.74,1,https://books.toscrape.com/...,In stock
Soumission,£50.10,1,https://books.toscrape.com/...,In stock
```

## 🔄 How the Scraper Works

The application follows these steps:

```text
User enters URL
       ↓
Check URL
       ↓
Check robots.txt
       ↓
Send HTTP Request
       ↓
Download HTML
       ↓
Parse HTML using BeautifulSoup
       ↓
Extract Product Details
       ↓
Clean and Remove Duplicates
       ↓
Merge With Existing CSV
       ↓
Save products.csv
```

### 1. Fetch the Web Page

The `requests` library sends an HTTP request to the target website.

### 2. Parse HTML

BeautifulSoup analyzes the downloaded HTML and identifies product elements using CSS selectors.

### 3. Extract Product Information

The scraper collects:

```text
Product Name
Price
Rating
Availability
Product URL
```

### 4. Clean the Data

Missing values are replaced with:

```text
N/A
```

Duplicate products are removed using the product URL.

### 5. Save the Data

Pandas is used to store the information and export it to:

```text
products.csv
```

Existing data can be preserved and updated when the same product is scraped again.

## 🧩 Customizing the Scraper

The scraper uses CSS selectors to identify product information.

For another website, inspect the HTML structure using your browser's Developer Tools and update the selectors in `scraper.py`.

Example:

```python
SELECTORS = {
    "product_card": "...",
    "name": "...",
    "price": "...",
    "rating": "...",
    "link": "...",
    "availability": "...",
    "next_page": "..."
}
```

The selectors must match the HTML structure of the target website.

## ⚠️ Error Handling

The application handles common problems such as:

* Invalid URLs
* Connection failures
* Request timeouts
* HTTP errors
* Missing product information
* Unexpected HTML structures
* Empty product pages
* CSV writing errors
* `robots.txt` restrictions

Instead of displaying a complicated Python traceback, the program provides a readable error message.

## 🔐 Responsible Web Scraping

This project is designed for educational purposes.

Before scraping any website:

* Scrape only publicly accessible information.
* Check the website's `robots.txt`.
* Review the website's Terms of Service.
* Do not bypass CAPTCHA or anti-bot systems.
* Do not bypass authentication or access controls.
* Use reasonable delays between requests.
* Avoid collecting personal or sensitive information.
* Limit the number of pages requested.
* Prefer an official API when one is available.

## 🚀 Future Improvements

Possible improvements include:

* Product image extraction
* JSON export
* Database storage using MySQL or MongoDB
* Automatic retry with exponential backoff
* Playwright/Selenium support for JavaScript websites
* Graphical user interface
* Automated unit testing
* Price tracking
* Scheduled scraping
* Email notifications when prices change

## 🎯 Learning Outcomes

By completing this project, you can learn:

* Python web scraping
* HTTP requests
* HTML parsing
* CSS selectors
* Data cleaning
* Pandas DataFrames
* CSV file handling
* Pagination
* Error handling
* Basic responsible scraping practices

## 📜 Disclaimer

This project is intended for educational purposes. Always verify that you are permitted to scrape a particular website before using this scraper against it. Respect the website's `robots.txt`, Terms of Service, rate limits, and applicable laws.

---

**Built with Python 🐍 for learning web scraping.**
