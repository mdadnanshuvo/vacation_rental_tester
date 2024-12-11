import os
import json
import traceback
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

class AlojamientoScraper:
    def __init__(self, url):
        """
        Initialize the web scraper with Chrome WebDriver
        """
        # Set up Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        # chrome_options.add_argument("--headless")  # Uncomment this line to run in headless mode

        # Set up the WebDriver
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )

        # Navigate to the URL
        self.driver.get(url)
        self.property_data = {}

    def fetch_script_data(self):
        """
        Use JavaScript execution to fetch data directly from the console.
        """
        try:
            # Use execute_script to fetch the ScriptData object
            script_data = self.driver.execute_script("return window.ScriptData;")
            if not script_data:
                raise ValueError("ScriptData not found on the page.")

            # Save the ScriptData object for further processing
            self.property_data = script_data

            # Debugging: Display the entire ScriptData object
            print("Fetched ScriptData (JSON):")
            print(json.dumps(self.property_data, indent=4))  # Pretty print for readability

        except Exception as e:
            print(f"Error fetching ScriptData: {e}")
            print(f"Stack Trace: {traceback.format_exc()}")
            self.property_data = {}

    def extract_required_fields(self):
        """
        Extract specific fields from ScriptData (SiteURL, CampaignID, SiteName, Browser, CountryCode, IP).
        """
        if not self.property_data:
            print("No ScriptData available.")
            return {}

        try:
            # Extracting required fields directly
            user_info = self.property_data.get('userInfo', {})

            extracted_data = {
                'SiteURL': self.property_data.get('staticFile', 'N/A'),
                'CampaignID': self.property_data.get('stsConfig', {}).get('EnabledFeeds', 'N/A'),
                'SiteName': self.property_data.get('config', {}).get('SiteName', 'N/A'),
                'Browser': user_info.get('Browser', 'N/A'),
                'CountryCode': user_info.get('CountryCode', 'N/A'),
                'IP': user_info.get('IP', 'N/A')
            }

            # Debugging: Print the extracted data
            print("Extracted Data:", extracted_data)

            return extracted_data

        except Exception as e:
            print(f"Error extracting fields: {e}")
            return {}

    def save_to_excel(self, data, filename='alojamiento_property_details.xlsx'):
        """
        Save collected data to an Excel file.
        """
        if not data:
            print("No data to save!")
            return

        try:
            # Create the 'test_results' folder if it doesn't exist
            output_dir = 'test_results'
            os.makedirs(output_dir, exist_ok=True)

            # Define the full file path
            file_path = os.path.join(output_dir, filename)

            # Create DataFrame
            df = pd.DataFrame([data])

            # Save to Excel
            df.to_excel(file_path, index=False)
            print(f"Data saved to {file_path}")
        except Exception as e:
            print(f"Error saving data to Excel: {e}")

    def close(self):
        """
        Close the WebDriver.
        """
        try:
            self.driver.quit()
            print("Driver closed successfully.")
        except Exception as e:
            print(f"Error closing driver: {e}")


def main():
    # Target URL
    url = 'https://www.alojamiento.io/property/apartamentos-centro-col%c3%b3n/BC-189483/'

    # Create scraper instance
    scraper = AlojamientoScraper(url)

    try:
        # Fetch ScriptData using JavaScript execution
        scraper.fetch_script_data()

        # Extract required fields
        extracted_data = scraper.extract_required_fields()
        print("Extracted Data:", extracted_data)

        # Save results to Excel
        scraper.save_to_excel(extracted_data)

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        # Always close the driver
        scraper.close()


if __name__ == "__main__":
    main()
