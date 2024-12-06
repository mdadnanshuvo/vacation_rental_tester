import requests
from selenium.webdriver.common.by import By

def run(driver, add_result):
    try:
        links = driver.find_elements(By.TAG_NAME, 'a')
        for link in links:
            href = link.get_attribute('href')
            if href and href.startswith('http'):
                try:
                    response = requests.head(href, timeout=5)
                    add_result('URL Status Code', response.status_code < 400, f'Status Code: {response.status_code}', page_url=href)
                except requests.RequestException:
                    add_result('URL Status Code', False, 'Error accessing URL', page_url=href)
    except Exception as e:
        add_result('URL Status Code', False, f'Error checking URL status codes: {e}')
