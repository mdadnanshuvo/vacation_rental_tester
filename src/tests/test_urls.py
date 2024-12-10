import os
import pandas as pd
from urllib.parse import urlparse, urljoin
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

class VacationRentalTester:
    def __init__(self, url='https://www.example.com', output_folder='test_results', headless=False, max_workers=5, max_depth=3, max_links=100):
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
        self.max_workers = max_workers
        self.max_depth = max_depth
        self.max_links = max_links

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

    def check_url_status_code(self, url):
        """Check the status code of the URL."""
        try:
            response = requests.get(url)
            if response.status_code == 404:
                print(f"[ERROR] URL: {url} - Status code 404 (Not Found)")
                self.results.append((url, "URL Status Code", "Fail", "404 Not Found"))
            else:
                print(f"[SUCCESS] URL: {url} - Status code: {response.status_code}")
                self.results.append((url, "URL Status Code", "Pass", f"Status code: {response.status_code}"))
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] URL: {url} - Error during status code check: {e}")
            self.results.append((url, "URL Status Code", "Error", str(e)))

    def process_page(self, url, depth):
        if depth > self.max_depth or len(self.visited_urls) >= self.max_links:
            return

        driver = self._initialize_driver()
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

            # Run the URL status code test
            self.check_url_status_code(final_url)

            # Extract and queue new links
            links = driver.find_elements(By.XPATH, "//a[@href]")
            for link in links:
                href = link.get_attribute("href")
                if href and not href.startswith(('javascript:', '#')):
                    resolved_url = urljoin(final_url, href).rstrip('/')
                    parsed_resolved_url = urlparse(resolved_url)
                    canonical_url = f"{parsed_resolved_url.scheme}://{parsed_resolved_url.netloc}{parsed_resolved_url.path}"
                    if canonical_url not in self.visited_urls and all(canonical_url != item[0] for item in self.to_visit) and parsed_resolved_url.netloc == self.start_domain:
                        self.to_visit.append((canonical_url, depth + 1))

        except Exception as e:
            print(f"Error testing URL {url}: {e}")
        finally:
            driver.quit()

    def run_recursive_tests(self):
        """Crawl pages recursively using multithreading."""
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            while self.to_visit:
                futures = {executor.submit(self.process_page, url, depth): (url, depth) for url, depth in self.to_visit}
                self.to_visit.clear()

                for future in as_completed(futures):
                    url, depth = futures[future]
                    try:
                        future.result()
                    except Exception as e:
                        print(f"Error processing {url}: {e}")

    def generate_report(self):
        """Generate an Excel report of the results."""
        print("Generating test report...")
        df = pd.DataFrame(self.results, columns=["URL", "Test", "Result", "Comments"])
        report_file = os.path.join(self.output_folder, "url_status_code_test_report.xlsx")
        df.to_excel(report_file, index=False)
        print(f"Report saved to {report_file}")

if __name__ == "__main__":
    tester = VacationRentalTester(url="https://www.alojamiento.io/property/apartamentos-centro-col%c3%b3n/BC-189483/", headless=True, max_depth=3, max_links=100)
    tester.run_recursive_tests()
    tester.generate_report()
 