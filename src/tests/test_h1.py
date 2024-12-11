import os
import sys
import pandas as pd
from urllib.parse import urlparse, urljoin
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from selenium.common.exceptions import TimeoutException

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

# Import TestReportGenerator from your existing file


class H1TagTester:
    def __init__(self, url='https://www.example.com', output_folder='test_results', headless=False, max_workers=10, max_depth=3, max_links=40):
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

        self.options.add_argument("--start-maximized")

        self.start_url = url
        self.start_domain = urlparse(url).netloc
        self.results = []
        self.visited_urls = set()
        self.to_visit = [(url, 0)]  # Store URLs along with their depth
        self.max_workers = max_workers  # This is set to 10 to ensure at least 10 pages are processed concurrently
        self.max_depth = max_depth
        self.max_links = max_links  # Max links to visit

    def _initialize_driver(self):
        return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=self.options)

    def _wait_for_page_load(self, driver):
        """Wait for the page to finish loading."""
        try:
            WebDriverWait(driver, 15).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
        except Exception as e:
            print(f"[WARNING] Page load timeout: {e}")

    def _handle_dynamic_content(self, driver):
        """Handle loading dynamic content by waiting for all visible links."""
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.XPATH, "//a[@href]"))
            )
        except Exception as e:
            print(f"[WARNING] Dynamic content loading timeout: {e}")

    def run_h1_tag_test(self, driver, url):
        """Test H1 tag existence and content for the given URL."""
        try:
            self._wait_for_page_load(driver)

            # Find H1 tags
            h1_tags = driver.find_elements(By.TAG_NAME, 'h1')

            # Test H1 tag existence
            passed = bool(h1_tags)
            comments = f"Found {len(h1_tags)} H1 tag(s) on {url}" if passed else "No H1 tags found"
            self.results.append((url, "H1 Tag Existence", "Pass" if passed else "Fail", comments))

            # Test number of H1 tags
            passed = len(h1_tags) <= 1
            comments = f"Total H1 tags: {len(h1_tags)} on {url}" if passed else f"Too many H1 tags: {len(h1_tags)}"
            self.results.append((url, "H1 Tag Count", "Pass" if passed else "Fail", comments))

            # Test H1 tag content
            if h1_tags:
                h1_text = h1_tags[0].text.strip()
                passed = bool(h1_text)
                comments = f"H1 Text: {h1_text} on {url}" if passed else "H1 Text is empty"
                self.results.append((url, "H1 Tag Content", "Pass" if passed else "Fail", comments))

        except Exception as e:
            print(f"[ERROR] URL: {url} - Error during H1 tag test: {e}")
            self.results.append((url, "H1 Tag Test", "Fail", str(e)))

    def process_page(self, url, depth):
        """Process each page and crawl its links."""
        if depth > self.max_depth or len(self.visited_urls) >= self.max_links:
            return

        driver = self._initialize_driver()
        retries = 2  # Number of retries for timeout errors
        try:
            for attempt in range(retries):
                try:
                    driver.get(url)
                    self._wait_for_page_load(driver)

                    # Capture final redirected URL
                    final_url = driver.current_url.rstrip('/')
                    final_url_parsed = urlparse(final_url)
                    if final_url in self.visited_urls or final_url_parsed.netloc != self.start_domain:
                        return

                    self.visited_urls.add(final_url)
                    print(f"Testing URL: {final_url} (Depth: {depth})")

                    # Run H1 tag test
                    self.run_h1_tag_test(driver, final_url)

                    # Extract and queue new links from the current page only within the same domain
                    links = driver.find_elements(By.XPATH, "//a[@href]")
                    for link in links:
                        href = link.get_attribute("href")
                        if href and not href.startswith(('javascript:', '#')):
                            resolved_url = urljoin(final_url, href).rstrip('/')
                            parsed_resolved_url = urlparse(resolved_url)
                            canonical_url = f"{parsed_resolved_url.scheme}://{parsed_resolved_url.netloc}{parsed_resolved_url.path}"
                            
                            # Only add links that belong to the same domain
                            if canonical_url not in self.visited_urls and parsed_resolved_url.netloc == self.start_domain:
                                self.to_visit.append((canonical_url, depth + 1))
                    break  # Exit the retry loop if page loads successfully
                except TimeoutException as e:
                    if attempt < retries - 1:
                        print(f"[WARNING] Timeout on {url}, retrying ({attempt + 1}/{retries})...")
                        time.sleep(1)  # Wait before retrying
                    else:
                        print(f"[ERROR] URL: {url} - Timeout after {retries} attempts.")
                        self.results.append((url, "Page Load", "Fail", str(e)))
                        return

        except Exception as e:
            print(f"Error testing URL {url}: {e}")
        finally:
            driver.quit()

    def run_recursive_tests(self):
        """Crawl pages recursively using multithreading."""
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            while self.to_visit and len(self.visited_urls) < self.max_links:
                futures = {executor.submit(self.process_page, url, depth): (url, depth) for url, depth in self.to_visit[:self.max_workers]}
                self.to_visit = self.to_visit[self.max_workers:]  # Remove the processed URLs from to_visit

                for future in as_completed(futures):
                    url, depth = futures[future]
                    try:
                        future.result()
                    except Exception as e:
                        print(f"Error processing {url}: {e}")

                # Stop if max_links is reached
                if len(self.visited_urls) >= self.max_links:
                    break

    def generate_report(self):
        """Generate a consolidated report in an Excel file."""
        print("Generating test report...")

        # Create a DataFrame from the results
        df = pd.DataFrame(self.results, columns=["URL", "Test Type", "Status", "Comments"])

        # Create the output file path
        report_file = os.path.join(self.output_folder, "h1_tag_test_report.xlsx")

        # Save the DataFrame to an Excel file
        try:
            with pd.ExcelWriter(report_file, engine='openpyxl') as writer:

                df.to_excel(writer, index=False, sheet_name='H1 Tag Test Results')
                print(f"Report saved successfully to {report_file}")
        except Exception as e:
            print(f"Error generating report: {e}")


if __name__ == "__main__":
    tester = H1TagTester(url="https://www.alojamiento.io/property/apartamentos-centro-col%c3%b3n/BC-189483/", headless=True, max_depth=3, max_links=50, max_workers=10)
    tester.run_recursive_tests()
    tester.generate_report()
