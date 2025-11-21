#!/usr/bin/env python3
"""
Optimized Multithreaded Standalone Phase 2 Processor - Independent CSV-based Phase 2 Processing
- Accepts Phase 1 CSV file as input (specify file path in code)
- Skips Phase 1 entirely - only performs Phase 2 processing
- Visits each "know_more_link" URL to extract detailed school information
- Consolidates original Phase 1 data with newly extracted Phase 2 data
- Creates output CSV with incremental writing for crash recovery
- Handles cases where schools may not have valid "know_more_link" URLs
- Uses 3 worker threads with persistent WebDriver instances for optimal performance
- Thread 1 processes rows 1,4,7,10..., Thread 2 processes rows 2,5,8,11..., Thread 3 processes rows 3,6,9,12...
- Each thread reuses its WebDriver to process multiple schools sequentially
- Includes error handling to recreate WebDriver if it becomes unresponsive
"""

import pandas as pd
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
import logging
from datetime import datetime
import os
import re
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ===== CONFIGURATION SECTION =====
# Specify the Phase 1 CSV file to process
INPUT_CSV_FILE = "UP_75 copy.csv"  # Change this to your Phase 1 CSV file

# Optional: Limit processing for testing (set to None for all records)
MAX_RECORDS_TO_PROCESS = None  # Set to a number like 10 for testing, None for all

# ===== END CONFIGURATION SECTION =====

class StandalonePhase2Processor:
    def __init__(self, input_csv_file):
        self.input_csv_file = input_csv_file
        self.driver = None
        self.processed_count = 0
        self.success_count = 0
        self.fail_count = 0

        # Output file setup
        self.output_csv_file = None
        self.csv_headers_written = False

        # Thread-safe mechanisms
        self.csv_lock = threading.Lock()
        self.stats_lock = threading.Lock()

        # Extract state name from input file
        self.state_name = self.extract_state_name_from_filename(input_csv_file)

        # Setup output CSV file
        self.setup_output_csv()

    def extract_state_name_from_filename(self, filename):
        """Extract state name from CSV filename"""
        try:
            basename = os.path.basename(filename)
            
            # Extract state name from different naming patterns
            if "_phase1_complete_" in basename:
                state_name = basename.split("_phase1_complete_")[0]
            elif "_with_links_" in basename:
                state_name = basename.split("_with_links_")[0]
            else:
                state_name = basename.split("_")[0]
            
            # Convert back to readable format
            state_name = state_name.replace("_", " ").replace("and", "&")
            return state_name
            
        except Exception as e:
            logger.error(f"❌ Error extracting state name from {filename}: {e}")
            return "UNKNOWN_STATE"

    def setup_output_csv(self):
        """Setup output CSV file for Phase 2 complete data"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            clean_state = self.state_name.replace(' ', '_').replace('&', 'and').replace('/', '_').upper()
            
            self.output_csv_file = f"{clean_state}_phase2_complete_{timestamp}.csv"
            self.csv_headers_written = False
            
            logger.info(f"📝 Output file will be: {self.output_csv_file}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error setting up output CSV: {e}")
            return False

    def write_to_output_csv(self, combined_data):
        """Thread-safe write of a single school record to output CSV immediately (incremental writing)"""
        try:
            if not self.output_csv_file:
                logger.warning("⚠️ Output CSV file not setup")
                return False

            # Define column order to match exact target format
            column_order = [
                # Phase 1 columns (exact order as specified)
                'has_know_more_link', 'phase2_ready', 'state', 'state_id', 'district', 'district_id',
                'extraction_date', 'udise_code', 'operational_status', 'school_name', 'know_more_link',
                'edu_district', 'edu_block', 'academic_year', 'school_category', 'school_management',
                'class_range', 'school_type', 'school_location', 'address', 'pin_code', 'email',

                # Phase 2 additional columns (exact order as specified)
                'detail_school_name', 'extraction_timestamp', 'location', 'class_from', 'class_to',
                'year_of_establishment', 'national_management', 'state_management',
                'affiliation_board_sec', 'affiliation_board_hsec', 'total_students', 'total_boys',
                'total_girls', 'enrollment_class_range', 'total_teachers', 'male_teachers',
                'female_teachers', 'extraction_status', 'fields_extracted', 'critical_fields_extracted'
            ]

            # Thread-safe CSV writing
            with self.csv_lock:
                # Debug: Check pin_code specifically
                pin_code_value = combined_data.get('pin_code', 'NOT_FOUND')
                logger.debug(f"📍 PIN CODE DEBUG: Input value = '{pin_code_value}'")

                # Create ordered dictionary with specified column order
                ordered_data = {}
                for col in column_order:
                    ordered_data[col] = combined_data.get(col, 'N/A')

                # Add any additional columns that might exist but aren't in our predefined order
                for key, value in combined_data.items():
                    if key not in ordered_data:
                        ordered_data[key] = value

                # Convert to DataFrame with specified column order
                df = pd.DataFrame([ordered_data])

                # Write headers if first record
                if not self.csv_headers_written:
                    df.to_csv(self.output_csv_file, mode='w', index=False, header=True)
                    self.csv_headers_written = True
                    logger.info(f"📝 Created output CSV with headers: {self.output_csv_file}")
                else:
                    # Append data without headers
                    df.to_csv(self.output_csv_file, mode='a', index=False, header=False)

                logger.debug(f"📝 Appended 1 record to output CSV")

            return True

        except Exception as e:
            logger.error(f"❌ Error writing to output CSV: {e}")
            return False

    def update_stats(self, processed=0, success=0, fail=0):
        """Thread-safe update of processing statistics"""
        with self.stats_lock:
            self.processed_count += processed
            self.success_count += success
            self.fail_count += fail

    def check_already_processed(self, udise_code):
        """Check if a school has already been processed (for crash recovery)"""
        try:
            if not os.path.exists(self.output_csv_file):
                return False
            
            # Read existing output file to check for this UDISE code
            existing_df = pd.read_csv(self.output_csv_file)
            if 'udise_code' in existing_df.columns:
                return udise_code in existing_df['udise_code'].values
            
            return False
            
        except Exception as e:
            logger.debug(f"Error checking if already processed: {e}")
            return False

    def setup_driver(self):
        """Initialize Chrome browser driver with optimized settings for Phase 2 processing"""
        try:
            # Setup Chrome options for Phase 2 data extraction
            options = ChromeOptions()

            # Core stability options
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-blink-features=AutomationControlled")

            # Performance optimizations (KEEP JavaScript enabled for dynamic content)
            options.add_argument("--disable-images")  # Speed optimization
            options.add_argument("--disable-plugins")  # Speed optimization

            # Memory and resource optimizations
            options.add_argument("--memory-pressure-off")
            options.add_argument("--max_old_space_size=4096")

            # Additional options for stability in multithreading
            options.add_argument("--disable-web-security")
            options.add_argument("--disable-features=VizDisplayCompositor")

            self.driver = webdriver.Chrome(options=options)
            self.driver.maximize_window()

            # Balanced timeouts for Phase 2 processing
            self.driver.implicitly_wait(5)
            self.driver.set_page_load_timeout(25)

            logger.info("✅ Chrome browser driver initialized for standalone Phase 2 processing")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to initialize Chrome driver: {e}")
            logger.error("Please ensure Chrome browser is installed and updated")
            return False

    def load_phase1_data(self):
        """Load and validate Phase 1 CSV data"""
        try:
            if not os.path.exists(self.input_csv_file):
                logger.error(f"❌ Input CSV file not found: {self.input_csv_file}")
                return None
            
            # Load CSV data
            df = pd.read_csv(self.input_csv_file)
            logger.info(f"📊 Loaded {len(df)} total records from {self.input_csv_file}")
            
            # Check for required columns
            required_columns = ['know_more_link']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                logger.error(f"❌ Missing required columns: {missing_columns}")
                logger.info(f"Available columns: {list(df.columns)}")
                return None
            
            # Filter schools with valid know_more_link URLs
            valid_schools = df[
                df['know_more_link'].notna() & 
                (df['know_more_link'] != 'N/A') & 
                (df['know_more_link'].str.contains('http', na=False))
            ].copy()
            
            logger.info(f"📊 Found {len(valid_schools)} schools with valid know_more_link URLs")
            
            if len(valid_schools) == 0:
                logger.warning("⚠️ No schools with valid know_more_link URLs found")
                return pd.DataFrame()
            
            return valid_schools
            
        except Exception as e:
            logger.error(f"❌ Error loading Phase 1 data: {e}")
            return None

    def extract_focused_data(self, url, max_retries=2):
        """Extract comprehensive data from school detail page with immediate browser refresh"""
        for attempt in range(max_retries):
            try:
                logger.info(f"🌐 Navigating to school detail page: {url}")
                
                # IMMEDIATE BROWSER REFRESH: Navigate and immediately refresh
                try:
                    # Step 1: Navigate to the URL
                    self.driver.get(url)
                    logger.debug(f"   📍 Initial navigation completed")
                    
                    # Step 2: IMMEDIATE REFRESH as requested
                    logger.debug(f"   🔄 Performing IMMEDIATE browser refresh...")
                    self.driver.refresh()
                    
                    # Step 3: Wait for refresh to complete
                    time.sleep(4)  # Increased wait for refresh completion
                    
                    # Step 4: Verify page is loaded
                    WebDriverWait(self.driver, 10).until(
                        lambda driver: driver.execute_script("return document.readyState") == "complete"
                    )
                    
                    # Step 5: Additional wait for dynamic content
                    time.sleep(2)
                    
                    logger.debug(f"   ✅ Page refreshed and loaded successfully")
                    
                except Exception as e:
                    logger.error(f"   ❌ Navigation/refresh error: {e}")
                    if attempt < max_retries - 1:
                        continue
                    return None
                
                # Initialize comprehensive data structure for all extracted fields
                data = {
                    # School identification
                    'detail_school_name': 'N/A',
                    'extraction_timestamp': datetime.now().isoformat(),

                    # Header information (NEW)
                    'edu_district': 'N/A',
                    'edu_block': 'N/A',

                    # Basic Details section
                    'academic_year': '2025-26',
                    'location': 'N/A',
                    'school_category': 'N/A',
                    'class_from': 'N/A',
                    'class_to': 'N/A',
                    'class_range': 'N/A',
                    'school_type': 'N/A',
                    'year_of_establishment': 'N/A',
                    'national_management': 'N/A',
                    'state_management': 'N/A',
                    'affiliation_board_sec': 'N/A',
                    'affiliation_board_hsec': 'N/A',

                    # Student Enrollment section
                    'total_students': 'N/A',
                    'total_boys': 'N/A',
                    'total_girls': 'N/A',
                    'enrollment_class_range': 'N/A',

                    # Teacher section
                    'total_teachers': 'N/A',
                    'male_teachers': 'N/A',
                    'female_teachers': 'N/A'
                }
                
                # Get page content for extraction
                page_text = self.driver.page_source
                
                # Extract school ID for verification
                url_school_id = re.search(r'/(\d+)/\d+$', url)
                expected_school_id = url_school_id.group(1) if url_school_id else "unknown"
                
                logger.debug(f"   📄 Expected school ID: {expected_school_id}")
                logger.debug(f"   📄 Page content length: {len(page_text)} characters")
                
                # Continue with data extraction in the next part...
                return self.extract_data_from_page(data, page_text, expected_school_id)
                
            except Exception as e:
                logger.warning(f"⚠️ Failed to extract data from {url} (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    logger.info(f"⏳ Retrying in 3 seconds...")
                    time.sleep(3)
                else:
                    return None
        
        return None

    def extract_data_from_page(self, data, page_text, expected_school_id):
        """Extract data from the loaded page"""
        try:
            # 0. HEADER SECTION - Extract Educational District and Block (NEW)
            try:
                logger.debug(f"   🏛️ Extracting Header Information (Educational District & Block)...")

                # Method 1: Try to find header section using Selenium elements
                try:
                    # Look for the header section with State, District, Block information
                    header_elements = self.driver.find_elements(By.CSS_SELECTOR, ".col-sm-12 p.h4")

                    for element in header_elements:
                        element_text = element.text.strip()
                        logger.debug(f"   Found header element: {element_text}")

                        # Look for District and Block information in the same element
                        if "District :" in element_text and "Block :" in element_text:
                            # Extract Educational District
                            district_match = re.search(r'District\s*:\s*([^|]+)', element_text)
                            if district_match:
                                data['edu_district'] = district_match.group(1).strip()
                                logger.debug(f"   Found Educational District: {data['edu_district']}")

                            # Extract Educational Block
                            block_match = re.search(r'Block\s*:\s*(.+)$', element_text)
                            if block_match:
                                data['edu_block'] = block_match.group(1).strip()
                                logger.debug(f"   Found Educational Block: {data['edu_block']}")

                            break

                except Exception as e:
                    logger.debug(f"   Error finding header elements: {e}")

                # Method 2: Fallback - Use regex patterns on page source
                if data['edu_district'] == 'N/A' or data['edu_block'] == 'N/A':
                    try:
                        # Pattern for Educational District
                        if data['edu_district'] == 'N/A':
                            district_patterns = [
                                r'District\s*:\s*</span><span[^>]*class="blueCol[^>]*>([^<]+)</span>',
                                r'District\s*:\s*([^|]+)\|',
                                r'District\s*:\s*([^<]+)<'
                            ]
                            for pattern in district_patterns:
                                match = re.search(pattern, page_text, re.IGNORECASE)
                                if match:
                                    data['edu_district'] = match.group(1).strip()
                                    logger.debug(f"   Found Educational District (regex): {data['edu_district']}")
                                    break

                        # Pattern for Educational Block
                        if data['edu_block'] == 'N/A':
                            block_patterns = [
                                r'Block\s*:\s*</span><span[^>]*class="blueCol[^>]*>([^<]+)</span>',
                                r'Block\s*:\s*([^<]+)</p>',
                                r'Block\s*:\s*([^<]+)$'
                            ]
                            for pattern in block_patterns:
                                match = re.search(pattern, page_text, re.IGNORECASE | re.MULTILINE)
                                if match:
                                    data['edu_block'] = match.group(1).strip()
                                    logger.debug(f"   Found Educational Block (regex): {data['edu_block']}")
                                    break

                    except Exception as e:
                        logger.debug(f"   Error in regex header extraction: {e}")

            except Exception as e:
                logger.debug(f"   Error extracting header information: {e}")

            # 1. BASIC DETAILS SECTION - Extract from .innerPad div with .schoolInfoCol elements
            try:
                logger.debug(f"   📋 Extracting Basic Details...")

                # Try to find Basic Details section using Selenium elements first
                try:
                    basic_details_elements = self.driver.find_elements(By.CSS_SELECTOR, ".innerPad .schoolInfoCol")
                    if basic_details_elements:
                        logger.debug(f"   Found {len(basic_details_elements)} basic detail elements")

                        # Define field mapping for proper extraction
                        basic_fields_map = {
                            'Location': 'location',
                            'School Category': 'school_category',
                            'Class From': 'class_from',
                            'Class To': 'class_to',
                            'School Type': 'school_type',
                            'Year of Establishment': 'year_of_establishment',
                            'National Management': 'national_management',
                            'State Management': 'state_management',
                            'Affiliation Board Sec.': 'affiliation_board_sec',
                            'Affiliation Board HSec.': 'affiliation_board_hsec'
                        }

                        for element in basic_details_elements:
                            try:
                                # Find the title element within this schoolInfoCol
                                title_element = element.find_element(By.CSS_SELECTOR, ".title p.fw-600")
                                title_text = title_element.text.strip()

                                # Find the corresponding value element
                                value_element = element.find_element(By.CSS_SELECTOR, ".blueCol")
                                value_text = value_element.text.strip()

                                # Map the field to our data structure
                                if title_text in basic_fields_map and value_text:
                                    field_key = basic_fields_map[title_text]
                                    data[field_key] = value_text
                                    logger.debug(f"   Extracted {title_text}: {value_text}")

                            except Exception as e:
                                logger.debug(f"   Error processing basic detail element: {e}")
                                continue

                except Exception as e:
                    logger.debug(f"   Error finding basic details elements: {e}")

                # Fallback: Use regex patterns for basic details
                if data['location'] == 'N/A':
                    location_match = re.search(r'Location</p></div><div[^>]*class="blueCol">([^<]+)', page_text, re.IGNORECASE)
                    if location_match:
                        data['location'] = location_match.group(1).strip()

                if data['school_category'] == 'N/A':
                    category_match = re.search(r'School Category</p></div><div[^>]*class="blueCol">([^<]+)', page_text, re.IGNORECASE)
                    if category_match:
                        data['school_category'] = category_match.group(1).strip()

                if data['school_type'] == 'N/A':
                    type_match = re.search(r'School Type</p></div><div[^>]*class="blueCol">([^<]+)', page_text, re.IGNORECASE)
                    if type_match:
                        data['school_type'] = type_match.group(1).strip()

                if data['year_of_establishment'] == 'N/A':
                    year_match = re.search(r'Year of Establishment</p></div><div[^>]*class="blueCol">([^<]+)', page_text, re.IGNORECASE)
                    if year_match:
                        data['year_of_establishment'] = year_match.group(1).strip()

                # Combine class range if both from and to are found
                if data['class_from'] != 'N/A' and data['class_to'] != 'N/A':
                    data['class_range'] = f"{data['class_from']} To {data['class_to']}"

            except Exception as e:
                logger.debug(f"   Error extracting basic details: {e}")

            # 2. STUDENT ENROLLMENT SECTION
            try:
                logger.debug(f"   👥 Extracting Student Enrollment...")

                # Try to find Student Enrollment section using Selenium elements first
                try:
                    h3_value_elements = self.driver.find_elements(By.CSS_SELECTOR, ".bg-white .H3Value")
                    if h3_value_elements:
                        logger.debug(f"   Found {len(h3_value_elements)} H3Value elements")

                        for element in h3_value_elements:
                            try:
                                # Get the parent container to find the label
                                parent = element.find_element(By.XPATH, "..")
                                parent_text = parent.text.strip().lower()
                                value = element.text.strip()

                                if value.isdigit():
                                    if "total students" in parent_text:
                                        data['total_students'] = value
                                        logger.debug(f"   Found Total Students: {value}")
                                    elif "boys" in parent_text and "total" not in parent_text:
                                        data['total_boys'] = value
                                        logger.debug(f"   Found Boys: {value}")
                                    elif "girls" in parent_text:
                                        data['total_girls'] = value
                                        logger.debug(f"   Found Girls: {value}")
                            except Exception as e:
                                logger.debug(f"   Error processing H3Value element: {e}")
                                continue
                except Exception as e:
                    logger.debug(f"   Error finding H3Value elements: {e}")

                # Fallback: Use regex patterns for student enrollment
                if data['total_students'] == 'N/A':
                    total_students_patterns = [
                        r'Total Students[^>]*</p>\s*<p[^>]*class="H3Value[^>]*>\s*(\d+)\s*</p>',
                        r'Total Students[^>]*>\s*(\d+)\s*<',
                        r'Total Students[:\s]*(\d+)'
                    ]
                    for pattern in total_students_patterns:
                        match = re.search(pattern, page_text, re.IGNORECASE)
                        if match:
                            data['total_students'] = match.group(1).strip()
                            logger.debug(f"   Found Total Students (regex): {data['total_students']}")
                            break

            except Exception as e:
                logger.debug(f"   Error extracting student enrollment: {e}")

            # 3. TEACHER SECTION - Enhanced extraction for the specific HTML structure
            try:
                logger.debug(f"   👨‍🏫 Extracting Teacher data...")

                # Method 1: Look for teacher section with specific structure
                try:
                    # Find teacher section by looking for "Teacher" heading
                    teacher_sections = self.driver.find_elements(By.XPATH, "//h2[contains(text(), 'Teacher')]/following-sibling::div")

                    if teacher_sections:
                        teacher_section = teacher_sections[0]
                        logger.debug(f"   Found teacher section")

                        # Look for H3Value elements within the teacher section
                        h3_elements = teacher_section.find_elements(By.CSS_SELECTOR, ".H3Value")

                        for element in h3_elements:
                            try:
                                # Get the preceding sibling or parent to find the label
                                parent_li = element.find_element(By.XPATH, "ancestor::li[1]")
                                label_text = parent_li.text.strip().lower()
                                value = element.text.strip()

                                if value.isdigit():
                                    if "total teachers" in label_text:
                                        data['total_teachers'] = value
                                        logger.debug(f"   Found Total Teachers: {value}")
                                    elif "male" in label_text and "total" not in label_text and "female" not in label_text:
                                        data['male_teachers'] = value
                                        logger.debug(f"   Found Male Teachers: {value}")
                                    elif "female" in label_text:
                                        data['female_teachers'] = value
                                        logger.debug(f"   Found Female Teachers: {value}")
                            except Exception as e:
                                logger.debug(f"   Error processing teacher element: {e}")
                                continue

                except Exception as e:
                    logger.debug(f"   Error finding teacher section: {e}")

                # Method 2: Fallback - Look for any H3Value elements with teacher context
                if data['total_teachers'] == 'N/A':
                    try:
                        all_h3_elements = self.driver.find_elements(By.CSS_SELECTOR, ".H3Value")

                        for i, element in enumerate(all_h3_elements):
                            try:
                                value = element.text.strip()
                                if not value.isdigit():
                                    continue

                                # Get surrounding context
                                parent_text = ""
                                try:
                                    # Try multiple parent levels to find context
                                    for level in ["../..", "..", "../.."]:
                                        try:
                                            context_element = element.find_element(By.XPATH, level)
                                            context_text = context_element.text.lower()
                                            if "teacher" in context_text:
                                                parent_text = context_text
                                                break
                                        except:
                                            continue
                                except:
                                    pass

                                # Also check if this is in a teacher-related section by looking at nearby elements
                                if not parent_text:
                                    try:
                                        # Look for teacher-related text in nearby elements
                                        nearby_elements = self.driver.find_elements(By.XPATH, f"//p[contains(@class, 'H3Value')][{i+1}]/preceding::*[position()<=5] | //p[contains(@class, 'H3Value')][{i+1}]/following::*[position()<=5]")
                                        for nearby in nearby_elements:
                                            if "teacher" in nearby.text.lower():
                                                parent_text = nearby.text.lower()
                                                break
                                    except:
                                        pass

                                # Assign based on context and position
                                if "total teachers" in parent_text:
                                    data['total_teachers'] = value
                                    logger.debug(f"   Found Total Teachers (fallback): {value}")
                                elif "male" in parent_text and "teacher" in parent_text:
                                    data['male_teachers'] = value
                                    logger.debug(f"   Found Male Teachers (fallback): {value}")
                                elif "female" in parent_text and "teacher" in parent_text:
                                    data['female_teachers'] = value
                                    logger.debug(f"   Found Female Teachers (fallback): {value}")
                                elif "teacher" in parent_text and data['total_teachers'] == 'N/A':
                                    # If we find a teacher-related number and don't have total yet, assume it's total
                                    data['total_teachers'] = value
                                    logger.debug(f"   Found Total Teachers (assumed): {value}")

                            except Exception as e:
                                logger.debug(f"   Error processing H3Value element {i}: {e}")
                                continue

                    except Exception as e:
                        logger.debug(f"   Error in fallback teacher extraction: {e}")

                # Method 3: Enhanced CSS Selector approach for teacher data (IMPROVED)
                if data['total_teachers'] == 'N/A' or data['male_teachers'] == 'N/A' or data['female_teachers'] == 'N/A':
                    try:
                        logger.debug(f"   🎯 Using enhanced CSS selectors for teacher data...")

                        # First, try to find the teacher section specifically
                        teacher_section_found = False
                        try:
                            # Look for the teacher section by the header
                            teacher_headers = self.driver.find_elements(By.XPATH, "//h2[contains(text(), 'Teacher')]")
                            if teacher_headers:
                                teacher_section_found = True
                                logger.debug(f"   Found teacher section header")

                                # Get the teacher section container
                                teacher_section = teacher_headers[0].find_element(By.XPATH, "following-sibling::div[1]")

                                # Extract teacher data using robust selectors within the teacher section
                                teacher_data_mappings = [
                                    ("Total Teachers", 'total_teachers'),
                                    ("Male", 'male_teachers'),
                                    ("Female", 'female_teachers')
                                ]

                                for label_text, field_name in teacher_data_mappings:
                                    if data[field_name] == 'N/A':
                                        try:
                                            # Method 3a: Find by label text and get the following H3Value
                                            label_elements = teacher_section.find_elements(By.XPATH, f".//p[contains(@class, 'fontTitle15') and contains(text(), '{label_text}')]")
                                            for label_element in label_elements:
                                                try:
                                                    # Get the next sibling p element with H3Value class
                                                    value_element = label_element.find_element(By.XPATH, "following-sibling::p[contains(@class, 'H3Value')]")
                                                    value = value_element.text.strip()
                                                    if value.isdigit():
                                                        data[field_name] = value
                                                        logger.debug(f"   Found {field_name} (label-based): {value}")
                                                        break
                                                except Exception as e:
                                                    logger.debug(f"   Error getting value for {label_text}: {e}")
                                                    continue
                                        except Exception as e:
                                            logger.debug(f"   Error finding label for {field_name}: {e}")
                        except Exception as e:
                            logger.debug(f"   Error finding teacher section: {e}")

                        # Method 3b: Fallback CSS selectors if teacher section approach didn't work
                        if not teacher_section_found or data['total_teachers'] == 'N/A' or data['male_teachers'] == 'N/A' or data['female_teachers'] == 'N/A':
                            logger.debug(f"   Trying fallback CSS selectors...")

                            # Enhanced CSS selectors based on the provided HTML structure
                            teacher_selectors = [
                                # Specific selectors for the teacher section structure
                                (".greyInfoList li:nth-child(1) .H3Value", 'total_teachers'),  # First li = Total Teachers
                                (".greyInfoList li:nth-child(2) .H3Value", 'male_teachers'),   # Second li = Male
                                (".greyInfoList li:nth-child(3) .H3Value", 'female_teachers'), # Third li = Female

                                # More specific selectors
                                ("ul.greyInfoList li:first-child p.H3Value", 'total_teachers'),
                                ("ul.greyInfoList li:nth-child(2) p.H3Value", 'male_teachers'),
                                ("ul.greyInfoList li:last-child p.H3Value", 'female_teachers'),
                            ]

                            for selector, field_name in teacher_selectors:
                                if data[field_name] == 'N/A':
                                    try:
                                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                                        for element in elements:
                                            value = element.text.strip()
                                            if value.isdigit():
                                                data[field_name] = value
                                                logger.debug(f"   Found {field_name} (CSS): {value}")
                                                break
                                    except Exception as e:
                                        logger.debug(f"   CSS selector failed for {field_name}: {e}")
                                        continue

                    except Exception as e:
                        logger.debug(f"   Error in CSS selector teacher extraction: {e}")

                # Method 4: XPath-based extraction for teacher data (NEW)
                if data['total_teachers'] == 'N/A' or data['male_teachers'] == 'N/A' or data['female_teachers'] == 'N/A':
                    try:
                        logger.debug(f"   🎯 Using XPath selectors for teacher data...")

                        # XPath selectors based on the HTML structure
                        xpath_selectors = [
                            # Find Total Teachers by text content
                            ("//p[contains(@class, 'fontTitle15') and contains(text(), 'Total Teachers')]/following-sibling::p[contains(@class, 'H3Value')]", 'total_teachers'),
                            # Find Male by text content (excluding "Total" and "Female")
                            ("//p[contains(@class, 'fontTitle15') and text()='Male']/following-sibling::p[contains(@class, 'H3Value')]", 'male_teachers'),
                            # Find Female by text content
                            ("//p[contains(@class, 'fontTitle15') and text()='Female']/following-sibling::p[contains(@class, 'H3Value')]", 'female_teachers'),

                            # Alternative XPath approaches
                            ("//h2[contains(text(), 'Teacher')]/following-sibling::div//li[1]//p[contains(@class, 'H3Value')]", 'total_teachers'),
                            ("//h2[contains(text(), 'Teacher')]/following-sibling::div//li[2]//p[contains(@class, 'H3Value')]", 'male_teachers'),
                            ("//h2[contains(text(), 'Teacher')]/following-sibling::div//li[3]//p[contains(@class, 'H3Value')]", 'female_teachers'),
                        ]

                        for xpath, field_name in xpath_selectors:
                            if data[field_name] == 'N/A':
                                try:
                                    elements = self.driver.find_elements(By.XPATH, xpath)
                                    for element in elements:
                                        value = element.text.strip()
                                        if value.isdigit():
                                            data[field_name] = value
                                            logger.debug(f"   Found {field_name} (XPath): {value}")
                                            break
                                except Exception as e:
                                    logger.debug(f"   XPath selector failed for {field_name}: {e}")
                                    continue

                    except Exception as e:
                        logger.debug(f"   Error in XPath teacher extraction: {e}")

                # Method 5: Regex fallback for teacher data (Enhanced patterns)
                if data['total_teachers'] == 'N/A' or data['male_teachers'] == 'N/A' or data['female_teachers'] == 'N/A':
                    try:
                        # Enhanced regex patterns based on the HTML structure
                        teacher_patterns = [
                            # Specific patterns for the Angular-generated HTML structure
                            (r'<p[^>]*class="fontTitle15[^>]*>Total Teachers</p>\s*<p[^>]*class="H3Value[^>]*>\s*(\d+)\s*</p>', 'total_teachers'),
                            (r'<p[^>]*class="fontTitle15[^>]*>Male</p>\s*<p[^>]*class="H3Value[^>]*>\s*(\d+)\s*</p>', 'male_teachers'),
                            (r'<p[^>]*class="fontTitle15[^>]*>Female</p>\s*<p[^>]*class="H3Value[^>]*>\s*(\d+)\s*</p>', 'female_teachers'),

                            # More flexible patterns that handle whitespace and attributes
                            (r'fontTitle15[^>]*>\s*Total Teachers\s*</p>\s*<p[^>]*H3Value[^>]*>\s*(\d+)\s*</p>', 'total_teachers'),
                            (r'fontTitle15[^>]*>\s*Male\s*</p>\s*<p[^>]*H3Value[^>]*>\s*(\d+)\s*</p>', 'male_teachers'),
                            (r'fontTitle15[^>]*>\s*Female\s*</p>\s*<p[^>]*H3Value[^>]*>\s*(\d+)\s*</p>', 'female_teachers'),

                            # Original patterns (kept for backward compatibility)
                            (r'Total Teachers[^>]*</p>\s*<p[^>]*class="H3Value[^>]*>\s*(\d+)\s*</p>', 'total_teachers'),
                            (r'Male[^>]*</p>\s*<p[^>]*class="H3Value[^>]*>\s*(\d+)\s*</p>', 'male_teachers'),
                            (r'Female[^>]*</p>\s*<p[^>]*class="H3Value[^>]*>\s*(\d+)\s*</p>', 'female_teachers'),

                            # Fallback patterns
                            (r'Total Teachers[:\s]*(\d+)', 'total_teachers'),
                            (r'(?<!Fe)Male[:\s]*(\d+)', 'male_teachers'),  # Negative lookbehind to avoid matching "Female"
                            (r'Female[:\s]*(\d+)', 'female_teachers'),
                        ]

                        for pattern, field_name in teacher_patterns:
                            if data[field_name] == 'N/A':
                                match = re.search(pattern, page_text, re.IGNORECASE | re.DOTALL)
                                if match:
                                    data[field_name] = match.group(1).strip()
                                    logger.debug(f"   Found {field_name} (regex): {data[field_name]}")

                    except Exception as e:
                        logger.debug(f"   Error in regex teacher extraction: {e}")

            except Exception as e:
                logger.debug(f"   Error extracting teacher data: {e}")

            # TEACHER DATA CALCULATION FALLBACK
            try:
                logger.debug(f"   🧮 Applying teacher calculation fallback...")

                # If we have total and male teachers but missing female, calculate it
                if (data['total_teachers'] != 'N/A' and data['male_teachers'] != 'N/A' and
                    data['female_teachers'] == 'N/A'):
                    try:
                        total_teachers = int(data['total_teachers'])
                        male_teachers = int(data['male_teachers'])
                        calculated_female = total_teachers - male_teachers

                        if calculated_female >= 0:
                            data['female_teachers'] = str(calculated_female)
                            logger.debug(f"   Calculated Female Teachers: {calculated_female} (Total: {total_teachers} - Male: {male_teachers})")
                        else:
                            logger.debug(f"   Invalid calculation: Total({total_teachers}) - Male({male_teachers}) = {calculated_female}")
                    except ValueError as e:
                        logger.debug(f"   Error in teacher calculation: {e}")

                # If we have total and female teachers but missing male, calculate it
                elif (data['total_teachers'] != 'N/A' and data['female_teachers'] != 'N/A' and
                      data['male_teachers'] == 'N/A'):
                    try:
                        total_teachers = int(data['total_teachers'])
                        female_teachers = int(data['female_teachers'])
                        calculated_male = total_teachers - female_teachers

                        if calculated_male >= 0:
                            data['male_teachers'] = str(calculated_male)
                            logger.debug(f"   Calculated Male Teachers: {calculated_male} (Total: {total_teachers} - Female: {female_teachers})")
                        else:
                            logger.debug(f"   Invalid calculation: Total({total_teachers}) - Female({female_teachers}) = {calculated_male}")
                    except ValueError as e:
                        logger.debug(f"   Error in teacher calculation: {e}")

            except Exception as e:
                logger.debug(f"   Error in teacher calculation fallback: {e}")

            # 4. SCHOOL NAME - Extract from page title, header, or breadcrumb
            try:
                logger.debug(f"   🏫 Extracting School Name...")

                # Method 1: Try to get school name from page title
                page_title = self.driver.title
                if page_title and page_title != "Know Your School" and "UDISE" not in page_title:
                    clean_title = page_title.replace("Know Your School", "").replace("-", "").strip()
                    if clean_title and len(clean_title) > 3:
                        data['detail_school_name'] = clean_title
                        logger.debug(f"   Found school name from title: {clean_title}")

                # Fallback: Use school ID as identifier
                if data['detail_school_name'] == 'N/A':
                    data['detail_school_name'] = f"School_ID_{expected_school_id}"
                    logger.debug(f"   Using school ID as name: {data['detail_school_name']}")

            except Exception as e:
                logger.debug(f"   Error extracting school name: {e}")
                data['detail_school_name'] = f"School_ID_{expected_school_id}"

            # COMPREHENSIVE DATA VALIDATION AND STATUS INDICATORS
            try:
                logger.debug(f"   📊 Validating extracted data...")

                # Count successfully extracted fields
                extracted_fields = 0
                critical_fields = 0

                # Critical fields for Phase 2
                if data['total_students'] != 'N/A':
                    critical_fields += 1
                    extracted_fields += 1
                if data['total_teachers'] != 'N/A':
                    critical_fields += 1
                    extracted_fields += 1
                if data['detail_school_name'] != 'N/A' and not data['detail_school_name'].startswith('School_ID_'):
                    extracted_fields += 1

                # Additional fields
                additional_fields = [
                    'total_boys', 'total_girls', 'male_teachers', 'female_teachers',
                    'school_category', 'school_type', 'location', 'academic_year'
                ]
                for field in additional_fields:
                    if data[field] != 'N/A':
                        extracted_fields += 1

                # Add extraction status indicators
                data['extraction_status'] = 'SUCCESS' if critical_fields >= 2 else 'PARTIAL' if critical_fields >= 1 else 'FAILED'
                data['fields_extracted'] = extracted_fields
                data['critical_fields_extracted'] = critical_fields

                # Validation summary
                if critical_fields >= 2:
                    logger.info(f"✅ EXCELLENT extraction")
                    logger.info(f"   🎯 Critical fields: {critical_fields}/2, Total fields: {extracted_fields}")
                    logger.info(f"   👥 Students: {data['total_students']}, Teachers: {data['total_teachers']}")
                elif critical_fields >= 1:
                    logger.info(f"⚠️ PARTIAL extraction")
                    logger.info(f"   🎯 Critical fields: {critical_fields}/2, Total fields: {extracted_fields}")
                else:
                    logger.warning(f"❌ FAILED extraction")
                    logger.warning(f"   🎯 Critical fields: {critical_fields}/2, Total fields: {extracted_fields}")

            except Exception as e:
                logger.debug(f"   Error in data validation: {e}")
                data['extraction_status'] = 'ERROR'
                data['fields_extracted'] = 0
                data['critical_fields_extracted'] = 0

            return data

        except Exception as e:
            logger.error(f"   ❌ Error in extract_data_from_page: {e}")
            return None

    def create_thread_driver(self, thread_id):
        """Create a WebDriver instance for a specific thread"""
        try:
            # Setup Chrome options for this thread
            options = ChromeOptions()

            # Core stability options
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-blink-features=AutomationControlled")

            # Performance optimizations
            options.add_argument("--disable-images")
            options.add_argument("--disable-plugins")

            # Memory and resource optimizations
            options.add_argument("--memory-pressure-off")
            options.add_argument("--max_old_space_size=4096")

            # Additional options for stability in multithreading
            options.add_argument("--disable-web-security")
            options.add_argument("--disable-features=VizDisplayCompositor")

            # Create thread-specific driver
            thread_driver = webdriver.Chrome(options=options)
            thread_driver.maximize_window()
            thread_driver.implicitly_wait(5)
            thread_driver.set_page_load_timeout(25)

            logger.info(f"🧵 Thread {thread_id}: WebDriver initialized")
            return thread_driver

        except Exception as e:
            logger.error(f"🧵 Thread {thread_id}: ❌ Failed to create WebDriver: {e}")
            return None

    def worker_process_schools_batch(self, schools_batch, thread_id):
        """Optimized worker function that processes multiple schools with a single WebDriver instance"""
        thread_driver = None
        processed_in_thread = 0
        success_in_thread = 0
        fail_in_thread = 0

        try:
            # Initialize WebDriver once for this thread
            thread_driver = self.create_thread_driver(thread_id)
            if not thread_driver:
                logger.error(f"🧵 Thread {thread_id}: Failed to initialize WebDriver")
                # Update stats for all schools in this batch as failed
                self.update_stats(processed=len(schools_batch), fail=len(schools_batch))
                return False

            logger.info(f"🧵 Thread {thread_id}: Starting batch processing of {len(schools_batch)} schools")

            # Process each school in the batch using the same WebDriver
            for school_data in schools_batch:
                try:
                    # Extract school information
                    school_name = school_data.get('school_name', f'School_{thread_id}')
                    udise_code = school_data.get('udise_code', f'UDISE_{thread_id}')
                    know_more_link = school_data.get('know_more_link', '')
                    processing_index = school_data.get('processing_index', 0)

                    logger.info(f"🧵 Thread {thread_id}: Processing school {processing_index} - {school_name}")
                    logger.debug(f"🧵 Thread {thread_id}: UDISE Code: {udise_code}")

                    # Check if already processed (crash recovery)
                    if self.check_already_processed(udise_code):
                        logger.info(f"🧵 Thread {thread_id}: Already processed - skipping")
                        processed_in_thread += 1
                        continue

                    # Extract Phase 2 data using the persistent thread driver
                    extracted_data = self.extract_focused_data_with_driver(thread_driver, know_more_link)

                    if extracted_data:
                        # Combine original Phase 1 data with extracted Phase 2 data
                        combined_data = school_data.copy()
                        combined_data.update(extracted_data)

                        # Extract pin code from address if not available in pin_code field (NEW)
                        pin_code_value = school_data.get('pin_code', 'N/A')
                        address = school_data.get('address', '')

                        if pin_code_value in ['N/A', '', None] or pd.isna(pin_code_value):
                            # Try to extract pin code from address field
                            if address and address != 'N/A':
                                # Look for pin code patterns in address
                                pin_match = re.search(r'(?:pin|PIN)\s*[:\-]?\s*(\d{6})', address)
                                if not pin_match:
                                    # Look for 6-digit numbers at the end of address
                                    pin_match = re.search(r'\b(\d{6})\b', address)

                                if pin_match:
                                    extracted_pin = pin_match.group(1)
                                    combined_data['pin_code'] = extracted_pin
                                    logger.debug(f"🧵 Thread {thread_id}: Pin code extracted from address: {extracted_pin}")
                                else:
                                    combined_data['pin_code'] = 'N/A'
                                    logger.debug(f"🧵 Thread {thread_id}: No pin code found in address")
                            else:
                                combined_data['pin_code'] = 'N/A'
                        else:
                            combined_data['pin_code'] = pin_code_value
                            logger.debug(f"🧵 Thread {thread_id}: Pin code preserved from input: {pin_code_value}")

                        # Ensure academic year is set to 2025-26 (NEW)
                        combined_data['academic_year'] = '2025-26'

                        # Remove unwanted columns
                        unwanted_columns = ['last_modified', 'source_url', 'processing_index']
                        for col in unwanted_columns:
                            combined_data.pop(col, None)

                        # Write immediately to output CSV (thread-safe)
                        if self.write_to_output_csv(combined_data):
                            success_in_thread += 1
                            logger.info(f"🧵 Thread {thread_id}: ✅ Successfully processed and saved")
                        else:
                            logger.error(f"🧵 Thread {thread_id}: ❌ Failed to save to CSV")
                            fail_in_thread += 1
                    else:
                        logger.warning(f"🧵 Thread {thread_id}: ⚠️ Failed to extract Phase 2 data")

                        # Still save the original Phase 1 data with extraction failure markers
                        combined_data = school_data.copy()
                        combined_data.update({
                            'extraction_status': 'FAILED',
                            'extraction_timestamp': datetime.now().isoformat(),
                            'fields_extracted': 0,
                            'critical_fields_extracted': 0
                        })

                        # Extract pin code from address if not available in pin_code field (NEW)
                        pin_code_value = school_data.get('pin_code', 'N/A')
                        address = school_data.get('address', '')

                        if pin_code_value in ['N/A', '', None] or pd.isna(pin_code_value):
                            # Try to extract pin code from address field
                            if address and address != 'N/A':
                                # Look for pin code patterns in address
                                pin_match = re.search(r'(?:pin|PIN)\s*[:\-]?\s*(\d{6})', address)
                                if not pin_match:
                                    # Look for 6-digit numbers at the end of address
                                    pin_match = re.search(r'\b(\d{6})\b', address)

                                if pin_match:
                                    extracted_pin = pin_match.group(1)
                                    combined_data['pin_code'] = extracted_pin
                                    logger.debug(f"🧵 Thread {thread_id}: Pin code extracted from address (failed case): {extracted_pin}")
                                else:
                                    combined_data['pin_code'] = 'N/A'
                                    logger.debug(f"🧵 Thread {thread_id}: No pin code found in address (failed case)")
                            else:
                                combined_data['pin_code'] = 'N/A'
                        else:
                            combined_data['pin_code'] = pin_code_value
                            logger.debug(f"🧵 Thread {thread_id}: Pin code preserved from input (failed case): {pin_code_value}")

                        # Ensure academic year is set to 2025-26 (NEW)
                        combined_data['academic_year'] = '2025-26'

                        # Remove unwanted columns
                        unwanted_columns = ['last_modified', 'source_url', 'processing_index']
                        for col in unwanted_columns:
                            combined_data.pop(col, None)

                        if self.write_to_output_csv(combined_data):
                            logger.info(f"🧵 Thread {thread_id}: 📝 Saved with extraction failure markers")

                        fail_in_thread += 1

                    processed_in_thread += 1

                    # Brief pause between schools to avoid overwhelming the server
                    time.sleep(1)

                except Exception as school_error:
                    logger.error(f"🧵 Thread {thread_id}: ❌ Error processing school {processing_index}: {school_error}")

                    # Check if WebDriver is still responsive
                    try:
                        thread_driver.current_url  # Simple check to see if driver is responsive
                    except Exception:
                        logger.warning(f"🧵 Thread {thread_id}: WebDriver became unresponsive, recreating...")
                        try:
                            thread_driver.quit()
                        except:
                            pass

                        # Recreate WebDriver
                        thread_driver = self.create_thread_driver(thread_id)
                        if not thread_driver:
                            logger.error(f"🧵 Thread {thread_id}: Failed to recreate WebDriver, aborting batch")
                            fail_in_thread += len(schools_batch) - processed_in_thread
                            break

                    fail_in_thread += 1
                    processed_in_thread += 1
                    continue

            # Update global statistics
            self.update_stats(processed=processed_in_thread, success=success_in_thread, fail=fail_in_thread)

            logger.info(f"🧵 Thread {thread_id}: Completed batch - Processed: {processed_in_thread}, Success: {success_in_thread}, Failed: {fail_in_thread}")
            return True

        except Exception as e:
            logger.error(f"🧵 Thread {thread_id}: ❌ Critical error in batch processing: {e}")
            # Update stats for any remaining unprocessed schools
            remaining = len(schools_batch) - processed_in_thread
            if remaining > 0:
                self.update_stats(processed=remaining, fail=remaining)
            return False

        finally:
            # Always cleanup thread-specific driver
            if thread_driver:
                try:
                    thread_driver.quit()
                    logger.info(f"🧵 Thread {thread_id}: WebDriver closed after batch completion")
                except Exception as e:
                    logger.debug(f"🧵 Thread {thread_id}: Error closing WebDriver: {e}")

    def extract_focused_data_with_driver(self, driver, url, max_retries=2):
        """Extract comprehensive data from school detail page using provided driver"""
        for attempt in range(max_retries):
            try:
                logger.debug(f"🌐 Navigating to school detail page: {url}")

                # IMMEDIATE BROWSER REFRESH: Navigate and immediately refresh
                try:
                    # Step 1: Navigate to the URL
                    driver.get(url)
                    logger.debug(f"   📍 Initial navigation completed")

                    # Step 2: IMMEDIATE REFRESH as requested
                    logger.debug(f"   🔄 Performing IMMEDIATE browser refresh...")
                    driver.refresh()

                    # Step 3: Wait for refresh to complete
                    time.sleep(4)  # Increased wait for refresh completion

                    # Step 4: Verify page is loaded
                    WebDriverWait(driver, 10).until(
                        lambda d: d.execute_script("return document.readyState") == "complete"
                    )

                    # Step 5: Additional wait for dynamic content
                    time.sleep(2)

                    logger.debug(f"   ✅ Page refreshed and loaded successfully")

                except Exception as e:
                    logger.error(f"   ❌ Navigation/refresh error: {e}")
                    if attempt < max_retries - 1:
                        continue
                    return None

                # Initialize comprehensive data structure for all extracted fields
                data = {
                    # School identification
                    'detail_school_name': 'N/A',
                    'extraction_timestamp': datetime.now().isoformat(),

                    # Header information (NEW)
                    'edu_district': 'N/A',
                    'edu_block': 'N/A',

                    # Basic Details section
                    'academic_year': '2025-26',
                    'location': 'N/A',
                    'school_category': 'N/A',
                    'class_from': 'N/A',
                    'class_to': 'N/A',
                    'class_range': 'N/A',
                    'school_type': 'N/A',
                    'year_of_establishment': 'N/A',
                    'national_management': 'N/A',
                    'state_management': 'N/A',
                    'affiliation_board_sec': 'N/A',
                    'affiliation_board_hsec': 'N/A',

                    # Student Enrollment section
                    'total_students': 'N/A',
                    'total_boys': 'N/A',
                    'total_girls': 'N/A',
                    'enrollment_class_range': 'N/A',

                    # Teacher section
                    'total_teachers': 'N/A',
                    'male_teachers': 'N/A',
                    'female_teachers': 'N/A'
                }

                # Get page content for extraction
                page_text = driver.page_source

                # Extract school ID for verification
                url_school_id = re.search(r'/(\d+)/\d+$', url)
                expected_school_id = url_school_id.group(1) if url_school_id else "unknown"

                logger.debug(f"   📄 Expected school ID: {expected_school_id}")
                logger.debug(f"   📄 Page content length: {len(page_text)} characters")

                # Continue with data extraction using the provided driver
                return self.extract_data_from_page_with_driver(driver, data, page_text, expected_school_id)

            except Exception as e:
                logger.warning(f"⚠️ Failed to extract data from {url} (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    logger.info(f"⏳ Retrying in 3 seconds...")
                    time.sleep(3)
                else:
                    return None

        return None

    def extract_data_from_page_with_driver(self, driver, data, page_text, expected_school_id):
        """Extract data from the loaded page using provided driver"""
        try:
            # 0. HEADER SECTION - Extract Educational District and Block (NEW)
            try:
                logger.debug(f"   🏛️ Extracting Header Information (Educational District & Block)...")

                # Method 1: Try to find header section using Selenium elements
                try:
                    # Look for the header section with State, District, Block information
                    header_elements = driver.find_elements(By.CSS_SELECTOR, ".col-sm-12 p.h4")

                    for element in header_elements:
                        element_text = element.text.strip()
                        logger.debug(f"   Found header element: {element_text}")

                        # Look for District and Block information in the same element
                        if "District :" in element_text and "Block :" in element_text:
                            # Extract Educational District
                            district_match = re.search(r'District\s*:\s*([^|]+)', element_text)
                            if district_match:
                                data['edu_district'] = district_match.group(1).strip()
                                logger.debug(f"   Found Educational District: {data['edu_district']}")

                            # Extract Educational Block
                            block_match = re.search(r'Block\s*:\s*(.+)$', element_text)
                            if block_match:
                                data['edu_block'] = block_match.group(1).strip()
                                logger.debug(f"   Found Educational Block: {data['edu_block']}")

                            break

                except Exception as e:
                    logger.debug(f"   Error finding header elements: {e}")

                # Method 2: Fallback - Use regex patterns on page source
                if data['edu_district'] == 'N/A' or data['edu_block'] == 'N/A':
                    try:
                        # Pattern for Educational District
                        if data['edu_district'] == 'N/A':
                            district_patterns = [
                                r'District\s*:\s*</span><span[^>]*class="blueCol[^>]*>([^<]+)</span>',
                                r'District\s*:\s*([^|]+)\|',
                                r'District\s*:\s*([^<]+)<'
                            ]
                            for pattern in district_patterns:
                                match = re.search(pattern, page_text, re.IGNORECASE)
                                if match:
                                    data['edu_district'] = match.group(1).strip()
                                    logger.debug(f"   Found Educational District (regex): {data['edu_district']}")
                                    break

                        # Pattern for Educational Block
                        if data['edu_block'] == 'N/A':
                            block_patterns = [
                                r'Block\s*:\s*</span><span[^>]*class="blueCol[^>]*>([^<]+)</span>',
                                r'Block\s*:\s*([^<]+)</p>',
                                r'Block\s*:\s*([^<]+)$'
                            ]
                            for pattern in block_patterns:
                                match = re.search(pattern, page_text, re.IGNORECASE | re.MULTILINE)
                                if match:
                                    data['edu_block'] = match.group(1).strip()
                                    logger.debug(f"   Found Educational Block (regex): {data['edu_block']}")
                                    break

                    except Exception as e:
                        logger.debug(f"   Error in regex header extraction: {e}")

            except Exception as e:
                logger.debug(f"   Error extracting header information: {e}")

            # 1. BASIC DETAILS SECTION - Extract from .innerPad div with .schoolInfoCol elements
            try:
                logger.debug(f"   📋 Extracting Basic Details...")

                # Try to find Basic Details section using Selenium elements first
                try:
                    basic_details_elements = driver.find_elements(By.CSS_SELECTOR, ".innerPad .schoolInfoCol")
                    if basic_details_elements:
                        logger.debug(f"   Found {len(basic_details_elements)} basic detail elements")

                        # Define field mapping for proper extraction
                        basic_fields_map = {
                            'Location': 'location',
                            'School Category': 'school_category',
                            'Class From': 'class_from',
                            'Class To': 'class_to',
                            'School Type': 'school_type',
                            'Year of Establishment': 'year_of_establishment',
                            'National Management': 'national_management',
                            'State Management': 'state_management',
                            'Affiliation Board Sec.': 'affiliation_board_sec',
                            'Affiliation Board HSec.': 'affiliation_board_hsec'
                        }

                        for element in basic_details_elements:
                            try:
                                # Find the title element within this schoolInfoCol
                                title_element = element.find_element(By.CSS_SELECTOR, ".title p.fw-600")
                                title_text = title_element.text.strip()

                                # Find the corresponding value element
                                value_element = element.find_element(By.CSS_SELECTOR, ".blueCol")
                                value_text = value_element.text.strip()

                                # Map the field to our data structure
                                if title_text in basic_fields_map and value_text:
                                    field_key = basic_fields_map[title_text]
                                    data[field_key] = value_text
                                    logger.debug(f"   Extracted {title_text}: {value_text}")

                            except Exception as e:
                                logger.debug(f"   Error processing basic detail element: {e}")
                                continue

                except Exception as e:
                    logger.debug(f"   Error finding basic details elements: {e}")

                # Fallback: Use regex patterns for basic details
                if data['location'] == 'N/A':
                    location_match = re.search(r'Location</p></div><div[^>]*class="blueCol">([^<]+)', page_text, re.IGNORECASE)
                    if location_match:
                        data['location'] = location_match.group(1).strip()

                if data['school_category'] == 'N/A':
                    category_match = re.search(r'School Category</p></div><div[^>]*class="blueCol">([^<]+)', page_text, re.IGNORECASE)
                    if category_match:
                        data['school_category'] = category_match.group(1).strip()

                if data['school_type'] == 'N/A':
                    type_match = re.search(r'School Type</p></div><div[^>]*class="blueCol">([^<]+)', page_text, re.IGNORECASE)
                    if type_match:
                        data['school_type'] = type_match.group(1).strip()

                if data['year_of_establishment'] == 'N/A':
                    year_match = re.search(r'Year of Establishment</p></div><div[^>]*class="blueCol">([^<]+)', page_text, re.IGNORECASE)
                    if year_match:
                        data['year_of_establishment'] = year_match.group(1).strip()

                # Combine class range if both from and to are found
                if data['class_from'] != 'N/A' and data['class_to'] != 'N/A':
                    data['class_range'] = f"{data['class_from']} To {data['class_to']}"

            except Exception as e:
                logger.debug(f"   Error extracting basic details: {e}")

            # Continue with student enrollment and teacher extraction...
            # (This method will be similar to the original extract_data_from_page but uses the provided driver)
            return self.extract_remaining_data_with_driver(driver, data, page_text, expected_school_id)

        except Exception as e:
            logger.error(f"   ❌ Error in extract_data_from_page_with_driver: {e}")
            return None

    def extract_remaining_data_with_driver(self, driver, data, page_text, expected_school_id):
        """Extract student enrollment, teacher data, and school name using provided driver"""
        try:
            # 2. STUDENT ENROLLMENT SECTION
            try:
                logger.debug(f"   👥 Extracting Student Enrollment...")

                # Try to find Student Enrollment section using Selenium elements first
                try:
                    h3_value_elements = driver.find_elements(By.CSS_SELECTOR, ".bg-white .H3Value")
                    if h3_value_elements:
                        logger.debug(f"   Found {len(h3_value_elements)} H3Value elements")

                        for element in h3_value_elements:
                            try:
                                # Get the parent container to find the label
                                parent = element.find_element(By.XPATH, "..")
                                parent_text = parent.text.strip().lower()
                                value = element.text.strip()

                                if value.isdigit():
                                    if "total students" in parent_text:
                                        data['total_students'] = value
                                        logger.debug(f"   Found Total Students: {value}")
                                    elif "boys" in parent_text and "total" not in parent_text:
                                        data['total_boys'] = value
                                        logger.debug(f"   Found Boys: {value}")
                                    elif "girls" in parent_text:
                                        data['total_girls'] = value
                                        logger.debug(f"   Found Girls: {value}")
                            except Exception as e:
                                logger.debug(f"   Error processing H3Value element: {e}")
                                continue
                except Exception as e:
                    logger.debug(f"   Error finding H3Value elements: {e}")

                # Fallback: Use regex patterns for student enrollment
                if data['total_students'] == 'N/A':
                    total_students_patterns = [
                        r'Total Students[^>]*</p>\s*<p[^>]*class="H3Value[^>]*>\s*(\d+)\s*</p>',
                        r'Total Students[^>]*>\s*(\d+)\s*<',
                        r'Total Students[:\s]*(\d+)'
                    ]
                    for pattern in total_students_patterns:
                        match = re.search(pattern, page_text, re.IGNORECASE)
                        if match:
                            data['total_students'] = match.group(1).strip()
                            logger.debug(f"   Found Total Students (regex): {data['total_students']}")
                            break

            except Exception as e:
                logger.debug(f"   Error extracting student enrollment: {e}")

            # 3. TEACHER SECTION - Enhanced extraction for the specific HTML structure
            try:
                logger.debug(f"   👨‍🏫 Extracting Teacher data...")

                # Method 1: Look for teacher section with specific structure
                try:
                    # Find teacher section by looking for "Teacher" heading
                    teacher_sections = driver.find_elements(By.XPATH, "//h2[contains(text(), 'Teacher')]/following-sibling::div")

                    if teacher_sections:
                        teacher_section = teacher_sections[0]
                        logger.debug(f"   Found teacher section")

                        # Look for H3Value elements within the teacher section
                        h3_elements = teacher_section.find_elements(By.CSS_SELECTOR, ".H3Value")

                        for element in h3_elements:
                            try:
                                # Get the preceding sibling or parent to find the label
                                parent_li = element.find_element(By.XPATH, "ancestor::li[1]")
                                label_text = parent_li.text.strip().lower()
                                value = element.text.strip()

                                if value.isdigit():
                                    if "total teachers" in label_text:
                                        data['total_teachers'] = value
                                        logger.debug(f"   Found Total Teachers: {value}")
                                    elif "male" in label_text and "total" not in label_text and "female" not in label_text:
                                        data['male_teachers'] = value
                                        logger.debug(f"   Found Male Teachers: {value}")
                                    elif "female" in label_text and "male" not in label_text:
                                        data['female_teachers'] = value
                                        logger.debug(f"   Found Female Teachers: {value}")
                            except Exception as e:
                                logger.debug(f"   Error processing teacher element: {e}")
                                continue

                except Exception as e:
                    logger.debug(f"   Error finding teacher section: {e}")

                # Method 2: Fallback - Look for any H3Value elements with teacher context
                if data['total_teachers'] == 'N/A':
                    try:
                        all_h3_elements = driver.find_elements(By.CSS_SELECTOR, ".H3Value")

                        for i, element in enumerate(all_h3_elements):
                            try:
                                value = element.text.strip()
                                if not value.isdigit():
                                    continue

                                # Get surrounding context
                                parent_text = ""
                                try:
                                    # Try multiple parent levels to find context
                                    for level in ["../..", "..", "../.."]:
                                        try:
                                            context_element = element.find_element(By.XPATH, level)
                                            context_text = context_element.text.lower()
                                            if "teacher" in context_text:
                                                parent_text = context_text
                                                break
                                        except:
                                            continue
                                except:
                                    pass

                                # Assign based on context and position
                                if "total teachers" in parent_text:
                                    data['total_teachers'] = value
                                    logger.debug(f"   Found Total Teachers (fallback): {value}")
                                elif "male" in parent_text and "teacher" in parent_text:
                                    data['male_teachers'] = value
                                    logger.debug(f"   Found Male Teachers (fallback): {value}")
                                elif "female" in parent_text and "teacher" in parent_text:
                                    data['female_teachers'] = value
                                    logger.debug(f"   Found Female Teachers (fallback): {value}")
                                elif "teacher" in parent_text and data['total_teachers'] == 'N/A':
                                    # If we find a teacher-related number and don't have total yet, assume it's total
                                    data['total_teachers'] = value
                                    logger.debug(f"   Found Total Teachers (assumed): {value}")

                            except Exception as e:
                                logger.debug(f"   Error processing H3Value element {i}: {e}")
                                continue

                    except Exception as e:
                        logger.debug(f"   Error in fallback teacher extraction: {e}")

            except Exception as e:
                logger.debug(f"   Error extracting teacher data: {e}")

            # Method 3: Enhanced CSS Selector approach for teacher data (IMPROVED)
            if data['total_teachers'] == 'N/A' or data['male_teachers'] == 'N/A' or data['female_teachers'] == 'N/A':
                try:
                    logger.debug(f"   🎯 Using enhanced CSS selectors for teacher data...")

                    # First, try to find the teacher section specifically
                    teacher_section_found = False
                    try:
                        # Look for the teacher section by the header
                        teacher_headers = driver.find_elements(By.XPATH, "//h2[contains(text(), 'Teacher')]")
                        if teacher_headers:
                            teacher_section_found = True
                            logger.debug(f"   Found teacher section header")

                            # Get the teacher section container
                            teacher_section = teacher_headers[0].find_element(By.XPATH, "following-sibling::div[1]")

                            # Extract teacher data using robust selectors within the teacher section
                            teacher_data_mappings = [
                                ("Total Teachers", 'total_teachers'),
                                ("Male", 'male_teachers'),
                                ("Female", 'female_teachers')
                            ]

                            for label_text, field_name in teacher_data_mappings:
                                if data[field_name] == 'N/A':
                                    try:
                                        # Method 3a: Find by label text and get the following H3Value
                                        label_elements = teacher_section.find_elements(By.XPATH, f".//p[contains(@class, 'fontTitle15') and contains(text(), '{label_text}')]")
                                        for label_element in label_elements:
                                            try:
                                                # Get the next sibling p element with H3Value class
                                                value_element = label_element.find_element(By.XPATH, "following-sibling::p[contains(@class, 'H3Value')]")
                                                value = value_element.text.strip()
                                                if value.isdigit():
                                                    data[field_name] = value
                                                    logger.debug(f"   Found {field_name} (label-based): {value}")
                                                    break
                                            except Exception as e:
                                                logger.debug(f"   Error getting value for {label_text}: {e}")
                                                continue
                                    except Exception as e:
                                        logger.debug(f"   Error finding label for {field_name}: {e}")
                    except Exception as e:
                        logger.debug(f"   Error finding teacher section: {e}")

                    # Method 3b: Fallback CSS selectors if teacher section approach didn't work
                    if not teacher_section_found or data['total_teachers'] == 'N/A' or data['male_teachers'] == 'N/A' or data['female_teachers'] == 'N/A':
                        logger.debug(f"   Trying fallback CSS selectors...")

                        # Enhanced CSS selectors based on the provided HTML structure
                        teacher_selectors = [
                            # Specific selectors for the teacher section structure
                            (".greyInfoList li:nth-child(1) .H3Value", 'total_teachers'),  # First li = Total Teachers
                            (".greyInfoList li:nth-child(2) .H3Value", 'male_teachers'),   # Second li = Male
                            (".greyInfoList li:nth-child(3) .H3Value", 'female_teachers'), # Third li = Female

                            # More specific selectors
                            ("ul.greyInfoList li:first-child p.H3Value", 'total_teachers'),
                            ("ul.greyInfoList li:nth-child(2) p.H3Value", 'male_teachers'),
                            ("ul.greyInfoList li:last-child p.H3Value", 'female_teachers'),
                        ]

                        for selector, field_name in teacher_selectors:
                            if data[field_name] == 'N/A':
                                try:
                                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                                    for element in elements:
                                        value = element.text.strip()
                                        if value.isdigit():
                                            data[field_name] = value
                                            logger.debug(f"   Found {field_name} (CSS): {value}")
                                            break
                                except Exception as e:
                                    logger.debug(f"   CSS selector failed for {field_name}: {e}")
                                    continue

                except Exception as e:
                    logger.debug(f"   Error in CSS selector teacher extraction: {e}")

            # Method 4: XPath-based extraction for teacher data (NEW)
            if data['total_teachers'] == 'N/A' or data['male_teachers'] == 'N/A' or data['female_teachers'] == 'N/A':
                try:
                    logger.debug(f"   🎯 Using XPath selectors for teacher data...")

                    # XPath selectors based on the HTML structure
                    xpath_selectors = [
                        # Find Total Teachers by text content
                        ("//p[contains(@class, 'fontTitle15') and contains(text(), 'Total Teachers')]/following-sibling::p[contains(@class, 'H3Value')]", 'total_teachers'),
                        # Find Male by text content (excluding "Total" and "Female")
                        ("//p[contains(@class, 'fontTitle15') and text()='Male']/following-sibling::p[contains(@class, 'H3Value')]", 'male_teachers'),
                        # Find Female by text content
                        ("//p[contains(@class, 'fontTitle15') and text()='Female']/following-sibling::p[contains(@class, 'H3Value')]", 'female_teachers'),

                        # Alternative XPath approaches
                        ("//h2[contains(text(), 'Teacher')]/following-sibling::div//li[1]//p[contains(@class, 'H3Value')]", 'total_teachers'),
                        ("//h2[contains(text(), 'Teacher')]/following-sibling::div//li[2]//p[contains(@class, 'H3Value')]", 'male_teachers'),
                        ("//h2[contains(text(), 'Teacher')]/following-sibling::div//li[3]//p[contains(@class, 'H3Value')]", 'female_teachers'),
                    ]

                    for xpath, field_name in xpath_selectors:
                        if data[field_name] == 'N/A':
                            try:
                                elements = driver.find_elements(By.XPATH, xpath)
                                for element in elements:
                                    value = element.text.strip()
                                    if value.isdigit():
                                        data[field_name] = value
                                        logger.debug(f"   Found {field_name} (XPath): {value}")
                                        break
                            except Exception as e:
                                logger.debug(f"   XPath selector failed for {field_name}: {e}")
                                continue

                except Exception as e:
                    logger.debug(f"   Error in XPath teacher extraction: {e}")

            # Method 5: Regex fallback for teacher data (Enhanced patterns)
            if data['total_teachers'] == 'N/A' or data['male_teachers'] == 'N/A' or data['female_teachers'] == 'N/A':
                try:
                    # Enhanced regex patterns based on the HTML structure
                    teacher_patterns = [
                        # Specific patterns for the Angular-generated HTML structure
                        (r'<p[^>]*class="fontTitle15[^>]*>Total Teachers</p>\s*<p[^>]*class="H3Value[^>]*>\s*(\d+)\s*</p>', 'total_teachers'),
                        (r'<p[^>]*class="fontTitle15[^>]*>Male</p>\s*<p[^>]*class="H3Value[^>]*>\s*(\d+)\s*</p>', 'male_teachers'),
                        (r'<p[^>]*class="fontTitle15[^>]*>Female</p>\s*<p[^>]*class="H3Value[^>]*>\s*(\d+)\s*</p>', 'female_teachers'),

                        # More flexible patterns that handle whitespace and attributes
                        (r'fontTitle15[^>]*>\s*Total Teachers\s*</p>\s*<p[^>]*H3Value[^>]*>\s*(\d+)\s*</p>', 'total_teachers'),
                        (r'fontTitle15[^>]*>\s*Male\s*</p>\s*<p[^>]*H3Value[^>]*>\s*(\d+)\s*</p>', 'male_teachers'),
                        (r'fontTitle15[^>]*>\s*Female\s*</p>\s*<p[^>]*H3Value[^>]*>\s*(\d+)\s*</p>', 'female_teachers'),

                        # Original patterns (kept for backward compatibility)
                        (r'Total Teachers[^>]*</p>\s*<p[^>]*class="H3Value[^>]*>\s*(\d+)\s*</p>', 'total_teachers'),
                        (r'Male[^>]*</p>\s*<p[^>]*class="H3Value[^>]*>\s*(\d+)\s*</p>', 'male_teachers'),
                        (r'Female[^>]*</p>\s*<p[^>]*class="H3Value[^>]*>\s*(\d+)\s*</p>', 'female_teachers'),

                        # Fallback patterns
                        (r'Total Teachers[:\s]*(\d+)', 'total_teachers'),
                        (r'(?<!Fe)Male[:\s]*(\d+)', 'male_teachers'),  # Negative lookbehind to avoid matching "Female"
                        (r'Female[:\s]*(\d+)', 'female_teachers'),
                    ]

                    for pattern, field_name in teacher_patterns:
                        if data[field_name] == 'N/A':
                            match = re.search(pattern, page_text, re.IGNORECASE | re.DOTALL)
                            if match:
                                data[field_name] = match.group(1).strip()
                                logger.debug(f"   Found {field_name} (regex): {data[field_name]}")

                except Exception as e:
                    logger.debug(f"   Error in regex teacher extraction: {e}")

            # TEACHER DATA CALCULATION FALLBACK
            try:
                logger.debug(f"   🧮 Applying teacher calculation fallback...")

                # If we have total and male teachers but missing female, calculate it
                if (data['total_teachers'] != 'N/A' and data['male_teachers'] != 'N/A' and
                    data['female_teachers'] == 'N/A'):
                    try:
                        total_teachers = int(data['total_teachers'])
                        male_teachers = int(data['male_teachers'])
                        calculated_female = total_teachers - male_teachers

                        if calculated_female >= 0:
                            data['female_teachers'] = str(calculated_female)
                            logger.debug(f"   Calculated Female Teachers: {calculated_female} (Total: {total_teachers} - Male: {male_teachers})")
                        else:
                            logger.debug(f"   Invalid calculation: Total({total_teachers}) - Male({male_teachers}) = {calculated_female}")
                    except ValueError as e:
                        logger.debug(f"   Error in teacher calculation: {e}")

                # If we have total and female teachers but missing male, calculate it
                elif (data['total_teachers'] != 'N/A' and data['female_teachers'] != 'N/A' and
                      data['male_teachers'] == 'N/A'):
                    try:
                        total_teachers = int(data['total_teachers'])
                        female_teachers = int(data['female_teachers'])
                        calculated_male = total_teachers - female_teachers

                        if calculated_male >= 0:
                            data['male_teachers'] = str(calculated_male)
                            logger.debug(f"   Calculated Male Teachers: {calculated_male} (Total: {total_teachers} - Female: {female_teachers})")
                        else:
                            logger.debug(f"   Invalid calculation: Total({total_teachers}) - Female({female_teachers}) = {calculated_male}")
                    except ValueError as e:
                        logger.debug(f"   Error in teacher calculation: {e}")

            except Exception as e:
                logger.debug(f"   Error in teacher calculation fallback: {e}")

            # 4. SCHOOL NAME - Extract from page title, header, or breadcrumb
            try:
                logger.debug(f"   🏫 Extracting School Name...")

                # Method 1: Try to get school name from page title
                page_title = driver.title
                if page_title and page_title != "Know Your School" and "UDISE" not in page_title:
                    clean_title = page_title.replace("Know Your School", "").replace("-", "").strip()
                    if clean_title and len(clean_title) > 3:
                        data['detail_school_name'] = clean_title
                        logger.debug(f"   Found school name from title: {clean_title}")

                # Fallback: Use school ID as identifier
                if data['detail_school_name'] == 'N/A':
                    data['detail_school_name'] = f"School_ID_{expected_school_id}"
                    logger.debug(f"   Using school ID as name: {data['detail_school_name']}")

            except Exception as e:
                logger.debug(f"   Error extracting school name: {e}")
                data['detail_school_name'] = f"School_ID_{expected_school_id}"

            # COMPREHENSIVE DATA VALIDATION AND STATUS INDICATORS
            try:
                logger.debug(f"   📊 Validating extracted data...")

                # Count successfully extracted fields
                extracted_fields = 0
                critical_fields = 0

                # Critical fields for Phase 2
                if data['total_students'] != 'N/A':
                    critical_fields += 1
                    extracted_fields += 1
                if data['total_teachers'] != 'N/A':
                    critical_fields += 1
                    extracted_fields += 1
                if data['detail_school_name'] != 'N/A' and not data['detail_school_name'].startswith('School_ID_'):
                    extracted_fields += 1

                # Additional fields
                additional_fields = [
                    'total_boys', 'total_girls', 'male_teachers', 'female_teachers',
                    'school_category', 'school_type', 'location', 'academic_year'
                ]
                for field in additional_fields:
                    if data[field] != 'N/A':
                        extracted_fields += 1

                # Add extraction status indicators
                data['extraction_status'] = 'SUCCESS' if critical_fields >= 2 else 'PARTIAL' if critical_fields >= 1 else 'FAILED'
                data['fields_extracted'] = extracted_fields
                data['critical_fields_extracted'] = critical_fields

                # Validation summary
                if critical_fields >= 2:
                    logger.info(f"✅ EXCELLENT extraction")
                    logger.info(f"   🎯 Critical fields: {critical_fields}/2, Total fields: {extracted_fields}")
                    logger.info(f"   👥 Students: {data['total_students']}, Teachers: {data['total_teachers']}")
                elif critical_fields >= 1:
                    logger.info(f"⚠️ PARTIAL extraction")
                    logger.info(f"   🎯 Critical fields: {critical_fields}/2, Total fields: {extracted_fields}")
                else:
                    logger.warning(f"❌ FAILED extraction")
                    logger.warning(f"   🎯 Critical fields: {critical_fields}/2, Total fields: {extracted_fields}")

            except Exception as e:
                logger.debug(f"   Error in data validation: {e}")
                data['extraction_status'] = 'ERROR'
                data['fields_extracted'] = 0
                data['critical_fields_extracted'] = 0

            return data

        except Exception as e:
            logger.error(f"   ❌ Error in extract_remaining_data_with_driver: {e}")
            return None

    def process_schools(self):
        """Main processing method - processes all schools from Phase 1 CSV using multithreading"""
        try:
            logger.info(f"\n🚀 STARTING STANDALONE PHASE 2 PROCESSING WITH MULTITHREADING")
            logger.info(f"="*80)
            logger.info(f"📁 Input file: {self.input_csv_file}")
            logger.info(f"🏛️ State: {self.state_name}")
            logger.info(f"📝 Output file: {self.output_csv_file}")
            logger.info(f"🧵 Worker threads: 3")
            logger.info(f"="*80)

            # Load Phase 1 data
            schools_df = self.load_phase1_data()
            if schools_df is None or len(schools_df) == 0:
                logger.error("❌ No valid Phase 1 data to process")
                return False

            # Apply record limit if specified
            if MAX_RECORDS_TO_PROCESS:
                schools_df = schools_df.head(MAX_RECORDS_TO_PROCESS)
                logger.info(f"🔢 Limited to {MAX_RECORDS_TO_PROCESS} records for testing")

            total_schools = len(schools_df)
            logger.info(f"🎯 Processing {total_schools} schools with know_more_link URLs")

            # Convert DataFrame to list of dictionaries and split into batches for 2 threads
            schools_list = []
            for idx, (_, school) in enumerate(schools_df.iterrows()):
                school_dict = school.to_dict()
                school_dict['processing_index'] = idx + 1
                schools_list.append(school_dict)

            # Split schools alternately among 3 threads
            batch_1 = []  # Thread 1: rows 1,4,7,10... (idx % 3 == 0)
            batch_2 = []  # Thread 2: rows 2,5,8,11... (idx % 3 == 1)
            batch_3 = []  # Thread 3: rows 3,6,9,12... (idx % 3 == 2)

            for idx, school in enumerate(schools_list):
                if idx % 3 == 0:  # Index 0,3,6,9... = rows 1,4,7,10...
                    batch_1.append(school)
                elif idx % 3 == 1:  # Index 1,4,7,10... = rows 2,5,8,11...
                    batch_2.append(school)
                else:  # idx % 3 == 2: Index 2,5,8,11... = rows 3,6,9,12...
                    batch_3.append(school)

            logger.info(f"🧵 Alternating batch distribution (3 threads):")
            logger.info(f"   Thread 1: {len(batch_1)} schools (rows 1,4,7,10...)")
            logger.info(f"   Thread 2: {len(batch_2)} schools (rows 2,5,8,11...)")
            logger.info(f"   Thread 3: {len(batch_3)} schools (rows 3,6,9,12...)")

            # Process schools using ThreadPoolExecutor with exactly 2 worker threads
            start_time = time.time()

            logger.info(f"🧵 Starting optimized multithreaded processing with alternating row distribution...")

            with ThreadPoolExecutor(max_workers=3) as executor:
                # Submit batches to the thread pool
                future_to_batch = {}
                future_1 = executor.submit(self.worker_process_schools_batch, batch_1, 1)
                future_2 = executor.submit(self.worker_process_schools_batch, batch_2, 2)
                future_3 = executor.submit(self.worker_process_schools_batch, batch_3, 3)

                future_to_batch[future_1] = ("Thread 1", len(batch_1))
                future_to_batch[future_2] = ("Thread 2", len(batch_2))
                future_to_batch[future_3] = ("Thread 3", len(batch_3))

                # Monitor progress and wait for completion
                completed_threads = 0
                for future in as_completed(future_to_batch):
                    thread_name, batch_size = future_to_batch[future]
                    completed_threads += 1

                    try:
                        result = future.result()
                        if result:
                            logger.info(f"✅ {thread_name} completed successfully ({batch_size} schools)")
                        else:
                            logger.warning(f"⚠️ {thread_name} completed with errors ({batch_size} schools)")
                    except Exception as exc:
                        logger.error(f"❌ {thread_name} generated an exception: {exc}")

                    # Show progress update
                    elapsed_time = time.time() - start_time

                    with self.stats_lock:
                        current_processed = self.processed_count
                        current_success = self.success_count
                        current_fail = self.fail_count

                    logger.info(f"\n📊 THREAD COMPLETION UPDATE:")
                    logger.info(f"   🧵 Threads completed: {completed_threads}/2")
                    logger.info(f"   🎯 Schools processed: {current_processed}/{total_schools}")
                    logger.info(f"   ✅ Successful: {current_success}")
                    logger.info(f"   ❌ Failed: {current_fail}")
                    logger.info(f"   ⏱️ Elapsed: {elapsed_time/60:.1f} minutes")
                    logger.info(f"   📝 Output file: {self.output_csv_file}")

                    if completed_threads == 2:
                        logger.info(f"🎉 All threads completed!")

            # Final progress check
            with self.stats_lock:
                final_processed = self.processed_count
                final_success = self.success_count
                final_fail = self.fail_count

            logger.info(f"\n📊 FINAL PROCESSING SUMMARY:")
            logger.info(f"   🎯 Total processed: {final_processed}/{total_schools}")
            logger.info(f"   ✅ Successful extractions: {final_success}")
            logger.info(f"   ❌ Failed extractions: {final_fail}")
            logger.info(f"   📈 Success rate: {final_success/final_processed*100:.1f}%" if final_processed > 0 else "📈 Success rate: 0%")

            # Final summary
            total_time = time.time() - start_time
            self.show_final_summary(total_time)

            return True

        except Exception as e:
            logger.error(f"❌ Critical error in process_schools: {e}")
            return False

    def show_final_summary(self, total_time):
        """Show final processing summary"""
        logger.info(f"\n{'='*80}")
        logger.info("🎯 OPTIMIZED MULTITHREADED STANDALONE PHASE 2 PROCESSING COMPLETED")
        logger.info(f"{'='*80}")
        logger.info(f"⏱️ Total processing time: {total_time/60:.1f} minutes")
        logger.info(f"🧵 Worker threads used: 3 (alternating rows, with persistent WebDriver instances)")
        logger.info(f"📊 Total schools processed: {self.processed_count}")
        logger.info(f"✅ Successfully extracted: {self.success_count}")
        logger.info(f"❌ Failed extractions: {self.fail_count}")
        logger.info(f"📈 Success rate: {self.success_count/self.processed_count*100:.1f}%" if self.processed_count > 0 else "📈 Success rate: 0%")
        logger.info(f"📁 Input file: {self.input_csv_file}")
        logger.info(f"📝 Output file: {self.output_csv_file}")
        logger.info(f"💾 Output contains: Phase 1 + Phase 2 combined data")
        logger.info(f"🚀 Performance optimization: Reused WebDriver instances per thread")
        logger.info("🎉 Optimized multithreaded standalone Phase 2 processing complete!")

def main():
    """Main function for standalone Phase 2 processing with optimized multithreading"""
    try:
        print("🚀 OPTIMIZED MULTITHREADED STANDALONE PHASE 2 PROCESSOR")
        print("Processes Phase 1 CSV files independently to extract detailed school data")
        print("🧵 Uses 3 worker threads with alternating row processing for optimal performance")
        print("⚡ Thread 1: rows 1,4,7,10..., Thread 2: rows 2,5,8,11..., Thread 3: rows 3,6,9,12...")
        print("⚡ Optimization: Each thread reuses its WebDriver for multiple schools")
        print(f"📁 Input file: {INPUT_CSV_FILE}")
        print()

        # Check if input file exists
        if not os.path.exists(INPUT_CSV_FILE):
            print(f"❌ Input file not found: {INPUT_CSV_FILE}")
            print("Please update the INPUT_CSV_FILE variable in the script with the correct path")
            return

        # Create processor and run
        processor = StandalonePhase2Processor(INPUT_CSV_FILE)
        success = processor.process_schools()

        if success:
            print(f"\n✅ Optimized multithreaded processing completed successfully!")
            print(f"📝 Output file: {processor.output_csv_file}")
            print(f"🧵 Used 3 worker threads with alternating row processing")
            print(f"⚡ Performance optimized: Reduced browser initialization overhead")
        else:
            print(f"\n❌ Processing failed. Check logs for details.")

    except Exception as e:
        print(f"❌ Critical error: {e}")
        print("Please check the logs above for details")

if __name__ == "__main__":
    main()
