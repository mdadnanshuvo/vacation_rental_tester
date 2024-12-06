from selenium.webdriver.common.by import By

def run(driver, add_result):
    try:
        tag_levels = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']
        all_headings = [heading for tag in tag_levels for heading in driver.find_elements(By.TAG_NAME, tag)]
        add_result('HTML Tag Sequence', len(all_headings) > 0, f'Total headings found: {len(all_headings)}')
    except Exception as e:
        add_result('HTML Tag Sequence', False, f'Error checking HTML tag sequence: {e}')
