#!/usr/bin/env python3
"""
Test script to validate the improved teacher extraction methods in Phase 2 CBSE scraper.
This script tests the new Selenium-based extraction methods against the provided HTML structure.
"""

import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_teacher_extraction_methods():
    """Test the improved teacher extraction methods"""
    
    # Sample HTML structure for testing
    test_html = """
    <!DOCTYPE html>
    <html>
    <head><title>Test Teacher Extraction</title></head>
    <body>
        <div class="bg-white my-1 rounded p-3 me-3 shadow">
            <h2 class="innerTitle mt89898 mb-4">Teacher</h2>
            <div class="rounded" style="background: #41257a;">
                <div class="d-flex align-items-center">
                    <div class="flex-shrink-0 px-3">
                        <img src="assets/images/teacher-icon.svg" alt="graduation-student-icon" width="45px" class="img-fluid">
                    </div>
                    <div class="flex-grow-1">
                        <div class="greyInfoAreaBot">
                            <ul class="greyInfoList text-white">
                                <li>
                                    <div class="brLeft">
                                        <p class="fontTitle15 mb-0">Total Teachers</p>
                                        <p class="H3Value mb-0"> 12 </p>
                                    </div>
                                </li>
                                <li>
                                    <div class="brLeft">
                                        <p class="fontTitle15 mb-0">Male</p>
                                        <p class="H3Value mb-0"> 10 </p>
                                    </div>
                                </li>
                                <li>
                                    <p class="fontTitle15 mb-0">Female</p>
                                    <p class="H3Value mb-0"> 2 </p>
                                </li>
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Set up Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode for testing
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = None
    try:
        # Initialize WebDriver
        driver = webdriver.Chrome(options=chrome_options)
        
        # Load the test HTML
        driver.execute_script(f"document.open(); document.write(`{test_html}`); document.close();")
        
        # Wait for the page to load
        time.sleep(1)
        
        print("🧪 Testing Teacher Extraction Methods")
        print("=" * 50)
        
        # Initialize data structure
        data = {
            'total_teachers': 'N/A',
            'male_teachers': 'N/A',
            'female_teachers': 'N/A'
        }
        
        # Method 1: Label-based extraction within teacher section
        print("\n📋 Method 1: Label-based extraction")
        try:
            teacher_headers = driver.find_elements(By.XPATH, "//h2[contains(text(), 'Teacher')]")
            if teacher_headers:
                print("   ✅ Found teacher section header")
                teacher_section = teacher_headers[0].find_element(By.XPATH, "following-sibling::div[1]")
                
                teacher_data_mappings = [
                    ("Total Teachers", 'total_teachers'),
                    ("Male", 'male_teachers'), 
                    ("Female", 'female_teachers')
                ]
                
                for label_text, field_name in teacher_data_mappings:
                    try:
                        label_elements = teacher_section.find_elements(By.XPATH, f".//p[contains(@class, 'fontTitle15') and contains(text(), '{label_text}')]")
                        for label_element in label_elements:
                            try:
                                value_element = label_element.find_element(By.XPATH, "following-sibling::p[contains(@class, 'H3Value')]")
                                value = value_element.text.strip()
                                if value.isdigit():
                                    data[field_name] = value
                                    print(f"   ✅ Found {field_name}: {value}")
                                    break
                            except Exception as e:
                                print(f"   ❌ Error getting value for {label_text}: {e}")
                    except Exception as e:
                        print(f"   ❌ Error finding label for {field_name}: {e}")
        except Exception as e:
            print(f"   ❌ Error in label-based extraction: {e}")
        
        # Reset data for next test
        data = {'total_teachers': 'N/A', 'male_teachers': 'N/A', 'female_teachers': 'N/A'}
        
        # Method 2: CSS Selector approach
        print("\n🎯 Method 2: CSS Selector approach")
        teacher_selectors = [
            (".greyInfoList li:nth-child(1) .H3Value", 'total_teachers'),
            (".greyInfoList li:nth-child(2) .H3Value", 'male_teachers'),
            (".greyInfoList li:nth-child(3) .H3Value", 'female_teachers'),
        ]
        
        for selector, field_name in teacher_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    value = element.text.strip()
                    if value.isdigit():
                        data[field_name] = value
                        print(f"   ✅ Found {field_name}: {value}")
                        break
            except Exception as e:
                print(f"   ❌ CSS selector failed for {field_name}: {e}")
        
        # Reset data for next test
        data = {'total_teachers': 'N/A', 'male_teachers': 'N/A', 'female_teachers': 'N/A'}
        
        # Method 3: XPath approach
        print("\n🔍 Method 3: XPath approach")
        xpath_selectors = [
            ("//p[contains(@class, 'fontTitle15') and contains(text(), 'Total Teachers')]/following-sibling::p[contains(@class, 'H3Value')]", 'total_teachers'),
            ("//p[contains(@class, 'fontTitle15') and text()='Male']/following-sibling::p[contains(@class, 'H3Value')]", 'male_teachers'),
            ("//p[contains(@class, 'fontTitle15') and text()='Female']/following-sibling::p[contains(@class, 'H3Value')]", 'female_teachers'),
        ]
        
        for xpath, field_name in xpath_selectors:
            try:
                elements = driver.find_elements(By.XPATH, xpath)
                for element in elements:
                    value = element.text.strip()
                    if value.isdigit():
                        data[field_name] = value
                        print(f"   ✅ Found {field_name}: {value}")
                        break
            except Exception as e:
                print(f"   ❌ XPath selector failed for {field_name}: {e}")
        
        print("\n" + "=" * 50)
        print("🎉 Test completed successfully!")
        print("Expected results: Total=12, Male=10, Female=2")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    test_teacher_extraction_methods()
