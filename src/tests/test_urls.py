import os
import requests
import pandas as pd
from bs4 import BeautifulSoup
from urllib.parse import urljoin

class URLStatusTester:
    def __init__(self, url='https://www.example.com', output_folder='test_results'):
        # Initialize output folder and ensure it exists
        self.output_folder = output_folder
        os.makedirs(self.output_folder, exist_ok=True)

        # Initialize URL list and result storage
        self.start_url = url
        self.visited_urls = set()
        self.results = []

    def check_url_status(self, url):
        """Check the HTTP status code for the URL."""
        try:
            # Setting timeout and allowing redirects
            response = requests.get(url, timeout=10, allow_redirects=True)
            status_code = response.status_code
            if status_code == 404:
                print(f"[ERROR] URL: {url} - Status code: 404 (Not Found)")
                self.results.append((url, "URL Status Code", "Fail", "404 Not Found"))
            else:
                print(f"[INFO] URL: {url} - Status code: {status_code}")
                self.results.append((url, "URL Status Code", "Success", f"Status code: {status_code}"))
        except requests.RequestException as e:
            print(f"[ERROR] URL: {url} - Error checking status code: {e}")
            self.results.append((url, "URL Status Code", "Error", str(e)))

    def crawl_and_test(self, url):
        """Crawl the URL to extract all links and test them."""
        if url in self.visited_urls:
            return  # Skip already visited URLs
        
        print(f"Testing URL: {url}")
        self.check_url_status(url)
        self.visited_urls.add(url)

        # Attempt to extract links from the page
        try:
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.content, "html.parser")
            links = soup.find_all("a", href=True)
            
            for link in links:
                # Resolve relative URLs to absolute URLs
                full_url = urljoin(url, link['href'])
                
                # Crawl and test each link (if not already visited)
                if full_url not in self.visited_urls:
                    self.crawl_and_test(full_url)
        except requests.RequestException as e:
            print(f"[ERROR] URL: {url} - Error crawling links: {e}")

    def run_tests(self):
        """Run tests on the provided URL and crawl all links recursively."""
        print(f"Starting status code test on: {self.start_url}")
        self.crawl_and_test(self.start_url)

    def generate_report(self):
        """Generate an Excel report of the results."""
        print("Generating test report...")
        header_df = pd.DataFrame(self.results, columns=["URL", "Test", "Result", "Comments"])
        report_file = os.path.join(self.output_folder, "test_report.xlsx")

        with pd.ExcelWriter(report_file, engine='openpyxl') as writer:
            header_df.to_excel(writer, index=False, sheet_name="URL Status Code")

        print(f"Report saved to {report_file}")

if __name__ == "__main__":
    # Initialize the tester with the target URL
    tester = URLStatusTester(url="https://www.alojamiento.io/property/apartamentos-centro-col%c3%b3n/BC-189483/")
    try:
        # Run the status code tests and crawl all linked pages
        tester.run_tests()

        # Generate the report after tests
        tester.generate_report()
    finally:
        # No cleanup required
        pass
