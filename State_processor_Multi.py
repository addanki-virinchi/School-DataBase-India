#!/usr/bin/env python3
"""
Enhanced Sequential State Processor - Complete Phase 1 → Phase 2 workflow per state
- Interactive mode selection menu for flexible processing options
- Enhanced pagination handling with results per page optimization
- Smooth scrolling functionality for better page loading
- Robust connection error handling and retry mechanisms
- Maintains ultra-fast performance optimizations
- Resilient to connection issues with automatic recovery
"""

import time
import logging
import os
import glob
import re
import csv
import threading
import pandas as pd
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EnhancedStatewiseSchoolScraper:
    """Enhanced scraper with pagination, results per page, and scrolling improvements"""

    def __init__(self):
        # Import and inherit from the original scraper
        from phase1_statewise_scraper import StatewiseSchoolScraper
        self.base_scraper = StatewiseSchoolScraper()

        # Delegate all base functionality to the original scraper
        self.driver = None
        self.current_state = None
        self.current_district = None
        self.state_schools_with_links = {}
        self.state_schools_no_links = {}

        # CSV file management for incremental saving
        self.current_csv_file = None
        self.csv_headers_written = False
        self.total_schools_saved = 0

    def __getattr__(self, name):
        """Delegate all undefined methods to the base scraper"""
        return getattr(self.base_scraper, name)

    def setup_driver(self):
        """Setup standard Chrome WebDriver with automatic driver management"""
        try:
            logger.info("🔧 Setting up standard Chrome WebDriver for Phase 1...")

            # Setup Chrome options for Phase 1 processing
            options = Options()

            # Core stability options
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-blink-features=AutomationControlled")

            # Performance optimizations for Phase 1
            options.add_argument("--disable-images")  # Speed optimization
            options.add_argument("--disable-plugins")  # Speed optimization
            options.add_argument("--memory-pressure-off")
            options.add_argument("--max_old_space_size=4096")

            # Try automatic ChromeDriver management first
            try:
                from webdriver_manager.chrome import ChromeDriverManager
                logger.info("   🔄 Using webdriver-manager for automatic ChromeDriver setup...")

                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=options)
                logger.info("   ✅ ChromeDriver automatically managed and compatible")

            except ImportError:
                logger.warning("   ⚠️ webdriver-manager not available, trying manual ChromeDriver setup...")
                # Fallback to manual ChromeDriver setup
                self.driver = webdriver.Chrome(options=options)
                logger.info("   ✅ Using system ChromeDriver")

            except Exception as webdriver_manager_error:
                logger.warning(f"   ⚠️ webdriver-manager failed: {webdriver_manager_error}")
                logger.info("   🔄 Falling back to manual ChromeDriver setup...")
                # Fallback to manual ChromeDriver setup
                self.driver = webdriver.Chrome(options=options)
                logger.info("   ✅ Using system ChromeDriver")

            self.driver.maximize_window()

            # Phase 1 optimized timeouts
            self.driver.implicitly_wait(10)
            self.driver.set_page_load_timeout(45)  # Increased for Phase 1 stability
            self.driver.set_script_timeout(30)

            # Also set driver for base scraper compatibility
            self.base_scraper.driver = self.driver

            # Test driver functionality
            self.driver.get("about:blank")
            logger.info("✅ Standard Chrome WebDriver initialized and tested for Phase 1")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to initialize standard Chrome WebDriver: {e}")

            # Provide specific troubleshooting for ChromeDriver version issues
            error_message = str(e)
            if "This version of ChromeDriver only supports Chrome version" in error_message:
                logger.error("🔧 CHROMEDRIVER VERSION MISMATCH DETECTED:")
                logger.error("   1. Install webdriver-manager: pip install webdriver-manager")
                logger.error("   2. Or download matching ChromeDriver from: https://chromedriver.chromium.org/")
                logger.error("   3. Or update Chrome browser to match your ChromeDriver version")
                logger.error("   4. Current error suggests ChromeDriver and Chrome versions don't match")
            elif "cannot connect to chrome" in error_message:
                logger.error("🔧 CHROME CONNECTION ISSUE:")
                logger.error("   1. Ensure Chrome browser is properly installed")
                logger.error("   2. Close all Chrome instances and try again")
                logger.error("   3. Run as administrator if needed")
                logger.error("   4. Check if antivirus is blocking Chrome/ChromeDriver")
            else:
                logger.error("Please ensure Chrome browser is installed and updated")

            return False

    def navigate_to_portal(self, max_retries=3):
        """Navigate to UDISE Plus portal using standard WebDriver"""
        for attempt in range(max_retries):
            try:
                logger.info(f"🌐 Navigating to UDISE Plus portal (attempt {attempt + 1}/{max_retries})")

                # Navigate to portal
                self.driver.get("https://udiseplus.gov.in/#/en/home")
                time.sleep(3)

                # Click Visit Portal
                logger.info("🔍 Looking for Visit Portal button...")
                visit_portal_btn = WebDriverWait(self.driver, 15).until(
                    EC.element_to_be_clickable((By.XPATH, "//a[contains(text(),'Visit Portal')]"))
                )
                visit_portal_btn.click()
                time.sleep(3)

                # Switch to new tab if opened
                if len(self.driver.window_handles) > 1:
                    self.driver.switch_to.window(self.driver.window_handles[-1])
                    time.sleep(2)

                # Click Advance Search
                logger.info("🔍 Looking for Advance Search button...")
                advance_search_btn = WebDriverWait(self.driver, 15).until(
                    EC.element_to_be_clickable((By.XPATH, "//a[@id='advanceSearch']"))
                )
                advance_search_btn.click()

                # Wait for search page to load
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "select.form-select.select"))
                )

                logger.info("✅ Successfully navigated to portal using standard WebDriver")
                return True

            except Exception as e:
                logger.error(f"❌ Portal navigation failed (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(10)
                    try:
                        self.driver.refresh()
                        time.sleep(5)
                    except:
                        pass

        logger.error("❌ All portal navigation attempts failed")
        return False

    def extract_states_data(self):
        """Extract states data using standard WebDriver"""
        try:
            logger.info("📊 Extracting states data using standard WebDriver...")

            # Wait for state dropdown to be available
            state_dropdown = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "select.form-select.select"))
            )

            # Get all state options
            state_options = state_dropdown.find_elements(By.TAG_NAME, "option")
            states_data = []

            for option in state_options:
                value = option.get_attribute("value")
                text = option.text.strip()

                # Skip empty or default options
                if value and value != "0" and text and text != "Select State":
                    states_data.append({
                        'stateCode': value,
                        'stateName': text
                    })

            logger.info(f"✅ Extracted {len(states_data)} states using standard WebDriver")
            return states_data

        except Exception as e:
            logger.error(f"❌ Failed to extract states data: {e}")
            return []

    def select_state(self, state_data):
        """Select state using standard WebDriver"""
        try:
            logger.info(f"🎯 Selecting state: {state_data['stateName']}")

            # Find and select state dropdown
            state_dropdown = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "select.form-select.select"))
            )

            # Create Select object and select by value
            select = Select(state_dropdown)
            select.select_by_value(state_data['stateCode'])

            # Store current state
            self.current_state = state_data

            # Wait for districts to load
            time.sleep(3)

            logger.info(f"✅ State selected: {state_data['stateName']}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to select state {state_data['stateName']}: {e}")
            return False

    def extract_districts_data(self):
        """Extract districts data using standard WebDriver"""
        try:
            logger.info("🏛️ Extracting districts data using standard WebDriver...")

            # Wait for district dropdown to be available and populated
            WebDriverWait(self.driver, 15).until(
                lambda driver: len(driver.find_elements(By.CSS_SELECTOR, "select.form-select.select")[1].find_elements(By.TAG_NAME, "option")) > 1
            )

            # Get district dropdown (second select element)
            district_dropdowns = self.driver.find_elements(By.CSS_SELECTOR, "select.form-select.select")
            if len(district_dropdowns) < 2:
                logger.error("❌ District dropdown not found")
                return []

            district_dropdown = district_dropdowns[1]
            district_options = district_dropdown.find_elements(By.TAG_NAME, "option")
            districts_data = []

            for option in district_options:
                value = option.get_attribute("value")
                text = option.text.strip()

                # Skip empty or default options
                if value and value != "0" and text and text != "Select District":
                    districts_data.append({
                        'districtCode': value,
                        'districtName': text
                    })

            logger.info(f"✅ Extracted {len(districts_data)} districts using standard WebDriver")
            return districts_data

        except Exception as e:
            logger.error(f"❌ Failed to extract districts data: {e}")
            return []

    def select_district(self, district_data):
        """Select district using standard WebDriver with enhanced error handling"""
        try:
            logger.info(f"🎯 Selecting district: {district_data['districtName']}")
            logger.debug(f"   🔍 District data: {district_data}")

            # Get district dropdown (second select element)
            district_dropdowns = self.driver.find_elements(By.CSS_SELECTOR, "select.form-select.select")
            if len(district_dropdowns) < 2:
                logger.error("❌ District dropdown not found")
                logger.debug(f"   🔍 Found {len(district_dropdowns)} select elements")
                return False

            district_dropdown = district_dropdowns[1]

            # Create Select object
            select = Select(district_dropdown)

            # Extract the correct value to use for selection
            district_value = None

            # Try different possible keys for district value
            possible_keys = ['districtCode', 'districtId', 'value', 'id', 'code']
            for key in possible_keys:
                if key in district_data and district_data[key]:
                    district_value = str(district_data[key])
                    logger.debug(f"   🔍 Using district value from '{key}': {district_value}")
                    break

            if not district_value:
                # If no standard key found, try to extract from the district name
                district_value = district_data.get('districtName', '')
                logger.debug(f"   🔍 Fallback to district name: {district_value}")

            # Log available options for debugging
            options = select.options
            logger.debug(f"   🔍 Available district options ({len(options)}):")
            for i, option in enumerate(options[:10]):  # Log first 10 options
                try:
                    logger.debug(f"      {i+1}. value='{option.get_attribute('value')}', text='{option.text}'")
                except:
                    pass

            # Try multiple selection strategies
            selection_successful = False

            # Strategy 1: Select by value
            if district_value:
                try:
                    select.select_by_value(district_value)
                    selection_successful = True
                    logger.info(f"   ✅ Selected district by value: {district_value}")
                except Exception as value_error:
                    logger.debug(f"   ⚠️ Selection by value failed: {value_error}")

            # Strategy 2: Select by visible text
            if not selection_successful:
                try:
                    district_name = district_data['districtName']
                    select.select_by_visible_text(district_name)
                    selection_successful = True
                    logger.info(f"   ✅ Selected district by text: {district_name}")
                except Exception as text_error:
                    logger.debug(f"   ⚠️ Selection by text failed: {text_error}")

            # Strategy 3: Select by partial text match
            if not selection_successful:
                try:
                    district_name = district_data['districtName']
                    for option in options:
                        if district_name.upper() in option.text.upper():
                            option.click()
                            selection_successful = True
                            logger.info(f"   ✅ Selected district by partial match: {option.text}")
                            break
                except Exception as partial_error:
                    logger.debug(f"   ⚠️ Selection by partial match failed: {partial_error}")

            if not selection_successful:
                logger.error(f"❌ All district selection strategies failed for: {district_data['districtName']}")
                return False

            # Store current district
            self.current_district = district_data

            # Wait for blocks/sub-districts to load
            time.sleep(3)

            logger.info(f"✅ District selected: {district_data['districtName']}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to select district {district_data.get('districtName', 'Unknown')}: {e}")
            logger.debug(f"   🔍 District data type: {type(district_data)}")
            logger.debug(f"   🔍 District data keys: {list(district_data.keys()) if isinstance(district_data, dict) else 'Not a dict'}")
            return False

    def click_search_button_standard(self):
        """Click search button using standard WebDriver with multiple fallback selectors"""
        try:
            logger.info("🔍 Clicking search button using standard WebDriver...")

            # Multiple search button selectors to try
            search_button_selectors = [
                "//button[contains(text(),'Search')]",
                "//button[@type='submit']",
                "//input[@type='submit']",
                "//button[contains(@class,'btn-primary')]",
                "//button[contains(@class,'search')]",
                "//button[@id='searchBtn']",
                "//button[@id='search']",
                "#searchBtn",
                ".btn-primary",
                ".search-btn",
                "button[type='submit']"
            ]

            search_button = None
            used_selector = None

            # Try each selector until one works
            for selector in search_button_selectors:
                try:
                    if selector.startswith("//") or selector.startswith("("):
                        # XPath selector
                        search_button = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                    else:
                        # CSS selector
                        search_button = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                    used_selector = selector
                    logger.info(f"   ✅ Found search button with selector: {selector}")
                    break
                except Exception as selector_error:
                    logger.debug(f"   ⚠️ Selector failed: {selector} - {selector_error}")
                    continue

            if not search_button:
                # Log page source for debugging
                logger.error("❌ No search button found with any selector")
                logger.debug("🔍 Current page source (first 500 chars):")
                logger.debug(self.driver.page_source[:500])
                return False

            # Click the search button
            search_button.click()
            logger.info(f"   🔘 Search button clicked using: {used_selector}")

            # Wait for results to load
            time.sleep(5)

            # Verify results loaded with multiple possible selectors
            result_selectors = [
                ".table-responsive",
                ".school-list",
                ".results",
                ".accordion",
                ".card",
                "table",
                ".list-group",
                ".search-results"
            ]

            results_found = False
            for result_selector in result_selectors:
                try:
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, result_selector))
                    )
                    logger.info(f"   ✅ Results loaded, found: {result_selector}")
                    results_found = True
                    break
                except:
                    continue

            if not results_found:
                logger.warning("⚠️ Could not verify results loaded, but search button was clicked")
                # Continue anyway as results might be loading

            logger.info("✅ Search button clicked successfully")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to click search button: {e}")
            # Log additional debugging information
            try:
                logger.debug(f"🔍 Current URL: {self.driver.current_url}")
                logger.debug(f"🔍 Page title: {self.driver.title}")
                # Log available buttons
                buttons = self.driver.find_elements(By.TAG_NAME, "button")
                logger.debug(f"🔍 Found {len(buttons)} buttons on page")
                for i, btn in enumerate(buttons[:5]):  # Log first 5 buttons
                    try:
                        logger.debug(f"   Button {i+1}: text='{btn.text}', class='{btn.get_attribute('class')}'")
                    except:
                        pass
            except:
                pass
            return False

    def enhanced_click_search_button(self):
        """Enhanced search button click with results per page optimization using standard WebDriver"""
        try:
            # Click the search button using standard WebDriver
            search_success = self.click_search_button_standard()

            if not search_success:
                logger.error("❌ Failed to click search button")
                return False

            # Balanced wait for initial results to load (reliability focused)
            time.sleep(3)  # Increased for better reliability

            # Try to set results per page to 100 with verification
            results_per_page_success = self.set_results_per_page_to_100_standard()
            if results_per_page_success:
                logger.info("✅ Successfully set results per page to 100")
                # Reliable wait for page to reload with 100 results per page
                time.sleep(3)  # Wait for complete loading

                # Verify that school elements are now available
                self.wait_for_school_elements_to_load_standard()
            else:
                logger.warning("⚠️ Failed to set results per page to 100 - continuing with default")

            # Scroll to bottom of page to ensure all content is loaded
            self.scroll_to_bottom_standard()

            return True

        except Exception as e:
            logger.error(f"❌ Error in enhanced search button click: {e}")
            return False

    def set_results_per_page_to_100_standard(self):
        """Set results per page to 100 using standard WebDriver"""
        try:
            logger.info("🔧 Setting results per page to 100 using standard WebDriver...")

            # Multiple selectors for results per page dropdown
            results_per_page_selectors = [
                "select.form-select.w11110",
                "select[name='resultsPerPage']",
                "select.results-per-page",
                ".form-select:last-of-type",
                "select.form-control:last-of-type",
                "select:contains('10')",
                "select option[value='100']"
            ]

            results_per_page_select = None
            used_selector = None

            # Try each selector
            for selector in results_per_page_selectors:
                try:
                    results_per_page_select = WebDriverWait(self.driver, 8).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    used_selector = selector
                    logger.info(f"   ✅ Found results per page dropdown: {selector}")
                    break
                except Exception as selector_error:
                    logger.debug(f"   ⚠️ Selector failed: {selector} - {selector_error}")
                    continue

            if not results_per_page_select:
                logger.warning("⚠️ Results per page dropdown not found")
                return False

            # Create Select object and choose 100
            select = Select(results_per_page_select)

            # Log available options
            options = select.options
            logger.debug(f"   🔍 Available options: {[opt.get_attribute('value') for opt in options]}")

            # Check if 100 option is available and select it
            option_100_found = False
            for option in options:
                if option.get_attribute('value') == '100':
                    option_100_found = True
                    break

            if option_100_found:
                select.select_by_value('100')
                logger.info("   ✅ Selected 100 results per page")

                # Wait for page to reload with new results
                time.sleep(3)
                return True
            else:
                # Try to select the highest available option
                max_value = 0
                max_option = None
                for option in options:
                    try:
                        value = int(option.get_attribute('value'))
                        if value > max_value:
                            max_value = value
                            max_option = option
                    except:
                        continue

                if max_option and max_value > 10:
                    select.select_by_value(str(max_value))
                    logger.info(f"   ✅ Selected maximum available: {max_value} results per page")
                    time.sleep(3)
                    return True
                else:
                    logger.warning("   ⚠️ No suitable results per page option found")
                    return False

        except Exception as e:
            logger.warning(f"⚠️ Failed to set results per page: {e}")
            return False

    def wait_for_school_elements_to_load_standard(self):
        """Wait for school elements to load using standard WebDriver"""
        try:
            logger.info("⏳ Waiting for school elements to load...")

            # Multiple selectors for school elements
            school_element_selectors = [
                ".accordion-body",
                ".accordion-item",
                ".card-body",
                ".result-item",
                "table tbody tr",
                ".school-item",
                ".list-group-item"
            ]

            # Wait for any school elements to appear
            for selector in school_element_selectors:
                try:
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    logger.info(f"   ✅ School elements loaded: {selector}")
                    return True
                except:
                    continue

            logger.warning("⚠️ No school elements found with standard selectors")
            return False

        except Exception as e:
            logger.warning(f"⚠️ Error waiting for school elements: {e}")
            return False

    def scroll_to_bottom_standard(self):
        """Scroll to bottom of page using standard WebDriver"""
        try:
            logger.info("📜 Scrolling to bottom to load all content...")

            # Scroll to bottom of page
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)

            # Scroll back to top for better element visibility
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)

            logger.info("   ✅ Page scrolling completed")
            return True

        except Exception as e:
            logger.warning(f"⚠️ Error scrolling page: {e}")
            return False

    def set_results_per_page_to_100(self):
        """Set results per page to 100 for maximum efficiency with verification"""
        try:
            logger.info("🔧 Setting results per page to 100...")

            # Wait for the results per page dropdown with reliable timeout
            results_per_page_select = WebDriverWait(self.driver, 8).until(  # Restored to 8s for reliability
                EC.presence_of_element_located((By.CSS_SELECTOR, "select.form-select.w11110"))
            )

            # Create Select object and choose 100
            select = Select(results_per_page_select)

            # Check if 100 option is available
            available_options = [option.get_attribute('value') for option in select.options]
            logger.info(f"📋 Available results per page options: {available_options}")

            if "100" in available_options:
                select.select_by_value("100")

                # Verify the selection was successful
                selected_value = select.first_selected_option.get_attribute('value')
                if selected_value == "100":
                    logger.info("✅ Successfully set and verified results per page to 100")
                    time.sleep(1.5)  # Increased from 0.5s to 1.5s for reliable page update
                    return True
                else:
                    logger.warning(f"⚠️ Selection verification failed. Selected: {selected_value}")
                    return False
            else:
                logger.warning("⚠️ Option '100' not available in results per page dropdown")
                # Try to select the highest available option
                max_option = max([int(opt) for opt in available_options if opt.isdigit()])
                select.select_by_value(str(max_option))
                logger.info(f"📋 Selected maximum available option: {max_option}")
                time.sleep(1.5)  # Increased from 0.5s to 1.5s for reliable page update
                return True

        except Exception as e:
            logger.warning(f"⚠️ Failed to set results per page to 100: {e}")
            return False

    def scroll_to_bottom(self):
        """Optimized scroll to bottom with minimal wait times"""
        try:
            logger.debug("🔄 Scrolling to bottom of page...")

            # Fast scroll to bottom without height checking for performance
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(0.5)  # Minimal wait - reduced from 3 seconds to 0.5 seconds

            logger.debug("✅ Scrolled to bottom of page")
            return True

        except Exception as e:
            logger.warning(f"⚠️ Error scrolling to bottom: {e}")
            return False

    def wait_for_school_elements_to_load(self):
        """Wait for school elements to be properly loaded on the page"""
        try:
            logger.info("⏳ Waiting for school elements to load...")

            # Wait for school elements to be present
            selectors_to_check = [
                ".accordion-body",
                ".accordion-item",
                "[class*='accordion']"
            ]

            elements_found = False
            for selector in selectors_to_check:
                try:
                    WebDriverWait(self.driver, 10).until(
                        lambda driver: len(driver.find_elements(By.CSS_SELECTOR, selector)) > 0
                    )
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        logger.info(f"✅ Found {len(elements)} school elements with selector: {selector}")
                        elements_found = True
                        break
                except:
                    continue

            if not elements_found:
                logger.warning("⚠️ No school elements found after waiting - page may have no results")

            # Reliable wait to ensure all content is fully rendered
            time.sleep(3)  # Increased from 2s to 3s for complete content loading

            return elements_found

        except Exception as e:
            logger.warning(f"⚠️ Error waiting for school elements: {e}")
            return False

    def wait_for_school_elements_to_load_fast(self):
        """Fast version of element loading check with reduced timeouts"""
        try:
            logger.debug("⚡ Fast check for school elements...")

            # Quick check with reduced timeout
            selectors_to_check = [".accordion-body", ".accordion-item", "[class*='accordion']"]

            for selector in selectors_to_check:
                try:
                    WebDriverWait(self.driver, 5).until(  # Reduced from 10s to 5s
                        lambda driver: len(driver.find_elements(By.CSS_SELECTOR, selector)) > 0
                    )
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        logger.debug(f"⚡ Fast found {len(elements)} elements with: {selector}")
                        # Balanced wait for content rendering
                        time.sleep(1.5)  # Increased from 0.5s to 1.5s for better reliability
                        return True
                except:
                    continue

            logger.debug("⚡ Fast check: No elements found")
            return False

        except Exception as e:
            logger.debug(f"⚠️ Error in fast element check: {e}")
            return False

    def initialize_csv_file(self, state_name):
        """Initialize CSV file for incremental saving with enhanced debugging"""
        try:
            # Create filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            clean_state_name = state_name.replace(' ', '_').replace('&', 'and').replace('/', '_').upper()
            self.current_csv_file = f"{clean_state_name}_phase1_complete_{timestamp}.csv"

            # Get absolute path for debugging
            abs_path = os.path.abspath(self.current_csv_file)
            current_dir = os.getcwd()

            # Reset tracking variables
            self.csv_headers_written = False
            self.total_schools_saved = 0

            logger.info(f"📁 Initialized CSV file for incremental saving: {self.current_csv_file}")
            logger.info(f"📍 Absolute path: {abs_path}")
            logger.info(f"📂 Current working directory: {current_dir}")

            # Test if we can create the file
            try:
                test_file = open(self.current_csv_file, 'w', encoding='utf-8')
                test_file.close()
                os.remove(self.current_csv_file)  # Clean up test file
                logger.info(f"✅ CSV file creation test successful")
            except Exception as test_error:
                logger.error(f"❌ CSV file creation test failed: {test_error}")
                return False

            return True

        except Exception as e:
            logger.error(f"❌ Error initializing CSV file: {e}")
            return False

    def save_schools_to_csv_incremental(self, schools_data, page_number):
        """Save schools data to CSV file incrementally (page by page)"""
        try:
            if not schools_data:
                logger.debug(f"   📄 No schools to save for page {page_number}")
                return True

            if not self.current_csv_file:
                logger.error("❌ CSV file not initialized")
                return False

            # Define CSV headers (matching Phase 1 specification exactly)
            headers = [
                'has_know_more_link', 'phase2_ready', 'state', 'state_id', 'district', 'district_id',
                'extraction_date', 'udise_code', 'school_name', 'know_more_link', 'email',
                'operational_status', 'school_category', 'school_management', 'school_type',
                'school_location', 'address', 'pin_code'
            ]

            # Write headers if this is the first write
            if not self.csv_headers_written:
                try:
                    with open(self.current_csv_file, 'w', newline='', encoding='utf-8') as csvfile:
                        writer = csv.DictWriter(csvfile, fieldnames=headers)
                        writer.writeheader()
                        csvfile.flush()  # Ensure data is written to disk

                    # Verify file was created
                    if os.path.exists(self.current_csv_file):
                        file_size = os.path.getsize(self.current_csv_file)
                        logger.info(f"   📝 Created CSV file with headers: {self.current_csv_file} ({file_size} bytes)")
                        self.csv_headers_written = True
                    else:
                        logger.error(f"   ❌ CSV file was not created: {self.current_csv_file}")
                        return False

                except Exception as header_error:
                    logger.error(f"   ❌ Error writing CSV headers: {header_error}")
                    return False

            # Append schools data to CSV
            try:
                with open(self.current_csv_file, 'a', newline='', encoding='utf-8') as csvfile:
                    writer = csv.DictWriter(csvfile, fieldnames=headers)

                    rows_written = 0
                    for school in schools_data:
                        # Ensure all required fields are present and map field names
                        school_row = {}
                        for header in headers:
                            if header == 'has_know_more_link':
                                # Boolean: True if know_more_link exists and is valid
                                know_more_link = school.get('know_more_link', 'N/A')
                                school_row[header] = (know_more_link != 'N/A' and
                                                    know_more_link and
                                                    'schooldetail' in str(know_more_link))
                            elif header == 'phase2_ready':
                                # Boolean: Same as has_know_more_link (ready for Phase 2 if has valid link)
                                know_more_link = school.get('know_more_link', 'N/A')
                                school_row[header] = (know_more_link != 'N/A' and
                                                    know_more_link and
                                                    'schooldetail' in str(know_more_link))
                            elif header == 'school_location':
                                # Map 'location' field to 'school_location'
                                school_row[header] = school.get('location', 'N/A')
                            elif header == 'pin_code':
                                # Map 'pincode' field to 'pin_code'
                                school_row[header] = school.get('pincode', 'N/A')
                            elif header == 'address':
                                # Use address field or fallback to location
                                school_row[header] = school.get('address', school.get('location', 'N/A'))
                            else:
                                # Direct mapping for all other fields
                                school_row[header] = school.get(header, 'N/A')
                        writer.writerow(school_row)
                        rows_written += 1

                    csvfile.flush()  # Ensure data is written to disk

                self.total_schools_saved += len(schools_data)

                # Verify file exists and has grown
                if os.path.exists(self.current_csv_file):
                    file_size = os.path.getsize(self.current_csv_file)
                    logger.info(f"   💾 Saved page {page_number} with {len(schools_data)} schools to CSV")
                    logger.info(f"   📊 Total schools saved so far: {self.total_schools_saved}")
                    logger.info(f"   📄 Current file size: {file_size} bytes")
                else:
                    logger.error(f"   ❌ CSV file disappeared after writing: {self.current_csv_file}")
                    return False

            except Exception as write_error:
                logger.error(f"   ❌ Error writing schools data to CSV: {write_error}")
                return False

            return True

        except Exception as e:
            logger.error(f"❌ Error saving schools to CSV: {e}")
            return False

    def check_csv_file_status(self):
        """Check current CSV file status and provide detailed information"""
        try:
            if not self.current_csv_file:
                logger.warning("⚠️ No CSV file initialized")
                return False

            abs_path = os.path.abspath(self.current_csv_file)
            logger.info(f"🔍 Checking CSV file status:")
            logger.info(f"   📄 Filename: {self.current_csv_file}")
            logger.info(f"   📍 Absolute path: {abs_path}")

            if os.path.exists(self.current_csv_file):
                file_size = os.path.getsize(self.current_csv_file)
                mod_time = datetime.fromtimestamp(os.path.getmtime(self.current_csv_file))
                logger.info(f"   ✅ File exists: YES")
                logger.info(f"   📊 File size: {file_size} bytes ({file_size/1024:.1f} KB)")
                logger.info(f"   🕒 Last modified: {mod_time}")
                logger.info(f"   📊 Schools saved: {self.total_schools_saved}")
                return True
            else:
                logger.error(f"   ❌ File exists: NO")
                logger.error(f"   📂 Directory contents:")
                try:
                    current_dir = os.getcwd()
                    files = [f for f in os.listdir(current_dir) if f.endswith('.csv')]
                    for f in files[:5]:  # Show first 5 CSV files
                        logger.error(f"      • {f}")
                except:
                    pass
                return False

        except Exception as e:
            logger.error(f"❌ Error checking CSV file status: {e}")
            return False

    def finalize_csv_file(self):
        """Finalize CSV file and provide summary"""
        try:
            # First check the file status
            self.check_csv_file_status()

            if self.current_csv_file and os.path.exists(self.current_csv_file):
                file_size = os.path.getsize(self.current_csv_file)
                abs_path = os.path.abspath(self.current_csv_file)
                logger.info(f"📁 CSV file finalized: {self.current_csv_file}")
                logger.info(f"📍 Full path: {abs_path}")
                logger.info(f"📊 Final statistics: {self.total_schools_saved} schools, {file_size/1024:.1f} KB")
                return True
            else:
                logger.warning("⚠️ No CSV file to finalize or file does not exist")
                return False

        except Exception as e:
            logger.error(f"❌ Error finalizing CSV file: {e}")
            return False

    def enhanced_click_next_page(self):
        """Enhanced pagination handling with robust next button detection and retry mechanism"""
        max_retries = 3

        for attempt in range(max_retries):
            try:
                logger.debug(f"Attempting to click next page (attempt {attempt + 1}/{max_retries})")

                # Find next button using the specific HTML structure
                next_buttons = self.driver.find_elements(By.CSS_SELECTOR, "a.nextBtn")

                if not next_buttons:
                    logger.debug("No next button found")
                    return False

                next_button = next_buttons[0]

                # Check if button is displayed
                if not next_button.is_displayed():
                    logger.debug("Next button not displayed")
                    return False

                # CRITICAL: Check if the parent <li> element has disabled class
                try:
                    parent_li = next_button.find_element(By.XPATH, "..")
                    parent_classes = parent_li.get_attribute("class") or ""

                    # Check if parent li has disabled class - this is the primary indicator
                    if "disabled" in parent_classes.lower():
                        logger.info("📄 Next button is disabled (parent li has disabled class) - reached end of pagination")
                        logger.info(f"📊 Final pagination status: Parent classes = '{parent_classes}'")
                        return False

                except Exception as parent_check_error:
                    logger.debug(f"Could not check parent element: {parent_check_error}")
                    # Continue with other checks

                # Additional checks for button state
                button_classes = next_button.get_attribute("class") or ""
                if "disabled" in button_classes.lower():
                    logger.info("📄 Next button is disabled (has disabled class) - reached end of pagination")
                    logger.info(f"📊 Final pagination status: Button classes = '{button_classes}'")
                    return False

                # Check for disabled attribute
                if next_button.get_attribute("disabled"):
                    logger.info("📄 Next button has disabled attribute - reached end of pagination")
                    logger.info(f"📊 Final pagination status: Disabled attribute = True")
                    return False

                # Check if button is enabled (basic Selenium check)
                if not next_button.is_enabled():
                    logger.info("📄 Next button is not enabled - reached end of pagination")
                    logger.info(f"📊 Final pagination status: Button enabled = False")
                    return False

                # Scroll to button to ensure it's visible
                try:
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_button)
                    time.sleep(0.3)  # Reduced from 1 second to 0.3 seconds

                    # Try multiple click methods with retry
                    click_success = False

                    # Method 1: Regular click
                    try:
                        next_button.click()
                        logger.info("✅ Clicked next page button (regular click)")
                        click_success = True
                    except Exception as click_error:
                        logger.debug(f"Regular click failed: {click_error}")

                    # Method 2: JavaScript click if regular click failed
                    if not click_success:
                        try:
                            self.driver.execute_script("arguments[0].click();", next_button)
                            logger.info("✅ Clicked next page button (JavaScript click)")
                            click_success = True
                        except Exception as js_click_error:
                            logger.debug(f"JavaScript click failed: {js_click_error}")

                    # Method 3: Force click with JavaScript if both failed
                    if not click_success:
                        try:
                            self.driver.execute_script("""
                                var event = new MouseEvent('click', {
                                    view: window,
                                    bubbles: true,
                                    cancelable: true
                                });
                                arguments[0].dispatchEvent(event);
                            """, next_button)
                            logger.info("✅ Clicked next page button (force JavaScript click)")
                            click_success = True
                        except Exception as force_click_error:
                            logger.debug(f"Force JavaScript click failed: {force_click_error}")

                    if click_success:
                        # Balanced wait time for page to load after successful click
                        time.sleep(1.5)  # Restored from 0.8s to 1.5s for reliable page loading
                        return True
                    else:
                        logger.warning(f"All click methods failed on attempt {attempt + 1}")

                except Exception as scroll_error:
                    logger.warning(f"Failed to scroll to next button on attempt {attempt + 1}: {scroll_error}")

                # Reasonable wait before retry
                if attempt < max_retries - 1:
                    time.sleep(0.8)  # Increased from 0.3s to 0.8s for better reliability

            except Exception as e:
                logger.warning(f"Error in enhanced_click_next_page attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(1)

        logger.warning(f"Failed to click next page button after {max_retries} attempts")
        return False

    def extract_email_from_school_element(self, school_element):
        """Ultra-fast email extraction with single DOM access"""
        try:
            # Single DOM access for maximum performance
            element_html = school_element.get_attribute('innerHTML')
            if not element_html:
                return 'N/A'

            # Pre-compiled regex patterns for maximum speed
            if not hasattr(self, '_email_patterns'):
                self._email_patterns = [
                    re.compile(r'href="mailto:([^"]+)"', re.IGNORECASE),  # mailto links
                    re.compile(r'<span[^>]*>([^<]*@[^<]*)</span>', re.IGNORECASE),  # span with email
                    re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')  # general email
                ]

            # Fast pattern matching with early exit
            for i, pattern in enumerate(self._email_patterns):
                match = pattern.search(element_html)
                if match:
                    email = match.group(1) if i < 2 else match.group(0)
                    email = email.strip()
                    if email and '@' in email and len(email) > 5:  # Basic validation
                        return email

            return 'N/A'

        except:
            return 'N/A'

    def extract_single_school_data_with_email(self, school_element):
        """Enhanced single school data extraction using standard WebDriver"""
        try:
            # Extract school data using standard WebDriver methods
            school_data = self.extract_single_school_data_standard(school_element)

            if not school_data:
                return None

            # Validate that we have meaningful school data
            # Check if essential fields have actual data (not just N/A)
            essential_fields = ['school_name', 'udise_code', 'know_more_link']
            has_meaningful_data = False

            for field in essential_fields:
                value = school_data.get(field, 'N/A')
                if value and value != 'N/A' and value.strip():
                    has_meaningful_data = True
                    break

            # If no meaningful data found, this might be an empty element
            if not has_meaningful_data:
                logger.debug(f"   ⚠️ Skipping element with no meaningful school data")
                return None

            # Add email extraction
            email = self.extract_email_from_school_element(school_element)
            school_data['email'] = email

            return school_data

        except Exception as e:
            logger.debug(f"   Error in enhanced school data extraction: {e}")
            return None

    def extract_single_school_data_standard(self, school_element):
        """Extract single school data using standard WebDriver methods"""
        try:
            school_data = {
                'school_name': 'N/A',
                'udise_code': 'N/A',
                'know_more_link': 'N/A',
                'district_name': getattr(self.current_district, 'districtName', 'N/A') if hasattr(self, 'current_district') and self.current_district else 'N/A',
                'state_name': getattr(self.current_state, 'stateName', 'N/A') if hasattr(self, 'current_state') and self.current_state else 'N/A'
            }

            # Extract school name
            try:
                name_selectors = [
                    ".school-name", ".name", "h5", "h4", "h3",
                    "[class*='name']", "[class*='title']"
                ]
                for selector in name_selectors:
                    try:
                        name_element = school_element.find_element(By.CSS_SELECTOR, selector)
                        if name_element and name_element.text.strip():
                            school_data['school_name'] = name_element.text.strip()
                            break
                    except:
                        continue
            except:
                pass

            # Extract UDISE code
            try:
                udise_selectors = [
                    "[class*='udise']", "[class*='code']", ".code", ".udise"
                ]
                for selector in udise_selectors:
                    try:
                        udise_element = school_element.find_element(By.CSS_SELECTOR, selector)
                        if udise_element and udise_element.text.strip():
                            school_data['udise_code'] = udise_element.text.strip()
                            break
                    except:
                        continue

                # Also try to find UDISE in text content
                if school_data['udise_code'] == 'N/A':
                    text_content = school_element.text
                    import re
                    udise_match = re.search(r'UDISE[:\s]*(\d+)', text_content, re.IGNORECASE)
                    if udise_match:
                        school_data['udise_code'] = udise_match.group(1)
            except:
                pass

            # Extract know more link
            try:
                link_selectors = [
                    "a[href*='schooldetail']", "a[href*='detail']",
                    ".know-more a", ".details a", "a"
                ]
                for selector in link_selectors:
                    try:
                        link_element = school_element.find_element(By.CSS_SELECTOR, selector)
                        href = link_element.get_attribute('href')
                        if href and 'schooldetail' in href:
                            school_data['know_more_link'] = href
                            break
                    except:
                        continue
            except:
                pass

            return school_data

        except Exception as e:
            logger.debug(f"   Error extracting school data: {e}")
            return None

    def extract_schools_from_current_page_with_email(self):
        """Enhanced schools extraction from current page with email functionality"""
        try:
            # Try multiple selectors to find school elements (same as base method)
            selectors_to_try = [
                ".accordion-body",
                ".accordion-item",
                "[class*='accordion']",
                ".card-body",
                ".result-item",
                "table tbody tr",
                ".school-item"
            ]

            school_elements = []

            for selector in selectors_to_try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    # Filter out potentially empty elements
                    filtered_elements = []
                    for element in elements:
                        try:
                            # Check if element has meaningful content
                            element_text = element.text.strip()
                            element_html = element.get_attribute('innerHTML')

                            # Skip if element is empty or has minimal content
                            if (element_text and len(element_text) > 10) or \
                               (element_html and len(element_html) > 50):
                                filtered_elements.append(element)
                        except:
                            # If we can't check the element, include it to be safe
                            filtered_elements.append(element)

                    if filtered_elements:
                        school_elements = filtered_elements
                        logger.debug(f"   Found {len(elements)} elements, filtered to {len(filtered_elements)} with selector: {selector}")
                        break

            if not school_elements:
                logger.warning("   ⚠️ No school elements found with any selector")
                # Enhanced debugging: Check page content and state
                page_text = self.driver.page_source[:2000]
                current_url = self.driver.current_url
                page_title = self.driver.title

                logger.warning(f"   🔍 Debug info:")
                logger.warning(f"      URL: {current_url}")
                logger.warning(f"      Title: {page_title}")
                logger.warning(f"      Page length: {len(self.driver.page_source)} chars")

                if "No records found" in page_text or "No data available" in page_text:
                    logger.info("   📄 Confirmed: No schools in this district")
                elif "loading" in page_text.lower() or "please wait" in page_text.lower():
                    logger.warning("   ⏳ Page appears to be still loading - waiting for completion...")
                    time.sleep(3)  # Restored from 1.5s to 3s for complete loading
                    # Retry element detection after adequate wait
                    for selector in selectors_to_try:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        if elements:
                            school_elements = elements
                            logger.info(f"   ✅ Found {len(elements)} school elements after retry with: {selector}")
                            break

                    if not school_elements:
                        logger.warning("   ❌ Still no elements found after retry")
                        return []
                else:
                    logger.warning("   ⚠️ Page may not have loaded properly or has different structure")
                    # Log a sample of page content for debugging
                    logger.warning(f"   📄 Page sample: {page_text[:500]}...")
                    return []

            # Process all schools with enhanced extraction including email
            schools_data = []
            email_found_count = 0
            skipped_elements = 0

            logger.debug(f"   🔍 Processing {len(school_elements)} detected school elements...")

            for i, school_element in enumerate(school_elements, 1):
                try:
                    school_data = self.extract_single_school_data_with_email(school_element)
                    if school_data:
                        schools_data.append(school_data)

                        # Count emails found
                        if school_data.get('email', 'N/A') != 'N/A':
                            email_found_count += 1
                    else:
                        skipped_elements += 1
                        logger.debug(f"   ⚠️ Skipped element {i} - no meaningful data")

                except Exception as e:
                    skipped_elements += 1
                    logger.debug(f"   ❌ Error processing element {i}: {e}")
                    continue

            # Log extraction summary
            logger.info(f"   📊 Processed {len(school_elements)} elements: {len(schools_data)} valid schools, {skipped_elements} skipped")
            if skipped_elements > 0:
                logger.warning(f"   ⚠️ {skipped_elements} elements were skipped due to missing data - this may indicate empty divs or non-school elements")

            # Reduced logging frequency - only log email stats every 10 pages or when significant
            if len(schools_data) > 0:
                logger.info(f"   📧 Email extraction: {email_found_count}/{len(schools_data)} schools have email addresses")
            return schools_data

        except Exception as e:
            logger.error(f"   Error extracting schools from page with email: {e}")
            return []

    def extract_schools_basic_data_enhanced(self):
        """Optimized schools extraction with incremental CSV saving and improved pagination"""
        try:
            schools_data = []
            page_number = 1
            start_time = time.time()

            logger.info("� Starting OPTIMIZED schools data extraction with robust pagination and incremental CSV saving...")
            logger.info("⚡ Performance optimizations: Reduced wait times, optimized scrolling, faster email extraction")

            while True:  # Remove hardcoded page limit - continue until no more pages
                logger.info(f"📄 Processing page {page_number}")

                # Reliable handling for first page
                if page_number == 1:
                    logger.info("🔍 First page - ensuring complete loading...")
                    # Full check for school elements to ensure reliability
                    self.wait_for_school_elements_to_load()
                    # Always scroll on first page to ensure all content is loaded
                    self.scroll_to_bottom()
                elif page_number % 5 == 0:
                    # Balanced scrolling: Scroll every 5th page for reliability
                    self.scroll_to_bottom()

                # Extract schools from current page using enhanced method with email extraction
                page_schools = self.extract_schools_from_current_page_with_email()

                # Reliable first page recovery
                if page_number == 1 and not page_schools:
                    logger.warning("⚠️ First page extraction failed - attempting reliable recovery...")
                    # Adequate wait time for recovery
                    time.sleep(4)  # Increased from 2s to 4s for better recovery
                    self.scroll_to_bottom()
                    # Additional wait after scrolling
                    time.sleep(1)
                    page_schools = self.extract_schools_from_current_page_with_email()

                    if page_schools:
                        logger.info(f"✅ First page recovery successful - found {len(page_schools)} schools")
                    else:
                        logger.error("❌ First page recovery failed - no schools extracted")

                # Save page schools to CSV immediately for crash protection
                if page_schools:
                    save_success = self.save_schools_to_csv_incremental(page_schools, page_number)
                    if not save_success:
                        logger.warning(f"⚠️ Failed to save page {page_number} to CSV, but continuing extraction")

                    # Check CSV file status after first page for debugging
                    if page_number == 1:
                        logger.info(f"🔍 Checking CSV file status after first page:")
                        self.check_csv_file_status()
                else:
                    # Log when no schools are found on a page
                    logger.warning(f"⚠️ No schools extracted from page {page_number}")

                schools_data.extend(page_schools)

                logger.info(f"   ✅ Extracted {len(page_schools)} schools from page {page_number}")
                logger.info(f"   📊 Total schools in memory: {len(schools_data)}")

                # Try to go to next page using enhanced method with retry
                logger.info(f"   🔄 Checking for next page after page {page_number}...")
                if not self.enhanced_click_next_page():
                    logger.info(f"📄 No more pages available after page {page_number}")
                    break

                page_number += 1

                # Balanced wait time for next page to load completely
                time.sleep(2)  # Increased from 1s to 2s for reliable page loading

                # Reliable check for new content with adequate timeout
                try:
                    # Wait for new content to load with reliable timeout
                    WebDriverWait(self.driver, 8).until(  # Restored from 4s to 8s for reliability
                        lambda driver: len(driver.find_elements(By.CSS_SELECTOR, ".accordion-body, .accordion-item, [class*='accordion']")) > 0
                    )
                except Exception as wait_error:
                    logger.warning(f"Timeout waiting for new page content: {wait_error}")
                    # Continue anyway as content might already be loaded

            # Performance summary
            total_time = time.time() - start_time
            avg_time_per_page = total_time / page_number if page_number > 0 else 0

            logger.info(f"✅ OPTIMIZED extraction completed: {len(schools_data)} total schools from {page_number} pages")
            logger.info(f"⚡ Performance Summary: {total_time:.1f}s total, {avg_time_per_page:.1f}s per page (target: <180s per page)")
            logger.info(f"📊 Pagination Summary: Processed {page_number} pages with no hardcoded limits")
            logger.info(f"📊 Average schools per page: {len(schools_data)/page_number:.1f}")
            logger.info(f"💾 CSV file saved: {self.current_csv_file} with {self.total_schools_saved} total schools")
            return schools_data

        except Exception as e:
            logger.error(f"Failed to extract schools data with enhanced method: {e}")
            return []

    def process_single_state_enhanced(self, target_state):
        """Enhanced processing for a single state with incremental CSV saving"""
        try:
            logger.info(f"🎯 Enhanced processing for state: {target_state['stateName']}")

            # Set current state
            self.current_state = target_state
            self.base_scraper.current_state = target_state

            # Initialize CSV file for incremental saving
            if not self.initialize_csv_file(target_state['stateName']):
                logger.error(f"❌ Failed to initialize CSV file for {target_state['stateName']}")
                return False

            # Initialize state data storage
            self.state_schools_with_links[target_state['stateName']] = []
            self.state_schools_no_links[target_state['stateName']] = []
            self.base_scraper.state_schools_with_links[target_state['stateName']] = []
            self.base_scraper.state_schools_no_links[target_state['stateName']] = []

            # Select the state
            if not self.select_state(target_state):
                logger.error(f"Failed to select state: {target_state['stateName']}")
                return False

            # Extract districts for this state
            districts = self.extract_districts_data()
            if not districts:
                logger.warning(f"No districts found for {target_state['stateName']}")
                self.base_scraper.save_state_data_to_csv(target_state['stateName'])
                return True

            logger.info(f"📋 Found {len(districts)} districts in {target_state['stateName']}")

            # Process each district with enhanced features
            for district_index, district in enumerate(districts, 1):
                logger.info(f"\n🏛️ Processing district {district_index}/{len(districts)}: {district['districtName']}")
                logger.info(f"💾 Writing to CSV file: {self.current_csv_file}")

                try:
                    # Select district
                    if self.select_district(district):
                        # Enhanced search with results per page optimization
                        if self.enhanced_click_search_button():
                            # Extract schools using enhanced method with incremental CSV saving
                            schools_data = self.extract_schools_basic_data_enhanced()
                        else:
                            logger.error(f"❌ Failed to click search button for district: {district['districtName']}")
                            schools_data = []

                        # Categorize schools
                        for school in schools_data:
                            if school.get('know_more_link') and school['know_more_link'] != 'N/A':
                                self.state_schools_with_links[target_state['stateName']].append(school)
                                self.base_scraper.state_schools_with_links[target_state['stateName']].append(school)
                            else:
                                self.state_schools_no_links[target_state['stateName']].append(school)
                                self.base_scraper.state_schools_no_links[target_state['stateName']].append(school)

                        logger.info(f"✅ Completed {district['districtName']}: {len(schools_data)} schools")
                    else:
                        logger.error(f"❌ Failed to select district: {district['districtName']}")

                except Exception as district_error:
                    logger.error(f"❌ Error processing district {district['districtName']}: {district_error}")
                    continue

            # Save data to CSV (legacy method - but incremental saving already done)
            self.base_scraper.save_state_data_to_csv(target_state['stateName'])

            total_schools = (len(self.state_schools_with_links.get(target_state['stateName'], [])) +
                           len(self.state_schools_no_links.get(target_state['stateName'], [])))
            logger.info(f"✅ Enhanced processing completed for {target_state['stateName']}: {total_schools} total schools")
            logger.info(f"💾 Incremental CSV file: {self.current_csv_file} with {self.total_schools_saved} schools saved")

            # Finalize CSV file
            self.finalize_csv_file()

            return True

        except Exception as e:
            logger.error(f"❌ Error in enhanced single state processing: {e}")
            return False

    def process_single_state_single_district(self, target_state, target_district):
        """Enhanced processing for a single state and single district with incremental CSV saving"""
        try:
            logger.info(f"🎯 Enhanced processing for district: {target_district['districtName']} in {target_state['stateName']}")

            # Set current state and district
            self.current_state = target_state
            self.current_district = target_district
            self.base_scraper.current_state = target_state
            self.base_scraper.current_district = target_district

            # Initialize CSV file for incremental saving
            if not self.initialize_csv_file(target_state['stateName']):
                logger.error(f"❌ Failed to initialize CSV file for {target_state['stateName']}")
                return False

            # Initialize state data storage
            self.state_schools_with_links[target_state['stateName']] = []
            self.state_schools_no_links[target_state['stateName']] = []
            self.base_scraper.state_schools_with_links[target_state['stateName']] = []
            self.base_scraper.state_schools_no_links[target_state['stateName']] = []

            # Select the state
            if not self.select_state(target_state):
                logger.error(f"Failed to select state: {target_state['stateName']}")
                return False

            # Select the district
            if not self.select_district(target_district):
                logger.error(f"Failed to select district: {target_district['districtName']}")
                return False

            # Enhanced search with results per page optimization
            if self.enhanced_click_search_button():
                # Extract schools using enhanced method
                schools_data = self.extract_schools_basic_data_enhanced()
            else:
                logger.error(f"❌ Failed to click search button for district: {target_district['districtName']}")
                schools_data = []

            # Categorize schools
            for school in schools_data:
                if school.get('know_more_link') and school['know_more_link'] != 'N/A':
                    self.state_schools_with_links[target_state['stateName']].append(school)
                    self.base_scraper.state_schools_with_links[target_state['stateName']].append(school)
                else:
                    self.state_schools_no_links[target_state['stateName']].append(school)
                    self.base_scraper.state_schools_no_links[target_state['stateName']].append(school)

            # Save data to CSV (legacy method - but incremental saving already done)
            self.base_scraper.save_state_data_to_csv(target_state['stateName'])

            logger.info(f"✅ Enhanced processing completed for {target_district['districtName']}: {len(schools_data)} schools")
            logger.info(f"💾 Incremental CSV file: {self.current_csv_file} with {self.total_schools_saved} schools saved")

            # Finalize CSV file
            self.finalize_csv_file()

            return True

        except Exception as e:
            logger.error(f"❌ Error in enhanced single district processing: {e}")
            return False


class MultiThreadedPhase2Processor:
    """Multi-threaded Phase 2 processor with 2 worker threads"""

    def __init__(self, state_name, csv_file):
        self.state_name = state_name
        self.csv_file = csv_file

        # Thread-safe locks
        self.csv_lock = threading.Lock()
        self.stats_lock = threading.Lock()

        # Statistics tracking
        self.processed_count = 0
        self.success_count = 0
        self.fail_count = 0

        # CSV file management
        self.incremental_csv_file = None
        self.csv_headers_written = False

        # Setup incremental CSV file
        self.setup_incremental_csv()

    def setup_incremental_csv(self):
        """Setup incremental CSV file for thread-safe writing"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            clean_state = self.state_name.replace(' ', '_').replace('&', 'and').replace('/', '_').upper()
            self.incremental_csv_file = f"{clean_state}_phase2_multithreaded_{timestamp}.csv"
            logger.info(f"   📝 Setup multi-threaded CSV: {self.incremental_csv_file}")
            return True
        except Exception as e:
            logger.error(f"   ❌ Error setting up incremental CSV: {e}")
            return False

    def write_to_incremental_csv(self, combined_data):
        """Thread-safe write of a single school record to incremental CSV"""
        try:
            if not self.incremental_csv_file:
                logger.warning("   ⚠️ Incremental CSV file not setup")
                return False

            # Thread-safe CSV writing
            with self.csv_lock:
                # Convert to DataFrame for consistent handling
                df = pd.DataFrame([combined_data])

                # Write headers if first record
                if not self.csv_headers_written:
                    df.to_csv(self.incremental_csv_file, mode='w', index=False, header=True)
                    self.csv_headers_written = True
                    logger.debug(f"   📝 Created multi-threaded CSV with headers")
                else:
                    # Append data without headers
                    df.to_csv(self.incremental_csv_file, mode='a', index=False, header=False)

                logger.debug(f"   📝 Thread-safe append: 1 record to CSV")

            return True

        except Exception as e:
            logger.error(f"   ❌ Error in thread-safe CSV writing: {e}")
            return False

    def update_stats(self, processed=0, success=0, fail=0):
        """Thread-safe update of processing statistics"""
        with self.stats_lock:
            self.processed_count += processed
            self.success_count += success
            self.fail_count += fail

    def setup_standard_driver(self):
        """Initialize standard Chrome browser driver with automatic driver management"""
        try:
            # Setup Chrome options for Phase 2 data extraction
            options = Options()

            # Core stability options
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-blink-features=AutomationControlled")

            # Performance optimizations (KEEP JavaScript enabled for dynamic content)
            options.add_argument("--disable-images")  # Speed optimization
            options.add_argument("--disable-plugins")  # Speed optimization
            # NOTE: JavaScript is ENABLED for proper page functionality

            # Memory and resource optimizations
            options.add_argument("--memory-pressure-off")
            options.add_argument("--max_old_space_size=4096")

            # Try automatic ChromeDriver management first
            try:
                from webdriver_manager.chrome import ChromeDriverManager
                logger.debug("   🔄 Using webdriver-manager for Phase 2 ChromeDriver setup...")

                service = Service(ChromeDriverManager().install())
                driver = webdriver.Chrome(service=service, options=options)
                logger.debug("   ✅ Phase 2 ChromeDriver automatically managed")

            except ImportError:
                logger.debug("   ⚠️ webdriver-manager not available for Phase 2, using system ChromeDriver...")
                driver = webdriver.Chrome(options=options)
                logger.debug("   ✅ Using system ChromeDriver for Phase 2")

            except Exception as webdriver_manager_error:
                logger.debug(f"   ⚠️ webdriver-manager failed for Phase 2: {webdriver_manager_error}")
                logger.debug("   🔄 Falling back to system ChromeDriver for Phase 2...")
                driver = webdriver.Chrome(options=options)
                logger.debug("   ✅ Using system ChromeDriver for Phase 2")

            driver.maximize_window()

            # Balanced timeouts for Phase 2 processing
            driver.implicitly_wait(5)  # Increased for dynamic content
            driver.set_page_load_timeout(25)  # Increased for detailed pages

            logger.debug("✅ Standard Chrome browser driver initialized for multi-threaded processing")
            return driver

        except Exception as e:
            logger.error(f"❌ Failed to initialize standard Chrome driver for Phase 2: {e}")

            # Provide specific troubleshooting for ChromeDriver version issues
            error_message = str(e)
            if "This version of ChromeDriver only supports Chrome version" in error_message:
                logger.error("🔧 PHASE 2 CHROMEDRIVER VERSION MISMATCH:")
                logger.error("   Install webdriver-manager: pip install webdriver-manager")
            elif "cannot connect to chrome" in error_message:
                logger.error("🔧 PHASE 2 CHROME CONNECTION ISSUE:")
                logger.error("   Ensure Chrome browser is properly installed")

            raise

    def extract_school_data_standard(self, driver, url, max_retries=2):
        """Extract school data using standard WebDriver with immediate browser refresh"""
        for attempt in range(max_retries):
            try:
                logger.debug(f"   🌐 Navigating to school detail page: {url}")

                # Step 1: Navigate to the URL
                driver.get(url)

                # Step 2: IMMEDIATE BROWSER REFRESH (critical for dynamic content)
                logger.debug(f"   🔄 Performing immediate browser refresh...")
                driver.refresh()

                # Step 3: Wait for refresh to complete
                time.sleep(3)

                # Step 4: Verify page is loaded after refresh
                WebDriverWait(driver, 10).until(
                    lambda driver: driver.execute_script("return document.readyState") == "complete"
                )

                time.sleep(2)  # Additional wait for dynamic content after refresh

                # Initialize comprehensive data structure for all extracted fields (matching original)
                data = {
                    # School identification
                    'detail_school_name': 'N/A',
                    'source_url': url,
                    'extraction_timestamp': datetime.now().isoformat(),

                    # Basic Details section (.innerPad div with .schoolInfoCol elements)
                    'academic_year': 'N/A',
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

                    # Student Enrollment section (.bg-white div with .H3Value elements)
                    'total_students': 'N/A',
                    'total_boys': 'N/A',
                    'total_girls': 'N/A',
                    'enrollment_class_range': 'N/A',

                    # Teacher section (similar structure with Total Teachers/Male/Female)
                    'total_teachers': 'N/A',
                    'male_teachers': 'N/A',
                    'female_teachers': 'N/A'
                }

                # Get page content for extraction
                page_text = driver.page_source

                # Extract school ID for verification
                import re
                url_school_id = re.search(r'/(\d+)/\d+$', url)
                expected_school_id = url_school_id.group(1) if url_school_id else "unknown"

                logger.debug(f"   📄 Expected school ID: {expected_school_id}")
                logger.debug(f"   📄 Page content length: {len(page_text)} characters")

                # Verify we're on the correct page
                if expected_school_id not in page_text and expected_school_id != "unknown":
                    logger.warning(f"   ⚠️ School ID {expected_school_id} not found in page content")
                    # Continue with extraction anyway, but mark as potential issue
                    data['detail_school_name'] = f"POTENTIAL_ISSUE_{expected_school_id}"

                # EXTRACT DATA FROM SPECIFIC HTML STRUCTURES (COMPREHENSIVE RESTORATION)
                self.extract_comprehensive_data(data, page_text, driver)

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
                        logger.debug(f"   ✅ EXCELLENT extraction: {critical_fields}/2 critical, {extracted_fields} total fields")
                    elif critical_fields >= 1:
                        logger.debug(f"   ⚠️ PARTIAL extraction: {critical_fields}/2 critical, {extracted_fields} total fields")
                    else:
                        logger.warning(f"   ❌ FAILED extraction: {critical_fields}/2 critical, {extracted_fields} total fields")

                except Exception as e:
                    logger.debug(f"   Error in data validation: {e}")
                    data['extraction_status'] = 'ERROR'
                    data['fields_extracted'] = 0
                    data['critical_fields_extracted'] = 0

                return data

            except Exception as e:
                logger.warning(f"   ⚠️ Failed to extract data from {url} (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    logger.info(f"   ⏳ Retrying in 3 seconds...")
                    time.sleep(3)
                else:
                    return None

        return None

    def extract_comprehensive_data(self, data, page_text, driver):
        """Extract comprehensive data using the complete original extraction logic"""
        try:
            import re

            # 1. BASIC DETAILS SECTION - Extract from .innerPad div with .schoolInfoCol elements
            try:
                logger.debug(f"   📋 Extracting Basic Details from .innerPad div...")

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

                        # Also check for Academic Year in the header section
                        try:
                            academic_year_element = driver.find_element(By.CSS_SELECTOR, ".innerPad .fw-600")
                            academic_year_text = academic_year_element.text.strip()
                            if "Academic Year" in academic_year_text:
                                # Extract year from text like "Academic Year : 2023-24"
                                year_match = re.search(r'Academic Year[:\s]*([^<\n]+)', academic_year_text)
                                if year_match:
                                    data['academic_year'] = year_match.group(1).strip()
                                    logger.debug(f"   Extracted Academic Year: {data['academic_year']}")
                        except:
                            logger.debug("   Academic Year not found in header")

                except Exception as e:
                    logger.debug(f"   Error finding basic details elements: {e}")

                # Fallback: Use regex patterns for basic details
                if data['academic_year'] == 'N/A':
                    academic_year_match = re.search(r'Academic Year[:\s]*(?:<[^>]*>)*([^<\n]+)', page_text, re.IGNORECASE)
                    if academic_year_match:
                        data['academic_year'] = academic_year_match.group(1).strip()

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

                if data['class_from'] == 'N/A':
                    class_from_match = re.search(r'Class From</p></div><div[^>]*class="blueCol">([^<]+)', page_text, re.IGNORECASE)
                    if class_from_match:
                        data['class_from'] = class_from_match.group(1).strip()

                if data['class_to'] == 'N/A':
                    class_to_match = re.search(r'Class To</p></div><div[^>]*class="blueCol">([^<]+)', page_text, re.IGNORECASE)
                    if class_to_match:
                        data['class_to'] = class_to_match.group(1).strip()

                if data['national_management'] == 'N/A':
                    national_mgmt_match = re.search(r'National Management</p></div><div[^>]*class="blueCol">([^<]+)', page_text, re.IGNORECASE)
                    if national_mgmt_match:
                        data['national_management'] = national_mgmt_match.group(1).strip()

                if data['state_management'] == 'N/A':
                    state_mgmt_match = re.search(r'State Management</p></div><div[^>]*class="blueCol">([^<]+)', page_text, re.IGNORECASE)
                    if state_mgmt_match:
                        data['state_management'] = state_mgmt_match.group(1).strip()

                if data['affiliation_board_sec'] == 'N/A':
                    affil_sec_match = re.search(r'Affiliation Board Sec\.</p></div><div[^>]*class="blueCol">([^<]+)', page_text, re.IGNORECASE)
                    if affil_sec_match:
                        data['affiliation_board_sec'] = affil_sec_match.group(1).strip()

                if data['affiliation_board_hsec'] == 'N/A':
                    affil_hsec_match = re.search(r'Affiliation Board HSec\.</p></div><div[^>]*class="blueCol">([^<]+)', page_text, re.IGNORECASE)
                    if affil_hsec_match:
                        data['affiliation_board_hsec'] = affil_hsec_match.group(1).strip()

                # Combine class range if both from and to are found
                if data['class_from'] != 'N/A' and data['class_to'] != 'N/A':
                    data['class_range'] = f"{data['class_from']} To {data['class_to']}"

                # Count extracted basic details fields
                basic_fields_extracted = sum(1 for field in ['location', 'school_category', 'school_type', 'year_of_establishment',
                                                            'national_management', 'state_management', 'affiliation_board_sec',
                                                            'affiliation_board_hsec'] if data[field] != 'N/A')

                logger.debug(f"   ✅ Basic Details extracted: {basic_fields_extracted}/8 fields")

            except Exception as e:
                logger.debug(f"   Error extracting basic details: {e}")

            # Continue with student and teacher extraction in next part...
            self.extract_student_teacher_data(data, page_text, driver)
            self.extract_school_name_data(data, page_text, driver)

        except Exception as e:
            logger.debug(f"   Error in comprehensive data extraction: {e}")

    def extract_student_teacher_data(self, data, page_text, driver):
        """Extract student enrollment and teacher data using original patterns"""
        try:
            import re

            # 2. STUDENT ENROLLMENT SECTION - Extract from .bg-white div with .H3Value elements
            try:
                logger.debug(f"   👥 Extracting Student Enrollment from .bg-white div with .H3Value elements...")

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

                if data['total_boys'] == 'N/A':
                    boys_patterns = [
                        r'Boys[^>]*</p>\s*<p[^>]*class="H3Value[^>]*>\s*(\d+)\s*</p>',
                        r'Boys[^>]*>\s*(\d+)\s*<',
                        r'Boys[:\s]*(\d+)'
                    ]
                    for pattern in boys_patterns:
                        match = re.search(pattern, page_text, re.IGNORECASE)
                        if match:
                            data['total_boys'] = match.group(1).strip()
                            logger.debug(f"   Found Boys (regex): {data['total_boys']}")
                            break

                if data['total_girls'] == 'N/A':
                    girls_patterns = [
                        r'Girls[^>]*</p>\s*<p[^>]*class="H3Value[^>]*>\s*(\d+)\s*</p>',
                        r'Girls[^>]*>\s*(\d+)\s*<',
                        r'Girls[:\s]*(\d+)'
                    ]
                    for pattern in girls_patterns:
                        match = re.search(pattern, page_text, re.IGNORECASE)
                        if match:
                            data['total_girls'] = match.group(1).strip()
                            logger.debug(f"   Found Girls (regex): {data['total_girls']}")
                            break

                logger.debug(f"   ✅ Student Enrollment extracted: Total={data['total_students']}, Boys={data['total_boys']}, Girls={data['total_girls']}")

            except Exception as e:
                logger.debug(f"   Error extracting student enrollment: {e}")

            # 3. TEACHER SECTION - Extract from similar HTML structure with Total Teachers/Male/Female
            try:
                logger.debug(f"   👨‍🏫 Extracting Teacher data from similar HTML structure...")

                # Try to find Teacher section using Selenium elements first
                try:
                    # Look for teacher-related H3Value elements
                    all_h3_elements = driver.find_elements(By.CSS_SELECTOR, ".H3Value")
                    teacher_section_found = False

                    for element in all_h3_elements:
                        try:
                            # Get the parent container to find the label
                            parent = element.find_element(By.XPATH, "..")
                            parent_text = parent.text.strip().lower()
                            value = element.text.strip()

                            if value.isdigit():
                                if "total teachers" in parent_text:
                                    data['total_teachers'] = value
                                    logger.debug(f"   Found Total Teachers: {value}")
                                    teacher_section_found = True
                                elif "male" in parent_text and "teacher" in parent_text:
                                    data['male_teachers'] = value
                                    logger.debug(f"   Found Male Teachers: {value}")
                                    teacher_section_found = True
                                elif "female" in parent_text and "teacher" in parent_text:
                                    data['female_teachers'] = value
                                    logger.debug(f"   Found Female Teachers: {value}")
                                    teacher_section_found = True
                                elif "male" in parent_text and teacher_section_found and data['male_teachers'] == 'N/A':
                                    # Sometimes just "Male" without "Teacher"
                                    data['male_teachers'] = value
                                    logger.debug(f"   Found Male Teachers (short): {value}")
                                elif "female" in parent_text and teacher_section_found and data['female_teachers'] == 'N/A':
                                    # Sometimes just "Female" without "Teacher"
                                    data['female_teachers'] = value
                                    logger.debug(f"   Found Female Teachers (short): {value}")
                        except Exception as e:
                            logger.debug(f"   Error processing teacher H3Value element: {e}")
                            continue
                except Exception as e:
                    logger.debug(f"   Error finding teacher H3Value elements: {e}")

                # Fallback: Use regex patterns for teacher data
                if data['total_teachers'] == 'N/A':
                    teacher_patterns = [
                        r'Total Teachers[^>]*</p>\s*<p[^>]*class="H3Value[^>]*>\s*(\d+)\s*</p>',
                        r'Total Teachers[^>]*>\s*(\d+)\s*<',
                        r'Total Teachers[:\s]*(\d+)'
                    ]
                    for pattern in teacher_patterns:
                        match = re.search(pattern, page_text, re.IGNORECASE)
                        if match:
                            data['total_teachers'] = match.group(1).strip()
                            logger.debug(f"   Found Total Teachers (regex): {data['total_teachers']}")
                            break

                if data['male_teachers'] == 'N/A':
                    male_patterns = [
                        r'Male[^>]*</p>\s*<p[^>]*class="H3Value[^>]*>\s*(\d+)\s*</p>',
                        r'Male Teachers[^>]*>\s*(\d+)\s*<',
                        r'Male[:\s]*(\d+)'
                    ]
                    for pattern in male_patterns:
                        match = re.search(pattern, page_text, re.IGNORECASE)
                        if match:
                            data['male_teachers'] = match.group(1).strip()
                            logger.debug(f"   Found Male Teachers (regex): {data['male_teachers']}")
                            break

                if data['female_teachers'] == 'N/A':
                    female_patterns = [
                        r'Female[^>]*</p>\s*<p[^>]*class="H3Value[^>]*>\s*(\d+)\s*</p>',
                        r'Female Teachers[^>]*>\s*(\d+)\s*<',
                        r'Female[:\s]*(\d+)'
                    ]
                    for pattern in female_patterns:
                        match = re.search(pattern, page_text, re.IGNORECASE)
                        if match:
                            data['female_teachers'] = match.group(1).strip()
                            logger.debug(f"   Found Female Teachers (regex): {data['female_teachers']}")
                            break

                logger.debug(f"   ✅ Teacher data extracted: Total={data['total_teachers']}, Male={data['male_teachers']}, Female={data['female_teachers']}")

            except Exception as e:
                logger.debug(f"   Error extracting teacher data: {e}")

        except Exception as e:
            logger.debug(f"   Error in student/teacher data extraction: {e}")

    def extract_school_name_data(self, data, page_text, driver):
        """Extract school name using original patterns and fallback strategies"""
        try:
            import re

            # 4. SCHOOL NAME - Extract from page title, header, or breadcrumb
            try:
                logger.debug(f"   🏫 Extracting School Name...")

                # Method 1: Try to get school name from page title
                page_title = driver.title
                if page_title and page_title != "Know Your School" and "UDISE" not in page_title:
                    clean_title = page_title.replace("Know Your School", "").replace("-", "").strip()
                    # Filter out generic titles
                    if clean_title and len(clean_title) > 3 and clean_title not in ['School Details', 'School Detail', 'Details']:
                        data['detail_school_name'] = clean_title
                        logger.debug(f"   Found school name from title: {clean_title}")

                # Method 2: Try to find school name in breadcrumb or header elements
                if data['detail_school_name'] == 'N/A':
                    try:
                        # Look for breadcrumb or header elements
                        name_selectors = [
                            "h1", "h2", "h3",
                            ".breadcrumb", ".page-title", ".school-name",
                            "[class*='title']", "[class*='name']", "[class*='header']"
                        ]

                        for selector in name_selectors:
                            elements = driver.find_elements(By.CSS_SELECTOR, selector)
                            for element in elements:
                                text = element.text.strip()
                                if text and len(text) > 5 and len(text) < 200:
                                    # Filter out common non-school-name text
                                    if not any(skip in text.lower() for skip in ['know your school', 'udise', 'dashboard', 'menu', 'search']):
                                        data['detail_school_name'] = text
                                        logger.debug(f"   Found school name from {selector}: {text}")
                                        break
                            if data['detail_school_name'] != 'N/A':
                                break
                    except Exception as e:
                        logger.debug(f"   Error finding school name in elements: {e}")

                # Method 3: Extract from page content using regex
                if data['detail_school_name'] == 'N/A':
                    name_patterns = [
                        r'School Name[:\s]*([^\n<]+)',
                        r'Name of School[:\s]*([^\n<]+)',
                        r'Institution Name[:\s]*([^\n<]+)'
                    ]
                    for pattern in name_patterns:
                        match = re.search(pattern, page_text, re.IGNORECASE)
                        if match:
                            school_name = match.group(1).strip()
                            if school_name and len(school_name) > 3:
                                data['detail_school_name'] = school_name
                                logger.debug(f"   Found school name from regex: {school_name}")
                                break

                # Fallback: Use school ID as identifier
                if data['detail_school_name'] == 'N/A' or data['detail_school_name'].startswith('POTENTIAL_ISSUE'):
                    # Extract school ID from URL
                    url_school_id = re.search(r'/(\d+)/\d+$', data['source_url'])
                    expected_school_id = url_school_id.group(1) if url_school_id else "unknown"
                    data['detail_school_name'] = f"School_ID_{expected_school_id}"
                    logger.debug(f"   Using school ID as name: {data['detail_school_name']}")

            except Exception as e:
                logger.debug(f"   Error extracting school name: {e}")
                # Emergency fallback
                url_school_id = re.search(r'/(\d+)/\d+$', data['source_url'])
                expected_school_id = url_school_id.group(1) if url_school_id else "unknown"
                data['detail_school_name'] = f"School_ID_{expected_school_id}"

            # Strategy 5: Fallback - Extract any visible numbers as potential data
            if data['total_students'] == 'N/A' or data['total_teachers'] == 'N/A':
                try:
                    # Get all visible text elements
                    text_elements = driver.find_elements(By.CSS_SELECTOR, "span, div, p, td, th")

                    for element in text_elements:
                        try:
                            text = element.text.strip()
                            if text.isdigit() and 1 <= int(text) <= 10000:  # Reasonable range for school data
                                # Check surrounding context
                                parent_text = ""
                                try:
                                    parent = element.find_element(By.XPATH, "..")
                                    parent_text = parent.text.lower()
                                except:
                                    pass

                                # Assign based on context or position
                                if ('student' in parent_text or 'enrollment' in parent_text) and data['total_students'] == 'N/A':
                                    data['total_students'] = text
                                    logger.debug(f"   Found students from context: {text}")
                                elif ('teacher' in parent_text or 'staff' in parent_text or 'faculty' in parent_text) and data['total_teachers'] == 'N/A':
                                    data['total_teachers'] = text
                                    logger.debug(f"   Found teachers from context: {text}")
                        except:
                            continue
                except Exception as e:
                    logger.debug(f"   Error in fallback extraction: {e}")

        except Exception as e:
            logger.debug(f"   Error in school name extraction: {e}")

    def worker_thread(self, thread_id, schools_batch):
        """Worker thread function for processing a batch of schools using standard WebDriver"""
        driver = None
        try:
            logger.info(f"   🧵 Thread-{thread_id}: Starting with {len(schools_batch)} schools")

            # Setup isolated standard WebDriver for this thread (no undetected-chromedriver)
            driver = self.setup_standard_driver()

            thread_success_count = 0
            thread_fail_count = 0

            # Process each school in the batch
            for idx, (_, school) in enumerate(schools_batch.iterrows(), 1):
                try:
                    school_name = school.get('school_name', f'School_{idx}')
                    logger.info(f"   🧵 Thread-{thread_id}: Processing school {idx}/{len(schools_batch)}: {school_name}")

                    # Extract Phase 2 data using standard WebDriver
                    extracted_data = self.extract_school_data_standard(driver, school['know_more_link'])

                    if extracted_data:
                        # Combine original and extracted data
                        combined_data = school.to_dict()
                        combined_data.update(extracted_data)

                        # Thread-safe write to incremental CSV
                        if self.write_to_incremental_csv(combined_data):
                            thread_success_count += 1
                            logger.info(f"   🧵 Thread-{thread_id}: ✅ School {idx} processed and saved")
                        else:
                            thread_fail_count += 1
                            logger.warning(f"   🧵 Thread-{thread_id}: ⚠️ School {idx} processed but CSV write failed")
                    else:
                        thread_fail_count += 1
                        logger.warning(f"   🧵 Thread-{thread_id}: ❌ School {idx} extraction failed")

                    # Brief pause between schools
                    time.sleep(0.2)

                except Exception as e:
                    thread_fail_count += 1
                    logger.warning(f"   🧵 Thread-{thread_id}: ⚠️ Failed to process school {idx}: {e}")
                    continue

            # Update thread-safe statistics
            self.update_stats(
                processed=len(schools_batch),
                success=thread_success_count,
                fail=thread_fail_count
            )

            # Cleanup WebDriver
            try:
                if driver:
                    driver.quit()
                    logger.debug(f"   🧵 Thread-{thread_id}: Standard WebDriver cleaned up successfully")
            except Exception as cleanup_error:
                logger.warning(f"   🧵 Thread-{thread_id}: WebDriver cleanup error: {cleanup_error}")

            logger.info(f"   🧵 Thread-{thread_id}: Completed - Success: {thread_success_count}, Failed: {thread_fail_count}")
            return True

        except Exception as e:
            logger.error(f"   🧵 Thread-{thread_id}: ❌ Critical error: {e}")
            # Attempt cleanup on error
            try:
                if driver:
                    driver.quit()
                    logger.debug(f"   🧵 Thread-{thread_id}: Emergency standard WebDriver cleanup completed")
            except:
                pass  # Ignore cleanup errors during exception handling
            return False

    def filter_phase2_ready_schools(self, df):
        """Filter schools that are ready for Phase 2 processing"""
        try:
            # Filter schools with valid know_more_link
            phase2_schools = df[
                (df['know_more_link'].notna()) &
                (df['know_more_link'] != 'N/A') &
                (df['know_more_link'].str.contains('schooldetail', na=False))
            ].copy()

            logger.info(f"   📊 Found {len(phase2_schools)} schools ready for Phase 2 processing")
            return phase2_schools

        except Exception as e:
            logger.error(f"   ❌ Error filtering Phase 2 ready schools: {e}")
            return pd.DataFrame()

    def process_with_threads(self):
        """Main processing method using 2 worker threads"""
        try:
            logger.info(f"   📊 Loading data from: {self.csv_file}")

            # Load data
            df = pd.read_csv(self.csv_file)
            logger.info(f"   📊 Loaded {len(df)} total records")

            # Filter Phase 2 ready schools
            schools_to_process = self.filter_phase2_ready_schools(df)

            if len(schools_to_process) == 0:
                logger.info("   ✅ No schools ready for Phase 2 processing")
                return True

            logger.info(f"   🎯 Processing {len(schools_to_process)} schools with 2 worker threads")
            logger.info(f"   📝 Multi-threaded CSV: {self.incremental_csv_file}")

            # Split data into 2 batches for the threads
            total_schools = len(schools_to_process)
            mid_point = total_schools // 2

            batch_1 = schools_to_process.iloc[:mid_point]
            batch_2 = schools_to_process.iloc[mid_point:]

            logger.info(f"   📦 Thread-1 batch: {len(batch_1)} schools")
            logger.info(f"   📦 Thread-2 batch: {len(batch_2)} schools")

            # Execute threads
            start_time = time.time()

            with ThreadPoolExecutor(max_workers=2) as executor:
                # Submit both worker threads
                future_1 = executor.submit(self.worker_thread, 1, batch_1)
                future_2 = executor.submit(self.worker_thread, 2, batch_2)

                # Monitor progress and wait for completion
                completed_threads = 0
                for future in as_completed([future_1, future_2]):
                    completed_threads += 1

                    try:
                        result = future.result()
                        if result:
                            logger.info(f"   ✅ Thread completed successfully")
                        else:
                            logger.warning(f"   ⚠️ Thread completed with errors")
                    except Exception as exc:
                        logger.error(f"   ❌ Thread generated an exception: {exc}")

                    # Show progress update
                    elapsed_time = time.time() - start_time

                    with self.stats_lock:
                        current_processed = self.processed_count
                        current_success = self.success_count
                        current_fail = self.fail_count

                    logger.info(f"   📊 THREAD COMPLETION UPDATE:")
                    logger.info(f"      🧵 Threads completed: {completed_threads}/2")
                    logger.info(f"      🎯 Schools processed: {current_processed}/{total_schools}")
                    logger.info(f"      ✅ Successful: {current_success}")
                    logger.info(f"      ❌ Failed: {current_fail}")
                    logger.info(f"      ⏱️ Elapsed: {elapsed_time/60:.1f} minutes")

            # Final statistics
            with self.stats_lock:
                final_processed = self.processed_count
                final_success = self.success_count
                final_fail = self.fail_count

            logger.info(f"   ✅ Multi-threaded processing completed for {self.state_name}")
            logger.info(f"   📊 Final results: {final_success}/{final_processed} successful, {final_fail} failed")

            # Upload to Google Sheets if configured
            if final_success > 0:
                self.upload_to_google_sheets()

            return True

        except Exception as e:
            logger.error(f"   ❌ Error in multi-threaded processing: {e}")
            return False

    def upload_to_google_sheets(self):
        """Upload results to Google Sheets (preserving existing functionality)"""
        try:
            # Import Google Sheets functionality
            try:
                from phase2_automated_processor import GOOGLE_SHEETS_ENABLED, GoogleSheetsUploader

                if GOOGLE_SHEETS_ENABLED and self.incremental_csv_file:
                    logger.info(f"   📤 Uploading {self.state_name} data to Google Sheets...")

                    sheets_uploader = GoogleSheetsUploader()
                    if sheets_uploader.authenticate():
                        upload_success = sheets_uploader.upload_phase2_data(self.incremental_csv_file, self.state_name)
                        if upload_success:
                            logger.info(f"   ✅ Google Sheets upload completed for {self.state_name}")
                        else:
                            logger.warning(f"   ⚠️ Google Sheets upload failed for {self.state_name} (CSV backup available)")
                    else:
                        logger.warning(f"   ⚠️ Google Sheets authentication failed for {self.state_name}")
                else:
                    logger.info(f"   ℹ️ Google Sheets upload disabled or CSV file not available")

            except ImportError as e:
                logger.warning(f"   ⚠️ Google Sheets functionality not available: {e}")
                logger.info(f"   📁 CSV file saved locally: {self.incremental_csv_file}")

        except Exception as e:
            logger.error(f"   ❌ Error in Google Sheets upload: {e}")
            logger.info(f"   📁 CSV file saved locally: {self.incremental_csv_file}")


class SequentialStateProcessor:
    def __init__(self):
        self.processed_states = []
        self.failed_states = []
        self.total_schools_processed = 0
        self.start_time = None
        self.max_retries = 3
        self.retry_delay = 30  # seconds

        # Multi-threading configuration
        self.use_multithreading = True  # Default to multi-threading

        # State list (all 38 Indian states)
        self.states_list = [
            "ANDAMAN & NICOBAR ISLANDS",
            "ANDHRA PRADESH",
            "ARUNACHAL PRADESH",
            "ASSAM",
            "BIHAR",
            "CHANDIGARH",
            "CHHATTISGARH",
            "DADRA & NAGAR HAVELI AND DAMAN & DIU",
            "DELHI",
            "GOA",
            "GUJARAT",
            "HARYANA",
            "HIMACHAL PRADESH",
            "JAMMU & KASHMIR",
            "JHARKHAND",
            "KARNATAKA",
            "KENDRIYA VIDYALAYA SANGHATHAN",
            "KERALA",
            "LADAKH",
            "LAKSHADWEEP",
            "MADHYA PRADESH",
            "MAHARASHTRA",
            "MANIPUR",
            "MEGHALAYA",
            "MIZORAM",
            "NAGALAND",
            "NAVODAYA VIDYALAYA SAMITI",
            "ODISHA",
            "PUDUCHERRY",
            "PUNJAB",
            "RAJASTHAN",
            "SIKKIM",
            "TAMILNADU",
            "TELANGANA",
            "TRIPURA",
            "UTTARAKHAND",
            "UTTAR PRADESH",
            "WEST BENGAL"
        ]

    def configure_threading(self):
        """Configure threading options for Phase 2 processing"""
        print("\n" + "="*60)
        print("🧵 PHASE 2 THREADING CONFIGURATION")
        print("="*60)
        print("Choose Phase 2 processing mode:")
        print("1. Multi-threaded (2 worker threads) - RECOMMENDED")
        print("   ✅ Faster processing")
        print("   ✅ Better resource utilization")
        print("   ✅ Maintains data integrity")
        print("   ✅ Uses standard Chrome WebDriver")
        print("2. Single-threaded (1 worker thread)")
        print("   ✅ More conservative approach")
        print("   ✅ Lower resource usage")
        print("   ✅ Uses undetected-chromedriver")
        print("="*60)

        while True:
            try:
                choice = input("\nEnter your choice (1-2): ").strip()
                if choice == '1':
                    self.use_multithreading = True
                    print("✅ Multi-threaded processing enabled (2 worker threads)")
                    return
                elif choice == '2':
                    self.use_multithreading = False
                    print("✅ Single-threaded processing enabled")
                    return
                else:
                    print("❌ Invalid choice. Please enter 1 or 2.")
            except KeyboardInterrupt:
                print("\n\n👋 Using default multi-threaded mode...")
                self.use_multithreading = True
                return
            except Exception as e:
                print(f"❌ Error reading input: {e}")
                self.use_multithreading = True
                return

    def show_interactive_menu(self):
        """Display interactive menu for processing options"""
        print("\n" + "="*80)
        print("🚀 ENHANCED SEQUENTIAL STATE PROCESSOR")
        print("="*80)

        # Show current threading configuration
        if self.use_multithreading:
            threading_status = "Multi-threaded (2 workers, Standard WebDriver)"
        else:
            threading_status = "Single-threaded (Undetected WebDriver)"
        print(f"🧵 Current Phase 2 mode: {threading_status}")
        print(f"🌐 Phase 1 WebDriver: Standard Chrome WebDriver")
        print("="*80)

        print("Select processing mode:")
        print("1. Process all states (Complete workflow)")
        print("2. Process a single specific state")
        print("3. Process one state and one district (Testing mode)")
        print("4. Configure Phase 2 threading mode")
        print("5. Test multi-threading with existing CSV file")
        print("6. Diagnose Phase 1 issues for problematic states")
        print("7. Exit the program")
        print("="*80)

        while True:
            try:
                choice = input("\nEnter your choice (1-7): ").strip()
                if choice in ['1', '2', '3', '4', '5', '6', '7']:
                    return choice
                else:
                    print("❌ Invalid choice. Please enter 1, 2, 3, 4, 5, 6, or 7.")
            except KeyboardInterrupt:
                print("\n\n👋 Exiting program...")
                return '7'
            except Exception as e:
                print(f"❌ Error reading input: {e}")
                return '7'

    def select_state_interactive(self):
        """Interactive state selection"""
        print("\n📋 Available States:")
        print("-" * 50)
        for i, state in enumerate(self.states_list, 1):
            print(f"{i:2d}. {state}")
        print("-" * 50)

        while True:
            try:
                choice = input(f"\nSelect state (1-{len(self.states_list)}) or 'q' to quit: ").strip()
                if choice.lower() == 'q':
                    return None

                state_index = int(choice) - 1
                if 0 <= state_index < len(self.states_list):
                    selected_state = self.states_list[state_index]
                    print(f"✅ Selected state: {selected_state}")
                    return selected_state
                else:
                    print(f"❌ Invalid choice. Please enter a number between 1 and {len(self.states_list)}.")
            except ValueError:
                print("❌ Invalid input. Please enter a number.")
            except KeyboardInterrupt:
                print("\n\n👋 Exiting...")
                return None

    def select_district_interactive(self, state_name):
        """Interactive district selection for a given state"""
        try:
            # Import the Phase 1 scraper to get districts
            from phase1_statewise_scraper import StatewiseSchoolScraper

            logger.info(f"🔧 Getting districts for {state_name}...")
            scraper = StatewiseSchoolScraper()
            scraper.setup_driver()

            # Navigate and get state data
            if not scraper.navigate_to_portal():
                logger.error("Failed to navigate to portal")
                scraper.driver.quit()
                return None

            states = scraper.extract_states_data()
            target_state = None
            for state in states:
                if state['stateName'] == state_name:
                    target_state = state
                    break

            if not target_state:
                logger.error(f"State {state_name} not found")
                scraper.driver.quit()
                return None

            # Select state and get districts
            scraper.select_state(target_state)
            districts = scraper.extract_districts_data()
            scraper.driver.quit()

            if not districts:
                print(f"❌ No districts found for {state_name}")
                return None

            print(f"\n📋 Available Districts in {state_name}:")
            print("-" * 60)
            for i, district in enumerate(districts, 1):
                print(f"{i:2d}. {district['districtName']}")
            print("-" * 60)

            while True:
                try:
                    choice = input(f"\nSelect district (1-{len(districts)}) or 'q' to quit: ").strip()
                    if choice.lower() == 'q':
                        return None

                    district_index = int(choice) - 1
                    if 0 <= district_index < len(districts):
                        selected_district = districts[district_index]
                        print(f"✅ Selected district: {selected_district['districtName']}")
                        return selected_district
                    else:
                        print(f"❌ Invalid choice. Please enter a number between 1 and {len(districts)}.")
                except ValueError:
                    print("❌ Invalid input. Please enter a number.")
                except KeyboardInterrupt:
                    print("\n\n👋 Exiting...")
                    return None

        except Exception as e:
            logger.error(f"Error getting districts for {state_name}: {e}")
            return None



    def execute_phase1_single_state(self, state_name, target_district=None):
        """Execute Phase 1 for a single state with enhanced WebDriver stability"""
        scraper = None
        try:
            logger.info(f"   🔧 Initializing enhanced Phase 1 scraper for {state_name}")
            scraper = EnhancedStatewiseSchoolScraper()

            # Enhanced WebDriver setup with better error handling
            if not self.setup_enhanced_phase1_driver(scraper, state_name):
                logger.error(f"   ❌ Failed to setup WebDriver for {state_name}")
                return False

            # Navigate to portal with enhanced retry mechanism
            success = self.navigate_to_portal_enhanced(scraper, state_name)
            if not success:
                logger.error(f"   ❌ Failed to navigate to portal for {state_name}")
                return False

            # Extract states list with timeout handling
            states = self.extract_states_data_enhanced(scraper, state_name)
            if not states:
                logger.error(f"   ❌ Failed to extract states data for {state_name}")
                return False

            # Find the target state
            target_state = None
            for state in states:
                if state['stateName'] == state_name:
                    target_state = state
                    break

            if not target_state:
                logger.error(f"   ❌ State {state_name} not found in states list")
                return False

            # Process the single state (or single district if specified)
            if target_district:
                logger.info(f"   🎯 Processing single district: {target_district['districtName']} in {state_name}")
                success = scraper.process_single_state_single_district(target_state, target_district)
            else:
                logger.info(f"   🎯 Processing single state: {state_name}")
                success = scraper.process_single_state_enhanced(target_state)

            # Cleanup WebDriver
            try:
                if scraper and scraper.driver:
                    scraper.driver.quit()
                    logger.debug(f"   🧹 WebDriver cleaned up for {state_name}")
            except Exception as cleanup_error:
                logger.warning(f"   ⚠️ WebDriver cleanup error for {state_name}: {cleanup_error}")

            return success

        except Exception as e:
            logger.error(f"   ❌ Error in Phase 1 execution for {state_name}: {e}")

            # Emergency cleanup
            try:
                if scraper and scraper.driver:
                    scraper.driver.quit()
                    logger.debug(f"   🧹 Emergency WebDriver cleanup for {state_name}")
            except:
                pass  # Ignore cleanup errors during exception handling

            return False

    def setup_enhanced_phase1_driver(self, scraper, state_name):
        """Setup enhanced WebDriver for Phase 1 with better stability"""
        try:
            logger.info(f"   🔧 Setting up enhanced WebDriver for {state_name}")

            # Try multiple times with different configurations
            for attempt in range(3):
                try:
                    # Enhanced driver setup with better timeout handling
                    success = scraper.setup_driver()
                    if success and scraper.driver:
                        # Additional WebDriver optimizations for stability
                        scraper.driver.implicitly_wait(10)  # Increased implicit wait
                        scraper.driver.set_page_load_timeout(45)  # Increased page load timeout
                        scraper.driver.set_script_timeout(30)  # Set script timeout

                        # Test WebDriver functionality
                        scraper.driver.get("about:blank")
                        logger.info(f"   ✅ Enhanced WebDriver setup successful for {state_name}")
                        return True

                except Exception as setup_error:
                    logger.warning(f"   ⚠️ WebDriver setup attempt {attempt + 1} failed for {state_name}: {setup_error}")

                    # Cleanup failed driver
                    try:
                        if scraper.driver:
                            scraper.driver.quit()
                    except:
                        pass

                    if attempt < 2:  # Not the last attempt
                        time.sleep(5)  # Wait before retry

            logger.error(f"   ❌ All WebDriver setup attempts failed for {state_name}")
            return False

        except Exception as e:
            logger.error(f"   ❌ Critical error in WebDriver setup for {state_name}: {e}")
            return False

    def navigate_to_portal_enhanced(self, scraper, state_name):
        """Enhanced portal navigation with better error handling"""
        try:
            logger.info(f"   🌐 Enhanced portal navigation for {state_name}")

            # Multiple navigation attempts with different strategies
            for attempt in range(3):
                try:
                    # Clear browser state
                    scraper.driver.delete_all_cookies()

                    # Navigate with enhanced retry
                    success = scraper.navigate_to_portal(max_retries=2)
                    if success:
                        logger.info(f"   ✅ Portal navigation successful for {state_name}")
                        return True

                except Exception as nav_error:
                    logger.warning(f"   ⚠️ Portal navigation attempt {attempt + 1} failed for {state_name}: {nav_error}")

                    if attempt < 2:  # Not the last attempt
                        # Try to recover
                        try:
                            scraper.driver.refresh()
                            time.sleep(10)
                        except:
                            pass

            logger.error(f"   ❌ All portal navigation attempts failed for {state_name}")
            return False

        except Exception as e:
            logger.error(f"   ❌ Critical error in portal navigation for {state_name}: {e}")
            return False

    def extract_states_data_enhanced(self, scraper, state_name):
        """Enhanced states data extraction with timeout handling"""
        try:
            logger.info(f"   📊 Enhanced states data extraction for {state_name}")

            # Multiple extraction attempts
            for attempt in range(2):
                try:
                    states = scraper.extract_states_data()
                    if states and len(states) > 0:
                        logger.info(f"   ✅ States data extraction successful for {state_name}: {len(states)} states found")
                        return states

                except Exception as extract_error:
                    logger.warning(f"   ⚠️ States extraction attempt {attempt + 1} failed for {state_name}: {extract_error}")

                    if attempt < 1:  # Not the last attempt
                        time.sleep(5)

            logger.error(f"   ❌ All states extraction attempts failed for {state_name}")
            return None

        except Exception as e:
            logger.error(f"   ❌ Critical error in states extraction for {state_name}: {e}")
            return None



    def find_phase1_csv_for_state(self, state_name):
        """Find the Phase 1 CSV file for a specific state"""
        try:
            # Clean state name for filename matching
            clean_state = state_name.replace(' ', '_').replace('&', 'and').replace('/', '_').upper()
            
            # Look for the Phase 1 CSV file
            pattern = f"{clean_state}_phase1_complete_*.csv"
            csv_files = glob.glob(pattern)
            
            if csv_files:
                # Return the most recent file
                latest_file = max(csv_files, key=os.path.getctime)
                logger.info(f"   📁 Found Phase 1 CSV: {latest_file}")
                return latest_file
            else:
                logger.error(f"   ❌ No Phase 1 CSV found for {state_name}")
                return None
                
        except Exception as e:
            logger.error(f"   ❌ Error finding Phase 1 CSV for {state_name}: {e}")
            return None

    def run_phase2_for_state(self, state_name, csv_file, use_multithreading=True):
        """Run Phase 2 processing for a specific state with retry mechanism"""
        logger.info(f"🔄 Starting Phase 2 for state: {state_name}")

        if use_multithreading:
            logger.info(f"🧵 Using multi-threaded processing (2 worker threads)")
        else:
            logger.info(f"🔄 Using single-threaded processing")

        for attempt in range(self.max_retries):
            try:
                if use_multithreading:
                    result = self.execute_phase2_multithreaded(state_name, csv_file)
                else:
                    result = self.execute_phase2_single_state(state_name, csv_file)

                if result:
                    logger.info(f"✅ Phase 2 completed successfully for {state_name}")
                    return True
                else:
                    logger.warning(f"⚠️ Phase 2 failed for {state_name} (attempt {attempt + 1}/{self.max_retries})")

            except Exception as e:
                logger.error(f"❌ Phase 2 error for {state_name} (attempt {attempt + 1}/{self.max_retries}): {e}")

            if attempt < self.max_retries - 1:
                logger.info(f"⏳ Retrying Phase 2 for {state_name} in {self.retry_delay} seconds...")
                time.sleep(self.retry_delay)

        logger.error(f"❌ Phase 2 failed for {state_name} after {self.max_retries} attempts")
        return False

    def execute_phase2_single_state(self, state_name, csv_file):
        """Execute Phase 2 for a single state"""
        try:
            # Import the Phase 2 processor components
            from phase2_automated_processor import AutomatedPhase2Processor

            logger.info(f"   🔧 Initializing Phase 2 processor for {state_name}")
            processor = AutomatedPhase2Processor()

            # Setup driver with connection error handling
            processor.setup_driver()

            # Process the single state file
            success = processor.process_state_file_automated(csv_file)

            # Cleanup
            processor.driver.quit()

            return success

        except Exception as e:
            logger.error(f"   ❌ Error in Phase 2 execution for {state_name}: {e}")
            return False

    def execute_phase2_multithreaded(self, state_name, csv_file):
        """Execute Phase 2 for a single state using 2 worker threads"""
        try:
            logger.info(f"   🔧 Initializing multi-threaded Phase 2 processor for {state_name}")
            logger.info(f"   🧵 Using 2 worker threads for parallel processing")

            # Create the multi-threaded processor
            processor = MultiThreadedPhase2Processor(state_name, csv_file)

            # Execute multi-threaded processing
            success = processor.process_with_threads()

            return success

        except Exception as e:
            logger.error(f"   ❌ Error in multi-threaded Phase 2 execution for {state_name}: {e}")
            return False

    def process_state_complete_cycle(self, state_name):
        """Process a complete Phase 1 → Phase 2 cycle for one state"""
        logger.info(f"\n{'='*80}")
        logger.info(f"🏛️ PROCESSING STATE: {state_name}")
        logger.info(f"{'='*80}")
        
        state_start_time = time.time()
        
        try:
            # Phase 1: Extract school data
            logger.info(f"📋 PHASE 1: Extracting school data for {state_name}")
            phase1_success = self.run_phase1_for_state(state_name)
            
            if not phase1_success:
                logger.error(f"❌ Phase 1 failed for {state_name} - skipping Phase 2")
                self.failed_states.append(f"{state_name} (Phase 1 failed)")
                return False
            
            # Find the generated CSV file
            csv_file = self.find_phase1_csv_for_state(state_name)
            if not csv_file:
                logger.error(f"❌ No Phase 1 CSV found for {state_name} - skipping Phase 2")
                self.failed_states.append(f"{state_name} (CSV not found)")
                return False
            
            # Brief pause between phases
            time.sleep(5)
            
            # Phase 2: Process detailed data
            logger.info(f"🔍 PHASE 2: Processing detailed data for {state_name}")
            phase2_success = self.run_phase2_for_state(state_name, csv_file, self.use_multithreading)
            
            if not phase2_success:
                logger.error(f"❌ Phase 2 failed for {state_name}")
                self.failed_states.append(f"{state_name} (Phase 2 failed)")
                return False
            
            # Success!
            state_time = time.time() - state_start_time
            self.processed_states.append(state_name)
            
            logger.info(f"✅ COMPLETED {state_name} in {state_time/60:.1f} minutes")
            logger.info(f"📊 Progress: {len(self.processed_states)}/{len(self.states_list)} states completed")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Critical error processing {state_name}: {e}")
            self.failed_states.append(f"{state_name} (Critical error)")
            return False

    def run_sequential_processing(self):
        """Run the complete sequential state processing workflow"""
        try:
            self.start_time = time.time()
            
            logger.info("🚀 STARTING SEQUENTIAL STATE PROCESSING")
            logger.info("="*80)
            logger.info(f"📋 Total states to process: {len(self.states_list)}")
            logger.info(f"🔄 Workflow: State → Phase 1 → Phase 2 → Next State")
            logger.info("="*80)
            
            # Process each state sequentially
            for i, state_name in enumerate(self.states_list, 1):
                logger.info(f"\n🎯 STARTING STATE {i}/{len(self.states_list)}: {state_name}")
                
                success = self.process_state_complete_cycle(state_name)
                
                if success:
                    logger.info(f"✅ State {i} completed successfully: {state_name}")
                else:
                    logger.warning(f"⚠️ State {i} failed: {state_name}")
                
                # Brief pause between states
                if i < len(self.states_list):
                    logger.info("⏳ Brief pause before next state...")
                    time.sleep(10)
            
            # Final summary
            self.show_final_summary()
            
        except Exception as e:
            logger.error(f"❌ Critical error in sequential processing: {e}")
        finally:
            logger.info("🔒 Sequential processing completed")

    def show_final_summary(self):
        """Show final processing summary"""
        total_time = time.time() - self.start_time
        
        logger.info(f"\n{'='*80}")
        logger.info("🎯 SEQUENTIAL PROCESSING COMPLETED")
        logger.info(f"{'='*80}")
        logger.info(f"⏱️ Total processing time: {total_time/3600:.1f} hours")
        logger.info(f"✅ Successfully processed states: {len(self.processed_states)}")
        logger.info(f"❌ Failed states: {len(self.failed_states)}")
        logger.info(f"📈 Success rate: {len(self.processed_states)/len(self.states_list)*100:.1f}%")
        
        if self.processed_states:
            logger.info(f"\n✅ SUCCESSFUL STATES:")
            for state in self.processed_states:
                logger.info(f"   ✓ {state}")
        
        if self.failed_states:
            logger.info(f"\n❌ FAILED STATES:")
            for state in self.failed_states:
                logger.info(f"   ✗ {state}")
        
        logger.info(f"\n💾 Output files pattern:")
        logger.info(f"   Phase 1: *_phase1_complete_*.csv")
        logger.info(f"   Phase 2: *_phase2_batch*_*.csv")
        logger.info("🎉 Sequential processing complete!")

    def run_single_state_processing(self, state_name):
        """Run processing for a single state"""
        try:
            self.start_time = time.time()

            logger.info("🚀 STARTING SINGLE STATE PROCESSING")
            logger.info("="*80)
            logger.info(f"🎯 Target state: {state_name}")
            logger.info("="*80)

            success = self.process_state_complete_cycle(state_name)

            if success:
                logger.info(f"✅ Single state processing completed successfully: {state_name}")
            else:
                logger.warning(f"⚠️ Single state processing failed: {state_name}")

            # Show summary
            self.show_final_summary()

        except Exception as e:
            logger.error(f"❌ Critical error in single state processing: {e}")
        finally:
            logger.info("🔒 Single state processing completed")

    def run_single_district_processing(self, state_name, district_data):
        """Run processing for a single district in a state"""
        try:
            self.start_time = time.time()

            logger.info("🚀 STARTING SINGLE DISTRICT PROCESSING")
            logger.info("="*80)
            logger.info(f"🎯 Target state: {state_name}")
            logger.info(f"🎯 Target district: {district_data['districtName']}")
            logger.info("="*80)

            # Phase 1: Extract school data for single district
            logger.info(f"📋 PHASE 1: Extracting school data for {district_data['districtName']}")
            phase1_success = self.run_phase1_for_state(state_name, target_district=district_data)

            if not phase1_success:
                logger.error(f"❌ Phase 1 failed for {district_data['districtName']} - skipping Phase 2")
                self.failed_states.append(f"{state_name} - {district_data['districtName']} (Phase 1 failed)")
                return False

            # Find the generated CSV file
            csv_file = self.find_phase1_csv_for_state(state_name)
            if not csv_file:
                logger.error(f"❌ No Phase 1 CSV found for {state_name} - skipping Phase 2")
                self.failed_states.append(f"{state_name} - {district_data['districtName']} (CSV not found)")
                return False

            # Brief pause between phases
            time.sleep(5)

            # Phase 2: Process detailed data
            logger.info(f"🔍 PHASE 2: Processing detailed data for {district_data['districtName']}")
            phase2_success = self.run_phase2_for_state(state_name, csv_file, self.use_multithreading)

            if not phase2_success:
                logger.error(f"❌ Phase 2 failed for {district_data['districtName']}")
                self.failed_states.append(f"{state_name} - {district_data['districtName']} (Phase 2 failed)")
                return False

            # Success!
            self.processed_states.append(f"{state_name} - {district_data['districtName']}")
            logger.info(f"✅ COMPLETED {district_data['districtName']} in {state_name}")

            # Show summary
            self.show_final_summary()

            return True

        except Exception as e:
            logger.error(f"❌ Critical error in single district processing: {e}")
            return False

    def run_phase1_for_state(self, state_name, target_district=None):
        """Run Phase 1 scraper for a specific state with enhanced retry mechanism"""
        logger.info(f"🚀 Starting enhanced Phase 1 for state: {state_name}")

        # State-specific retry configuration
        state_retry_config = self.get_state_retry_config(state_name)
        max_retries = state_retry_config['max_retries']
        retry_delay = state_retry_config['retry_delay']

        logger.info(f"   🔧 Using {max_retries} retries with {retry_delay}s delay for {state_name}")

        for attempt in range(max_retries):
            try:
                logger.info(f"   🎯 Phase 1 attempt {attempt + 1}/{max_retries} for {state_name}")

                # Execute Phase 1 with enhanced error handling
                result = self.execute_phase1_single_state(state_name, target_district)

                if result:
                    logger.info(f"✅ Phase 1 completed successfully for {state_name}")
                    return True
                else:
                    logger.warning(f"⚠️ Phase 1 failed for {state_name} (attempt {attempt + 1}/{max_retries})")

            except Exception as e:
                logger.error(f"❌ Phase 1 error for {state_name} (attempt {attempt + 1}/{max_retries}): {e}")

                # Log additional debugging info for problematic states
                if state_name in ['SIKKIM', 'ARUNACHAL PRADESH', 'MIZORAM', 'NAGALAND']:
                    logger.error(f"   🔍 Debug info for {state_name}: WebDriver timeout or connection issue detected")

            if attempt < max_retries - 1:
                logger.info(f"⏳ Retrying Phase 1 for {state_name} in {retry_delay} seconds...")
                time.sleep(retry_delay)

                # Additional recovery actions for certain states
                if state_name in ['SIKKIM', 'ARUNACHAL PRADESH'] and attempt == 1:
                    logger.info(f"   🔄 Performing additional recovery for {state_name}")
                    time.sleep(15)  # Extra delay for problematic states

        logger.error(f"❌ Phase 1 failed for {state_name} after {max_retries} attempts")
        return False

    def get_state_retry_config(self, state_name):
        """Get state-specific retry configuration"""
        # States known to have connectivity or processing issues
        problematic_states = {
            'SIKKIM': {'max_retries': 5, 'retry_delay': 45},
            'ARUNACHAL PRADESH': {'max_retries': 5, 'retry_delay': 45},
            'MIZORAM': {'max_retries': 4, 'retry_delay': 40},
            'NAGALAND': {'max_retries': 4, 'retry_delay': 40},
            'MANIPUR': {'max_retries': 4, 'retry_delay': 35},
            'TRIPURA': {'max_retries': 4, 'retry_delay': 35}
        }

        # Return state-specific config or default
        return problematic_states.get(state_name, {
            'max_retries': self.max_retries,
            'retry_delay': self.retry_delay
        })

    def test_multithreading_with_existing_csv(self):
        """Test multi-threading functionality with an existing Phase 1 CSV file"""
        try:
            print("\n" + "="*60)
            print("🧪 MULTI-THREADING TEST MODE")
            print("="*60)

            # Find available Phase 1 CSV files
            pattern = "*_phase1_complete_*.csv"
            csv_files = glob.glob(pattern)

            if not csv_files:
                # Fallback: look for old naming convention
                pattern = "*_with_links_*.csv"
                csv_files = glob.glob(pattern)

            if not csv_files:
                print("❌ No Phase 1 CSV files found for testing!")
                print("Please run Phase 1 first to generate CSV files.")
                return

            print(f"📋 Found {len(csv_files)} Phase 1 CSV files:")
            for i, csv_file in enumerate(csv_files, 1):
                print(f"{i:2d}. {csv_file}")

            while True:
                try:
                    choice = input(f"\nSelect CSV file (1-{len(csv_files)}) or 'q' to quit: ").strip()
                    if choice.lower() == 'q':
                        return

                    file_index = int(choice) - 1
                    if 0 <= file_index < len(csv_files):
                        selected_file = csv_files[file_index]
                        break
                    else:
                        print(f"❌ Invalid choice. Please enter a number between 1 and {len(csv_files)}.")
                except ValueError:
                    print("❌ Invalid input. Please enter a number.")
                except KeyboardInterrupt:
                    print("\n\n👋 Exiting test...")
                    return

            # Extract state name from filename
            state_name = self.extract_state_name_from_filename(selected_file)

            print(f"\n🧪 Testing multi-threaded Phase 2 processing:")
            print(f"   📁 File: {selected_file}")
            print(f"   🏛️ State: {state_name}")
            if self.use_multithreading:
                print(f"   🧵 Mode: Multi-threaded (2 workers, Standard WebDriver)")
            else:
                print(f"   🧵 Mode: Single-threaded (Undetected WebDriver)")

            # Run the test
            success = self.run_phase2_for_state(state_name, selected_file, self.use_multithreading)

            if success:
                print(f"\n✅ Multi-threading test completed successfully!")
                print(f"📊 Check the generated CSV file for results")
            else:
                print(f"\n❌ Multi-threading test failed")

        except Exception as e:
            logger.error(f"❌ Error in multi-threading test: {e}")

    def extract_state_name_from_filename(self, filename):
        """Extract state name from CSV filename"""
        try:
            # Remove path and extension
            base_name = os.path.basename(filename)
            base_name = os.path.splitext(base_name)[0]

            # Remove common suffixes
            suffixes = ['_phase1_complete', '_with_links', '_phase2_incremental', '_phase2_multithreaded']
            for suffix in suffixes:
                if suffix in base_name:
                    base_name = base_name.split(suffix)[0]
                    break

            # Remove timestamp patterns
            import re
            base_name = re.sub(r'_\d{8}_\d{6}$', '', base_name)

            # Convert back to proper state name format
            state_name = base_name.replace('_', ' ').replace('and', '&')

            return state_name

        except Exception as e:
            logger.error(f"Error extracting state name from {filename}: {e}")
            return "UNKNOWN_STATE"

    def diagnose_phase1_issues(self):
        """Diagnose Phase 1 issues for problematic states"""
        try:
            print("\n" + "="*60)
            print("🔍 PHASE 1 DIAGNOSTIC MODE")
            print("="*60)

            problematic_states = ['SIKKIM', 'ARUNACHAL PRADESH', 'MIZORAM', 'NAGALAND', 'MANIPUR', 'TRIPURA']

            print(f"📋 Problematic states identified:")
            for i, state in enumerate(problematic_states, 1):
                print(f"{i:2d}. {state}")

            print(f"{len(problematic_states) + 1:2d}. Test custom state")
            print(f"{len(problematic_states) + 2:2d}. Return to main menu")

            while True:
                try:
                    choice = input(f"\nSelect state to diagnose (1-{len(problematic_states) + 2}): ").strip()

                    if choice == str(len(problematic_states) + 2):  # Return to main menu
                        return
                    elif choice == str(len(problematic_states) + 1):  # Custom state
                        custom_state = input("Enter state name: ").strip().upper()
                        if custom_state:
                            selected_state = custom_state
                            break
                    else:
                        try:
                            state_index = int(choice) - 1
                            if 0 <= state_index < len(problematic_states):
                                selected_state = problematic_states[state_index]
                                break
                            else:
                                print(f"❌ Invalid choice. Please enter a number between 1 and {len(problematic_states) + 2}.")
                        except ValueError:
                            print("❌ Invalid input. Please enter a number.")
                except KeyboardInterrupt:
                    print("\n\n👋 Returning to main menu...")
                    return

            print(f"\n🔍 Diagnosing Phase 1 issues for: {selected_state}")
            print("="*60)

            # Get state-specific retry config
            retry_config = self.get_state_retry_config(selected_state)
            print(f"📊 State configuration:")
            print(f"   Max retries: {retry_config['max_retries']}")
            print(f"   Retry delay: {retry_config['retry_delay']} seconds")

            # Run diagnostic test
            print(f"\n🚀 Starting diagnostic Phase 1 test for {selected_state}...")
            success = self.run_phase1_for_state(selected_state)

            if success:
                print(f"\n✅ Phase 1 diagnostic completed successfully for {selected_state}!")

                # Check for generated CSV
                csv_file = self.find_phase1_csv_for_state(selected_state)
                if csv_file:
                    print(f"📁 Generated CSV: {csv_file}")

                    # Quick CSV analysis
                    try:
                        import pandas as pd
                        df = pd.read_csv(csv_file)
                        print(f"📊 CSV Analysis:")
                        print(f"   Total records: {len(df)}")
                        if 'know_more_link' in df.columns:
                            phase2_ready = len(df[df['know_more_link'] != 'N/A'])
                            print(f"   Phase 2 ready: {phase2_ready}/{len(df)} ({(phase2_ready/len(df)*100):.1f}%)")
                    except Exception as e:
                        print(f"   ⚠️ CSV analysis error: {e}")

                    # Offer to test Phase 2
                    test_phase2 = input(f"\n🧪 Test multi-threaded Phase 2 for {selected_state}? (y/n): ").strip().lower()
                    if test_phase2 == 'y':
                        print(f"\n🧵 Testing multi-threaded Phase 2 for {selected_state}...")
                        phase2_success = self.run_phase2_for_state(selected_state, csv_file, self.use_multithreading)
                        if phase2_success:
                            print(f"✅ Phase 2 diagnostic completed successfully!")
                        else:
                            print(f"❌ Phase 2 diagnostic failed")
                else:
                    print(f"⚠️ No CSV file found after Phase 1 completion")
            else:
                print(f"\n❌ Phase 1 diagnostic failed for {selected_state}")
                print(f"💡 Recommendations:")
                print(f"   1. Check internet connection stability")
                print(f"   2. Try running during off-peak hours")
                print(f"   3. Consider increasing retry parameters")
                print(f"   4. Check if Chrome browser is updated")

        except Exception as e:
            logger.error(f"❌ Error in Phase 1 diagnostic: {e}")

def main():
    """Main function with interactive menu for enhanced sequential state processing"""
    try:
        processor = SequentialStateProcessor()

        while True:
            choice = processor.show_interactive_menu()

            if choice == '1':
                # Process all states
                processor.run_sequential_processing()
                break

            elif choice == '2':
                # Process a single specific state
                selected_state = processor.select_state_interactive()
                if selected_state:
                    processor.run_single_state_processing(selected_state)
                break

            elif choice == '3':
                # Process one state and one district
                selected_state = processor.select_state_interactive()
                if selected_state:
                    selected_district = processor.select_district_interactive(selected_state)
                    if selected_district:
                        processor.run_single_district_processing(selected_state, selected_district)
                break

            elif choice == '4':
                # Configure threading mode
                processor.configure_threading()
                # Continue to show menu again

            elif choice == '5':
                # Test multi-threading with existing CSV
                processor.test_multithreading_with_existing_csv()
                break

            elif choice == '6':
                # Diagnose Phase 1 issues
                processor.diagnose_phase1_issues()
                # Continue to show menu again

            elif choice == '7':
                # Exit the program
                print("👋 Goodbye!")
                break

            else:
                print("❌ Invalid choice. Please try again.")

    except Exception as e:
        print(f"❌ Critical error: {e}")
        print("Please check the logs above for details")

if __name__ == "__main__":
    main()
