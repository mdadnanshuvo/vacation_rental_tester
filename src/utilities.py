import os
import logging
from typing import Optional

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

def setup_logging(log_dir: str = 'logs'):
    """
    Configure logging for the application.
    
    Args:
        log_dir (str): Directory to store log files
    """
    # Create logs directory if it doesn't exist
    os.makedirs(log_dir, exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(os.path.join(log_dir, 'vacation_rental_tester.log')),
            logging.StreamHandler()
        ]
    )

def create_output_directories():
    """
    Create necessary output directories for the project.
    """
    directories = [
        'data',
        'drivers',
        'test_results',
        'logs'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

class WebDriverSetup:
    def __init__(
        self, 
        base_url: str = 'https://www.alojamiento.io/', 
        headless: bool = False
    ):
        """
        Setup WebDriver with configurable options.
        
        Args:
            base_url (str): Base URL to test
            headless (bool): Run browser in headless mode
        """
        self.base_url = base_url
        self.headless = headless
        self.driver = self._setup_driver()
    
    def _setup_driver(self):
        """
        Configure and return WebDriver instance.
        
        Returns:
            Configured WebDriver
        """
        options = Options()
        if self.headless:
            options.add_argument('--headless')
        options.add_argument('--start-maximized')
        
        # Use WebDriver Manager to handle driver installation
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )
        
        return driver
    
    def export_results(self, filename: str):
        """
        Export test results to Excel.
        
        Args:
            filename (str): Output Excel file path
        """
        import pandas as pd
        
        # Implement result export logic
        # This is a placeholder and should be customized based on actual test results
        results = getattr(self, '_test_results', [])
        
        if results:
            df = pd.DataFrame(results)
            df.to_excel(filename, index=False)
            logging.info(f"Results exported to {filename}")