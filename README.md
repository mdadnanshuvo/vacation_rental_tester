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


