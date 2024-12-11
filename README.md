# Vacation Rental Tester

## Overview

The **Vacation Rental Tester** is a web scraping and testing tool designed to validate the presence and correctness of various elements on vacation rental websites. It uses Python with Selenium for browser automation, Pandas for data manipulation, and multithreading to improve the efficiency of crawling and testing.

## Project Structure

- **`drivers/`**: Contains WebDriver executables for various browsers like ChromeDriver and GeckoDriver.
- **`logs/`**: Directory to store log files generated during the test runs for debugging.
- **`src/`**: Contains the core source files that implement the test functionality.
- **`tests/`**: Includes individual Python test scripts such as `test_currency.py`, `test_h1.py`, etc., that test different aspects of the vacation rental websites.
- **`README.md`**: Documentation file with project details, installation, usage instructions, and more.

## Features

- **Web Scraping**: Uses Selenium to scrape vacation rental websites, such as `Alojamiento.io`, and checks the presence and content of specific HTML elements (e.g., H1 tags, currency formatting).
- **Multithreading**: Implements multithreading to run tests concurrently for more efficient crawling and testing.
- **Modular Design**: Code is organized into modules (e.g., `test_h1.py`, `test_currency.py`) to maintain clarity and scalability.
- **Logging**: Captures detailed logs of the scraping and testing process for debugging and result analysis.

## Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/mdadnanshuvo/vacation_rental_tester.git
   cd vacation_rental_tester


2. **Set up a virtual environment (optional but recommended):**
     
    
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows, use venv\Scripts\activate

3. **install dependencies:**
     
    
   ```bash
   pip install -r requirements.txt


### WebDriver Setup

WebDriver executables (ChromeDriver, GeckoDriver, etc.) must be placed in the `drivers/` folder. Ensure that the correct version of the driver is installed for your browser version.

1. Download the appropriate WebDriver for your browser:
   - [ChromeDriver](https://sites.google.com/a/chromium.org/chromedriver/)
   - [GeckoDriver (Firefox)](https://github.com/mozilla/geckodriver/releases)

2. Place the WebDriver executable inside the `drivers/` folder.

### Logs

Logs are stored in the `logs/` directory for debugging purposes. Each test run will create a new log file detailing the scraping and validation process.



## Usage

### Running Tests

To run the tests, simply execute the test scripts:

1. H1 tag existence test:

   ```bash
   
   python src/tests/test_h1.py

2. HTML tag sequence test:

   ```bash
   
   python src/tests/test_html_tags.py


3. Image alt attribute test:

   ```bash
   
   python src/tests/test_images.py


4. URL status code test:

   ```bash
   
   python src/tests/test_urls.py



5. currency filtering test:

   ```bash
   
   python src/tests/test_currency.py



6. Scrape data from Script

   ```bash
   
   python src/tests/test_scrape.py

  
