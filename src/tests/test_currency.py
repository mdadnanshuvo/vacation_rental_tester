import logging
from typing import List, Optional
import traceback
import time
import pandas as pd

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import (
    WebDriverException, 
    TimeoutException, 
    NoSuchElementException
)

from webdriver_manager.chrome import ChromeDriverManager

class CurrencyFilterTester:
    def __init__(
        self, 
        url: str, 
        headless: bool = True,
        timeout: int = 20,
        retry_attempts: int = 3
    ):
        self.url = url
        self.headless = headless
        self.timeout = timeout
        self.retry_attempts = retry_attempts
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s: %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Test results tracking
        self.test_results: List[str] = []
        
        # Initialize driver
        self.driver = self._setup_driver()

    def _setup_driver(self) -> webdriver.Chrome:
        try:
            options = Options()
            options.add_argument('--start-maximized')
            options.add_argument('--disable-extensions')
            options.add_argument('--disable-gpu')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            
            if self.headless:
                options.add_argument('--headless')
            
            # Use Service and ChromeDriverManager for automatic driver management
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            
            # Configure timeouts
            driver.set_page_load_timeout(self.timeout)
            driver.implicitly_wait(10)
            
            return driver
        
        except Exception as e:
            self.logger.error(f"Driver setup failed: {e}")
            raise

    def _safe_find_element(
        self, 
        locator: tuple, 
        timeout: Optional[int] = None
    ) -> Optional[WebElement]:
        timeout = timeout or self.timeout
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located(locator)
            )
            return element
        except (TimeoutException, NoSuchElementException) as e:
            self.logger.warning(f"Element not found: {locator}. Error: {e}")
            return None

    def _safe_click(self, element: WebElement) -> bool:
        interaction_methods = [
            lambda: element.click(),
            lambda: ActionChains(self.driver).move_to_element(element).click().perform(),
            lambda: self.driver.execute_script("arguments[0].click();", element)
        ]
        
        for method in interaction_methods:
            try:
                method()
                time.sleep(0.5)  # Reduce delay for faster interactions
                return True
            except Exception as e:
                self.logger.warning(f"Click method failed: {e}")
        
        return False

    def run_currency_test(self) -> List[str]:
        try:
            # Navigate to URL
            self.driver.get(self.url)
            
            # Find currency dropdown (by id: js-currency-sort-footer)
            dropdown = self._safe_find_element(
                (By.CSS_SELECTOR, "#js-currency-sort-footer")
            )
            if not dropdown:
                self.logger.error("Currency dropdown not found")
                return ["Currency dropdown not found"]
            
            # Open dropdown and wait for smooth interaction
            if not self._safe_click(dropdown):
                self.logger.error("Could not open currency dropdown")
                return ["Failed to open currency dropdown"]
            
            # Find currency options (inside ul.select-ul)
            options = self.driver.find_elements(
                By.CSS_SELECTOR, 
                "#js-currency-sort-footer .select-ul li"
            )
            
            if not options:
                self.logger.error("No currency options found")
                return ["No currency options found"]
            
            # Get initial price
            initial_price_element = self._safe_find_element(
                (By.XPATH, "//div[contains(@class, 'price')]")
            )
            if not initial_price_element:
                self.logger.error("Initial price not found")
                return ["Initial price not found"]
            
            initial_price = initial_price_element.text.strip()
            
            # Test currency options
            results = []
            for index, option in enumerate(options, 1):
                try:
                    # Scroll to option smoothly
                    self.driver.execute_script(
                        "arguments[0].scrollIntoView({ behavior: 'smooth', block: 'center' });", option
                    )
                    
                    # Click currency option
                    if not self._safe_click(option):
                        results.append({
                            "page_url": self.url,
                            "testcase": f"Currency Option {index}",
                            "status": "fail",
                            "comments": "Failed to click currency option"
                        })
                        continue
                    
                    # Wait for price update (explicit wait added here)
                    WebDriverWait(self.driver, self.timeout).until(
                        EC.text_to_be_present_in_element(
                            (By.XPATH, "//div[contains(@class, 'price')]"),
                            "Updated Price"  # You can specify a part of the expected price here
                        )
                    )
                    
                    updated_price_element = self._safe_find_element(
                        (By.XPATH, "//div[contains(@class, 'price')]")
                    )
                    
                    if updated_price_element:
                        updated_price = updated_price_element.text.strip()
                        if updated_price != initial_price:
                            results.append({
                                "page_url": self.url,
                                "testcase": f"Currency Option {index}",
                                "status": "pass",
                                "comments": f"Currency changed successfully to {option.text.strip()}"
                            })
                        else:
                            results.append({
                                "page_url": self.url,
                                "testcase": f"Currency Option {index}",
                                "status": "fail",
                                "comments": "Currency change did not affect price"
                            })
                    else:
                        results.append({
                            "page_url": self.url,
                            "testcase": f"Currency Option {index}",
                            "status": "fail",
                            "comments": "Price not found after currency change"
                        })
                    
                except Exception as e:
                    results.append({
                        "page_url": self.url,
                        "testcase": f"Currency Option {index}",
                        "status": "fail",
                        "comments": f"Error: {str(e)}"
                    })
            
            # Generate Excel report
            self._generate_excel_report(results)
            return results
        
        except Exception as e:
            self.logger.error(f"Test failed: {e}")
            return [f"Critical test failure: {str(e)}"]
        
        finally:
            self.driver.quit()

    def _generate_excel_report(self, results: List[dict]):
        df = pd.DataFrame(results)
        report_filename = "currency_filter_test_report.xlsx"
        df.to_excel(report_filename, index=False, engine='openpyxl')
        self.logger.info(f"Test report generated: {report_filename}")

def main():
    test_url = "https://www.alojamiento.io/property/apartamentos-centro-col%c3%b3n/BC-189483/"
    
    try:
        tester = CurrencyFilterTester(
            url=test_url, 
            headless=False,
            timeout=30
        )
        
        results = tester.run_currency_test()
        
        print("\n--- Test Results ---")
        for result in results:
            print(result)
    
    except Exception as e:
        print(f"Unexpected error: {e}")
        logging.exception(e)

if __name__ == "__main__":
    main()
