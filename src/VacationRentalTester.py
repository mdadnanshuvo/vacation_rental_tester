import os
import socket
from urllib.parse import urlparse
from datetime import datetime
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager # Ensure test_h1 is correctly implemented
from concurrent.futures import ThreadPoolExecutor
import argparse
from .tests.test_h1 import H1TagTester

class VacationRentalTester:
    def __init__(self, url='https://www.alojamiento.io/property/apartamentos-centro-col%c3%b3n/BC-189483/', output_folder='test_results', headless=False):
        self.output_folder = output_folder
        os.makedirs(self.output_folder, exist_ok=True)

        # Setup Chrome options
        self.options = webdriver.ChromeOptions()
        if headless:
            self.options.add_argument("--headless")
        self.options.add_argument("--start-maximized")

        # Initialize WebDriver
        self.driver = None  # Driver initialized on demand
        self.url = url
        self.results = []

        # Extract domain from URL
        try:
            parsed_url = urlparse(url)
            self.site_name = parsed_url.netloc.replace('www.', '').split('.')[0].capitalize()
        except Exception as e:
            self.site_name = 'Unknown'
            print(f"Error parsing URL: {e}")

        # Get local IP and basic network info
        try:
            self.ip = socket.gethostbyname(socket.gethostname())
            self.country_code = (
                socket.getfqdn().split('.')[-1].upper() if '.' in socket.getfqdn() else 'UNKNOWN'
            )
        except Exception as e:
            self.ip = 'UNKNOWN'
            self.country_code = 'UNKNOWN'
            print(f"Error obtaining network info: {e}")

    def _initialize_driver(self):
        if not self.driver:
            self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=self.options)

    def run_h1_test(self):
        try:
            self._initialize_driver()
            tester = H1TagTester(self.driver, self.url)
            tester.run(self._add_result)
            print("H1 test completed successfully.")
        except Exception as e:
            print(f"An error occurred during the H1 test: {e}")
        finally:
            if self.driver:
                self.driver.quit()
                self.driver = None

    def run_all_tests(self):
        """
        Run all available test cases concurrently
        """
        with ThreadPoolExecutor() as executor:
            # Run multiple tests concurrently
            future_to_test = {
                executor.submit(self.run_h1_test): 'H1 Test',
                # Add other test methods here as needed, e.g.:
                # executor.submit(self.run_another_test): 'Another Test',
            }

            for future in future_to_test:
                try:
                    future.result()  # Wait for the test to finish
                    print(f"{future_to_test[future]} completed successfully.")
                except Exception as e:
                    print(f"Error in {future_to_test[future]}: {e}")

    def _add_result(self, testcase, passed, comments, page_url=None):
        self.results.append({
            'page_url': page_url or self.url,
            'testcase': testcase,
            'passed': passed,
            'comments': comments
        })

    def generate_report(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_df = pd.DataFrame(self.results)

        if results_df.empty:
            print("No test results to generate reports.")
            return

        # Generate main test results report
        results_filename = os.path.join(self.output_folder, f'test_results_{timestamp}.xlsx')
        results_df.to_excel(results_filename, index=False)
        print(f"Test Results Report generated: {results_filename}")
