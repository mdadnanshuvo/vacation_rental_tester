import os
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

class VacationRentalTester:
    def __init__(self, url='https://www.example.com', output_folder='test_results', headless=False, max_workers=10, max_depth=3, max_links=400):
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

    def run_header_sequence_test(self, driver, url):
        """Check the sequence of HTML header tags for the given URL."""
        try:
            self._wait_for_page_load(driver)

            headers = driver.find_elements(By.XPATH, '//h1 | //h2 | //h3 | //h4 | //h5 | //h6')
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

    def process_page(self, url, depth):
        if depth > self.max_depth or len(self.visited_urls) >= self.max_links:
            return

        driver = self._initialize_driver()
        retries = 3  # Number of retries for timeout errors
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

                    # Run header sequence test
                    self.run_header_sequence_test(driver, final_url)

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
                        time.sleep(2)  # Wait before retrying
                    else:
                        print(f"[ERROR] URL: {url} - Timeout after {retries} attempts.")
                        self.results.append((url, "Page Load", "Timeout", str(e)))
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
        """Generate an Excel report of the results."""
        print("Generating test report...")
        df = pd.DataFrame(self.results, columns=["URL", "Test", "Result", "Comments"])
        report_file = os.path.join(self.output_folder, "header_sequence_test_report.xlsx")
        df.to_excel(report_file, index=False)
        print(f"Report saved to {report_file}")

if __name__ == "__main__":
    tester = VacationRentalTester(url="https://www.alojamiento.io/property/apartamentos-centro-col%c3%b3n/BC-189483/", headless=True, max_depth=3, max_links=10, max_workers=10)
    tester.run_recursive_tests()
    tester.generate_report()
