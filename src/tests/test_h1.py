from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import urlparse, urljoin
import time

class H1TagTester:
    def __init__(self, driver, base_url, sitemap_keywords=None):
        self.driver = driver
        self.base_url = base_url
        self.visited_urls = set()  # Set to track visited URLs
        self.sitemap_keywords = sitemap_keywords or ['sitemap', 'robots.txt']  # Sitemap-related keywords to skip

    def run(self, add_result_callback):
        """
        Test only the current page for H1 tags.
        """
        current_url = self.base_url  # Test the base URL

        # Check if this URL has already been visited
        if current_url in self.visited_urls:
            print(f"Skipping {current_url} (already visited)")
            return

        self.visited_urls.add(current_url)

        # Visit the page
        self.driver.get(current_url)
        print(f"Testing {current_url}")

        # Wait for the page to load
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, 'body'))
            )
        except Exception as e:
            add_result_callback('Page Load', False, f"Error loading page: {str(e)}", current_url)
            return

        # Run the H1 tag test on the current page
        self._test_h1_tags(add_result_callback, current_url)

    def _test_h1_tags(self, add_result_callback, current_url):
        """
        Perform the actual test of the H1 tag for the given page URL.
        """
        try:
            # Find H1 tags
            h1_tags = self.driver.find_elements(By.TAG_NAME, 'h1')

            # Test H1 tag existence
            add_result_callback('H1 Tag Existence', bool(h1_tags), f"Found {len(h1_tags)} H1 tag(s) on {current_url}", current_url)

            # Test number of H1 tags
            add_result_callback('H1 Tag Count', len(h1_tags) <= 1, f"Total H1 tags: {len(h1_tags)} on {current_url}", current_url)

            # Test H1 tag content
            if h1_tags:
                h1_text = h1_tags[0].text.strip()
                add_result_callback('H1 Tag Content', bool(h1_text), f'H1 Text: {h1_text} on {current_url}', current_url)
            else:
                add_result_callback('H1 Tag Content', False, f'No H1 tags found on {current_url}', current_url)
        except Exception as e:
            add_result_callback('H1 Tag Test', False, f'Error on {current_url}: {str(e)}', current_url)
