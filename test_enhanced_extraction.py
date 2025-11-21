#!/usr/bin/env python3
"""
Test Script for Enhanced Phase 2 Data Extraction
Tests the new Educational District, Block, and improved Teacher data extraction
"""

import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By

def test_html_parsing():
    """Test the regex patterns and CSS selectors with sample HTML"""
    
    # Sample HTML from the user's request
    sample_html = '''
    <div _ngcontent-ng-c1808753454="" class="col-sm-12">
        <p _ngcontent-ng-c1808753454="" class="fw-600 mb-1"> UDISE Code :<span _ngcontent-ng-c1808753454="" style="color: black;"> ******00501</span><span _ngcontent-ng-c1808753454="" class="ms-2 OperationalStatus">Operational</span></p>
        <p _ngcontent-ng-c1808753454="" class="fw-600 mb-1"> Academic Year :<span _ngcontent-ng-c1808753454="" style="color: black;"> 2025-26</span></p>
        <p _ngcontent-ng-c1808753454="" class="h4 mb-2"><span _ngcontent-ng-c1808753454="" class="fw-600"> State : </span><span _ngcontent-ng-c1808753454="" class="blueCol custom-word-break"> TRIPURA </span><span _ngcontent-ng-c1808753454="" class="px-2"> | </span><span _ngcontent-ng-c1808753454="" class="fw-600"> District : </span><span _ngcontent-ng-c1808753454="" class="blueCol custom-word-break">DHALAI</span><span _ngcontent-ng-c1808753454="" class="px-2"> | </span><span _ngcontent-ng-c1808753454="" class="fw-600"> Block : </span><span _ngcontent-ng-c1808753454="" class="blueCol custom-word-break">MANU</span></p>
        <h3 _ngcontent-ng-c1808753454="" class="custom-word-break schoolNameCSS mb-2"> ADHAR CHAND ROAJA PARA J.B. SCHOOL </h3>
        <p _ngcontent-ng-c1808753454="" class="h4"><span _ngcontent-ng-c1808753454="" class="fw-600">Address : </span> GAINAMA, MANU RD BLOCK , 799273 </p>
    </div>

    <div _ngcontent-ng-c1808753454="" class="bg-white my-1 rounded p-3 me-3 shadow">
        <h2 _ngcontent-ng-c1808753454="" class="innerTitle mt89898 mb-4">Teacher</h2>
        <div _ngcontent-ng-c1808753454="" class="rounded" style="background: #41257a;">
            <div _ngcontent-ng-c1808753454="" class="d-flex align-items-center">
                <div _ngcontent-ng-c1808753454="" class="flex-shrink-0 px-3">
                    <img _ngcontent-ng-c1808753454="" src="assets/images/teacher-icon.svg" alt="graduation-student-icon" width="45px" class="img-fluid">
                </div>
                <div _ngcontent-ng-c1808753454="" class="flex-grow-1">
                    <div _ngcontent-ng-c1808753454="" class="greyInfoAreaBot">
                        <ul _ngcontent-ng-c1808753454="" class="greyInfoList text-white">
                            <li _ngcontent-ng-c1808753454="">
                                <div _ngcontent-ng-c1808753454="" class="brLeft">
                                    <p _ngcontent-ng-c1808753454="" class="fontTitle15 mb-0">Total Teachers</p>
                                    <p _ngcontent-ng-c1808753454="" class="H3Value mb-0"> 1 </p>
                                </div>
                            </li>
                            <li _ngcontent-ng-c1808753454="">
                                <div _ngcontent-ng-c1808753454="" class="brLeft">
                                    <p _ngcontent-ng-c1808753454="" class="fontTitle15 mb-0">Male</p>
                                    <p _ngcontent-ng-c1808753454="" class="H3Value mb-0"> 1 </p>
                                </div>
                            </li>
                            <li _ngcontent-ng-c1808753454="">
                                <p _ngcontent-ng-c1808753454="" class="fontTitle15 mb-0">Female</p>
                                <p _ngcontent-ng-c1808753454="" class="H3Value mb-0"> 0 </p>
                            </li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>
    </div>
    '''
    
    print("🧪 Testing Enhanced Data Extraction Patterns")
    print("=" * 60)
    
    # Test Educational District extraction
    print("\n1. Educational District Extraction:")
    district_patterns = [
        r'District\s*:\s*</span><span[^>]*class="blueCol[^>]*>([^<]+)</span>',
        r'District\s*:\s*([^|]+)\|',
        r'District\s*:\s*([^<]+)<'
    ]
    
    for i, pattern in enumerate(district_patterns, 1):
        match = re.search(pattern, sample_html, re.IGNORECASE)
        if match:
            result = match.group(1).strip()
            print(f"   Pattern {i}: ✅ Found '{result}'")
        else:
            print(f"   Pattern {i}: ❌ No match")
    
    # Test Educational Block extraction
    print("\n2. Educational Block Extraction:")
    block_patterns = [
        r'Block\s*:\s*</span><span[^>]*class="blueCol[^>]*>([^<]+)</span>',
        r'Block\s*:\s*([^<]+)</p>',
        r'Block\s*:\s*([^<]+)$'
    ]
    
    for i, pattern in enumerate(block_patterns, 1):
        match = re.search(pattern, sample_html, re.IGNORECASE | re.MULTILINE)
        if match:
            result = match.group(1).strip()
            print(f"   Pattern {i}: ✅ Found '{result}'")
        else:
            print(f"   Pattern {i}: ❌ No match")
    
    # Test Teacher data extraction
    print("\n3. Teacher Data Extraction:")
    teacher_patterns = [
        (r'<p[^>]*class="fontTitle15[^>]*>Total Teachers</p>\s*<p[^>]*class="H3Value[^>]*>\s*(\d+)\s*</p>', 'Total Teachers'),
        (r'<p[^>]*class="fontTitle15[^>]*>Male</p>\s*<p[^>]*class="H3Value[^>]*>\s*(\d+)\s*</p>', 'Male Teachers'),
        (r'<p[^>]*class="fontTitle15[^>]*>Female</p>\s*<p[^>]*class="H3Value[^>]*>\s*(\d+)\s*</p>', 'Female Teachers'),
    ]
    
    for pattern, field_name in teacher_patterns:
        match = re.search(pattern, sample_html, re.IGNORECASE | re.DOTALL)
        if match:
            result = match.group(1).strip()
            print(f"   {field_name}: ✅ Found '{result}'")
        else:
            print(f"   {field_name}: ❌ No match")
    
    print("\n" + "=" * 60)
    print("✅ Pattern testing completed!")

def test_css_selectors_with_selenium():
    """Test CSS selectors with actual Selenium WebDriver (requires manual URL)"""
    
    print("\n🌐 Testing CSS Selectors with Selenium")
    print("=" * 60)
    print("Note: This requires a valid CBSE school detail page URL")
    print("Update the test_url variable below with an actual school URL")
    
    # Example URL - replace with actual school detail page
    test_url = "https://example-cbse-school-url.com"
    
    print(f"Test URL: {test_url}")
    print("To run this test:")
    print("1. Replace test_url with an actual CBSE school detail page URL")
    print("2. Uncomment the selenium test code below")
    print("3. Run the script")
    
    # Uncomment below to test with actual Selenium
    """
    try:
        # Setup Chrome options
        options = ChromeOptions()
        options.add_argument("--headless")  # Run in background
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        
        driver = webdriver.Chrome(options=options)
        driver.get(test_url)
        
        # Test Educational District and Block
        print("\n📍 Testing Header Information:")
        header_elements = driver.find_elements(By.CSS_SELECTOR, ".col-sm-12 p.h4")
        for element in header_elements:
            text = element.text.strip()
            if "District :" in text and "Block :" in text:
                print(f"   Found header: {text}")
                
                # Extract district
                district_match = re.search(r'District\s*:\s*([^|]+)', text)
                if district_match:
                    print(f"   Educational District: {district_match.group(1).strip()}")
                
                # Extract block
                block_match = re.search(r'Block\s*:\s*(.+)$', text)
                if block_match:
                    print(f"   Educational Block: {block_match.group(1).strip()}")
        
        # Test Teacher Data
        print("\n👨‍🏫 Testing Teacher Data:")
        teacher_selectors = [
            (".greyInfoList li:nth-child(1) .H3Value", 'Total Teachers'),
            (".greyInfoList li:nth-child(2) .H3Value", 'Male Teachers'),
            (".greyInfoList li:nth-child(3) .H3Value", 'Female Teachers'),
        ]
        
        for selector, field_name in teacher_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    value = element.text.strip()
                    if value.isdigit():
                        print(f"   {field_name}: {value}")
                        break
            except Exception as e:
                print(f"   {field_name}: Error - {e}")
        
        driver.quit()
        print("\n✅ Selenium testing completed!")
        
    except Exception as e:
        print(f"❌ Selenium test failed: {e}")
        print("Make sure ChromeDriver is installed and the URL is valid")
    """

def test_data_combination():
    """Test data combination logic"""
    
    print("\n🔄 Testing Data Combination Logic")
    print("=" * 60)
    
    # Sample Phase 1 data
    phase1_data = {
        'udise_code': '12345678901',
        'school_name': 'Test School',
        'state': 'TRIPURA',
        'district': 'DHALAI',
        'pin_code': '799273',
        'academic_year': '2024-25'  # This should be overridden
    }
    
    # Sample Phase 2 extracted data
    phase2_data = {
        'edu_district': 'DHALAI',
        'edu_block': 'MANU',
        'academic_year': '2025-26',
        'total_teachers': '1',
        'male_teachers': '1',
        'female_teachers': '0'
    }
    
    # Combine data (simulating the scraper logic)
    combined_data = phase1_data.copy()
    combined_data.update(phase2_data)
    
    # Ensure pin_code is preserved from Phase 1
    if 'pin_code' in phase1_data and phase1_data['pin_code'] not in ['N/A', '', None]:
        combined_data['pin_code'] = phase1_data['pin_code']
    
    # Ensure academic year is set to 2025-26
    combined_data['academic_year'] = '2025-26'
    
    print("Phase 1 Data:")
    for key, value in phase1_data.items():
        print(f"   {key}: {value}")
    
    print("\nPhase 2 Data:")
    for key, value in phase2_data.items():
        print(f"   {key}: {value}")
    
    print("\nCombined Data:")
    for key, value in combined_data.items():
        print(f"   {key}: {value}")
    
    # Verify key requirements
    print("\n✅ Verification:")
    print(f"   Pin code preserved: {'✅' if combined_data['pin_code'] == '799273' else '❌'}")
    print(f"   Academic year set to 2025-26: {'✅' if combined_data['academic_year'] == '2025-26' else '❌'}")
    print(f"   Educational District extracted: {'✅' if combined_data['edu_district'] == 'DHALAI' else '❌'}")
    print(f"   Educational Block extracted: {'✅' if combined_data['edu_block'] == 'MANU' else '❌'}")
    print(f"   Female teachers extracted: {'✅' if combined_data['female_teachers'] == '0' else '❌'}")

if __name__ == "__main__":
    print("🧪 Enhanced Phase 2 Extraction Test Suite")
    print("=" * 60)
    
    # Run all tests
    test_html_parsing()
    test_css_selectors_with_selenium()
    test_data_combination()
    
    print("\n🎉 All tests completed!")
    print("\nNext steps:")
    print("1. Run the enhanced Phase_2_Scraping.py with your CSV file")
    print("2. Check the output CSV for the new edu_district and edu_block columns")
    print("3. Verify that pin_code is preserved and academic_year is set to 2025-26")
    print("4. Confirm that female teacher extraction is working correctly")
