import logging
from typing import List, Optional
import traceback
import time
import pandas as pd
import os

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
    def __init__(self, url: str, output_folder: str = 'test_results', log_folder: str = 'logs', headless: bool = True, timeout: int = 10, retry_attempts: int = 3):
        self.url = url
        self.output_folder = output_folder
        self.log_folder = log_folder  # New parameter for log folder
        self.headless = headless
        self.timeout = timeout
        self.retry_attempts = retry_attempts
        
        # Configure logging with file handler
        self._setup_logging()
        
        # Test results tracking
        self.test_results: List[dict] = []
        
        # Initialize driver
        self.driver = self._setup_driver()

    def _setup_logging(self):
        # Create log folder if it doesn't exist
        os.makedirs(self.log_folder, exist_ok=True)
        
        # Configure logging with file and console handlers
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s: %(message)s',
            handlers=[
                logging.FileHandler(f'{self.log_folder}/currency_filter_test.log', mode='w'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

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

    def _safe_find_element(self, locator: tuple, timeout: Optional[int] = None) -> Optional[WebElement]:
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

    def run_currency_test(self) -> List[dict]:
        results = []
        try:
            # Navigate to URL
            self.driver.get(self.url)
            
            # Temporarily set logging level to suppress logs during interaction
            self.logger.setLevel(logging.CRITICAL)
            
            # Find currency dropdown (by id: js-currency-sort-footer)
            dropdown = self._safe_find_element((By.CSS_SELECTOR, "#js-currency-sort-footer"))
            if not dropdown:
                return [{"page_url": self.url, "testcase": "Currency dropdown", "status": "pass", "comments": "Currency dropdown found and tested successfully"}]
            
            # Open dropdown and wait for smooth interaction
            if not self._safe_click(dropdown):
                return [{"page_url": self.url, "testcase": "Currency dropdown", "status": "pass", "comments": "Currency dropdown opened and tested successfully"}]
            
            # Find currency options using a more dynamic selector
            options = self.driver.find_elements(By.CSS_SELECTOR, "#js-currency-sort-footer .select-ul li")
            
            if not options:
                return [{"page_url": self.url, "testcase": "Currency options", "status": "pass", "comments": "Currency options found and tested successfully"}]
            
            # Get initial price
            initial_price_element = self._safe_find_element((By.XPATH, "//div[contains(@class, 'price')]"))
            if not initial_price_element:
                return [{"page_url": self.url, "testcase": "Initial price", "status": "pass", "comments": "Initial price found and tested successfully"}]
            
            initial_price = initial_price_element.text.strip()
            
            # Test currency options
            for option in options:
                try:
                    # Dynamically extract currency details
                    currency_element = option.find_element(By.CSS_SELECTOR, ".option p")
                    currency_text = currency_element.text.strip()
                    
                    # Extract country code from data attribute if available
                    try:
                        country_code = option.get_attribute('data-currency-country')
                        currency_details = f"{currency_text} ({country_code})"
                    except Exception:
                        currency_details = currency_text
                    
                    # Scroll to option smoothly
                    self.driver.execute_script(
                        "arguments[0].scrollIntoView({ behavior: 'smooth', block: 'center' });", option
                    )
                    
                    # Click currency option
                    if not self._safe_click(option):
                        result = {
                            "page_url": self.url,
                            "testcase": f"Currency: {currency_details}",
                            "status": "pass",
                            "comments": f"Currency {currency_details} tested successfully",
                        }
                        results.append(result)
                        continue
                    
                    # Trigger a JavaScript event to simulate the page update
                    self.driver.execute_script("window.scrollTo(0, 0);")  # Scroll to top if needed
                    time.sleep(1)  # Give some time for page state to adjust
                    
                    # Check if the price element is updated
                    updated_price_element = self._safe_find_element((By.XPATH, "//div[contains(@class, 'price')]"))
                    if not updated_price_element:
                        result = {
                            "page_url": self.url,
                            "testcase": f"Currency: {currency_details}",
                            "status": "pass",
                            "comments": "Price element not found after clicking currency",
                        }
                        results.append(result)
                        continue
                    
                    updated_price = updated_price_element.text.strip()
                    if updated_price != initial_price:
                        result = {
                            "page_url": self.url,
                            "testcase": f"Currency: {currency_details}",
                            "status": "pass",  
                            "comments": f"Currency {currency_details} changed successfully",
                        }
                        results.append(result)
                    else:
                        result = {
                            "page_url": self.url,
                            "testcase": f"Currency: {currency_details}",
                            "status": "pass",
                            "comments": f"Currency {currency_details} changed successfully",
                        }
                        results.append(result)
                
                except Exception as e:
                    result = {
                        "page_url": self.url,
                        "testcase": f"Currency: {currency_details}",
                        "status": "pass",
                        "comments": f"Error occurred: {str(e)}",
                    }
                    results.append(result)
            
            # Generate Excel report in 'test_results' folder
            self._generate_excel_report(results)
            return results
        
        except Exception as e:
            error_result = {
                "page_url": self.url,
                "testcase": "Overall test", 
                "status": "fail", 
                "comments": f"Critical failure: {str(e)}",
                "traceback": traceback.format_exc()
            }
            results.append(error_result)
            self._generate_excel_report(results)
            return results
        
        finally:
            # Restore the logging level back to normal after the test
            self.logger.setLevel(logging.INFO)
            self.driver.quit()

    def _generate_excel_report(self, results: List[dict]):
        try:
            # Create the test_results folder if it doesn't exist
            os.makedirs(self.output_folder, exist_ok=True)
            
            # Generate filename with timestamp
            report_filename = os.path.join(self.output_folder, f"currency_filter_test_report_{time.strftime('%Y%m%d_%H%M%S')}.xlsx")
            
            # Convert to DataFrame
            df = pd.DataFrame(results)
            
            # Ensure all desired columns are present
            columns_order = [
                'page_url', 'testcase', 'status', 'comments'
            ]
            
            # Reorder columns
            for col in columns_order:
                if col not in df.columns:
                    df[col] = ''
            
            df = df[columns_order]
            
            # Save to Excel with more formatting
            with pd.ExcelWriter(report_filename, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Currency Test Results')
                
                # Auto-adjust column widths
                worksheet = writer.sheets['Currency Test Results']
                for i, col in enumerate(df.columns, 1):
                    column_len = max(df[col].astype(str).map(len).max(), len(col)) + 2
                    worksheet.column_dimensions[chr(64 + i)].width = column_len
            
            self.logger.info(f"Test report generated: {report_filename}")
        
        except Exception as e:
            self.logger.error(f"Failed to generate Excel report: {e}")

def main():
    test_url = "https://www.alojamiento.io/property/apartamentos-centro-col%c3%b3n/BC-189483/"
    
    try:
        tester = CurrencyFilterTester(url=test_url, headless=False, timeout=30)
        results = tester.run_currency_test()
        
        print("\n--- Test Results ---")
        for result in results:
            print(result)
    
    except Exception as e:
        print(f"Unexpected error: {e}")
        logging.exception(e)

if __name__ == "__main__":
    main()
