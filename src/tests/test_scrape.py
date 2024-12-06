def run(driver, add_result):
    try:
        script_data = {
            'SiteURL': driver.current_url,
            'SiteName': driver.title,
            'Browser': 'Chrome',
            'CountryCode': 'UNKNOWN',  # You can replace this with actual country code logic
            'IP': 'UNKNOWN_IP'  # Replace with actual IP logic
        }
        add_result('Script Data Scraping', True, str(script_data))
    except Exception as e:
        add_result('Script Data Scraping', False, f'Error scraping script data: {e}')
