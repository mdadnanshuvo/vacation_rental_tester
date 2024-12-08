import os
import pandas as pd
from urllib.parse import urlparse, urljoin
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

class VacationRentalTester:
    def __init__(self, url='https://www.example.com', output_folder='test_results', headless=False):
        self.output_folder = output_folder
        os.makedirs(self.output_folder, exist_ok=True)

        # Setup Chrome options
        self.options = webdriver.ChromeOptions()
        if headless:
            self.options.add_argument("--headless")
            self.options.add_argument("--disable-gpu")
            self.options.add_argument("--window-size=1920,1080")
            self.options.add_argument("--disable-dev-shm-usage")
            self.options.add_argument("--no-sandbox")
            self.options.add_argument("--disable-blink-features=AutomationControlled")
            self.options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

        self.options.add_argument("--start-maximized")

        # Initialize WebDriver
        self.driver = None
        self.start_url = url
        self.results = []
        self.visited_urls = set()
        self.to_visit = [url]
        self.script_data = []

    def _initialize_driver(self):
        if not self.driver:
            self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=self.options)

    def _wait_for_page_load(self):
        """Wait for the page to finish loading."""
        try:
            WebDriverWait(self.driver, 15).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
        except Exception as e:
            print(f"[WARNING] Page load timeout: {e}")

    def _extract_links(self, current_url):
        """Extract all valid links from the current page."""
        try:
            self._wait_for_page_load()
            links = self.driver.find_elements(By.XPATH, "//a[@href]")
            valid_links = []
            for link in links:
                href = link.get_attribute("href")
                if href and not href.startswith(('javascript:', '#')):
                    resolved_url = urljoin(current_url, href)
                    if urlparse(resolved_url).netloc == urlparse(self.start_url).netloc:
                        valid_links.append(resolved_url)
            return valid_links
        except Exception as e:
            print(f"Error extracting links from {current_url}: {e}")
            return []

    def _extract_script_data(self, url):
        """Extract specific data from script tags."""
        try:
            self._wait_for_page_load()
            script_tags = self.driver.find_elements(By.TAG_NAME, "script")
            for script in script_tags:
                content = script.get_attribute("innerHTML")
                if content:
                    self._parse_script_data(content, url)
        except Exception as e:
            print(f"Error extracting script data from {url}: {e}")

    def _parse_script_data(self, content, url):
        """Parse script content to extract required fields."""
        data = {
            "SiteURL": url,
            "CampaignID": "Extracted CampaignID",  # Replace with actual parsing logic
            "SiteName": "Extracted SiteName",      # Replace with actual parsing logic
            "Browser": "Extracted Browser",        # Replace with actual parsing logic
            "CountryCode": "Extracted CountryCode",# Replace with actual parsing logic
            "IP": "Extracted IP"                   # Replace with actual parsing logic
        }
        self.script_data.append(data)

    def run_recursive_tests(self):
        """Crawl pages recursively and perform tests."""
        self._initialize_driver()

        while self.to_visit:
            current_url = self.to_visit.pop()
            if current_url in self.visited_urls:
                continue

            self.visited_urls.add(current_url)
            try:
                self.driver.get(current_url)
                self._wait_for_page_load()
                print(f"Testing URL: {current_url}")

                # Run header sequence test
                self.run_header_sequence_test(current_url)

                # Extract and queue new links
                new_links = self._extract_links(current_url)
                for link in new_links:
                    if link not in self.visited_urls and link not in self.to_visit:
                        self.to_visit.append(link)

                # Extract script data
                self._extract_script_data(current_url)

            except Exception as e:
                print(f"Error testing URL {current_url}: {e}")

    def run_header_sequence_test(self, url):
        """Check the sequence of HTML header tags for the given URL."""
        try:
            headers = self.driver.find_elements(By.XPATH, '//h1 | //h2 | //h3 | //h4 | //h5 | //h6')
            header_order = {f'h{i}': i for i in range(1, 7)}
            extracted_order = []

            # Extract the order of header tags
            for header in headers:
                tag_name = header.tag_name.lower()
                if tag_name in header_order:
                    extracted_order.append(header_order[tag_name])

            # Validate the header sequence
            is_valid = True
            for i in range(1, len(extracted_order)):
                if extracted_order[i] > extracted_order[i - 1] + 1:
                    is_valid = False
                    print(f"[ERROR] URL: {url} - Header sequence broken. Found h{extracted_order[i]} skipping h{extracted_order[i - 1] + 1}.")
                    self.results.append((url, "Header Sequence", "Invalid", f"Broken sequence: h{extracted_order[i]} after h{extracted_order[i - 1]}"))
                    break

            if is_valid:
                print(f"[SUCCESS] URL: {url} - Header sequence is valid.")
                self.results.append((url, "Header Sequence", "Valid", "All headers are in correct order."))

        except Exception as e:
            print(f"[ERROR] URL: {url} - Error during header sequence test: {e}")
            self.results.append((url, "Header Sequence", "Error", str(e)))

    def generate_report(self):
        """Generate an Excel report of the results."""
        print("Generating test report...")
        header_df = pd.DataFrame(self.results, columns=["URL", "Test", "Result", "Comments"])
        script_df = pd.DataFrame(self.script_data)
        report_file = os.path.join(self.output_folder, "test_report.xlsx")

        with pd.ExcelWriter(report_file, engine='openpyxl') as writer:
            header_df.to_excel(writer, index=False, sheet_name="Header Sequence")
            script_df.to_excel(writer, index=False, sheet_name="Script Data")

        print(f"Report saved to {report_file}")

    def cleanup(self):
        """Close the WebDriver."""
        if self.driver:
            self.driver.quit()

if __name__ == "__main__":
    tester = VacationRentalTester(url="https://www.alojamiento.io/property/apartamentos-centro-col%c3%b3n/BC-189483/", headless=True)
    try:
        tester.run_recursive_tests()
        tester.generate_report()
    finally:
        tester.cleanup()

