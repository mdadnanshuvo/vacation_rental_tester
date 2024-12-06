from selenium.webdriver.common.by import By

def run(driver, add_result):
    try:
        images = driver.find_elements(By.TAG_NAME, 'img')
        images_without_alt = [img for img in images if not img.get_attribute('alt')]
        add_result('Image Alt Attributes', len(images_without_alt) == 0, f'{len(images_without_alt)} images without alt attribute')
    except Exception as e:
        add_result('Image Alt Attributes', False, f'Error checking image alt attributes: {e}')
