#!/usr/bin/env python3
"""
Script to fix ChromeDriver version mismatch issues and test the solution
"""

import subprocess
import sys
import os
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def install_webdriver_manager():
    """Install webdriver-manager to automatically handle ChromeDriver versions"""
    try:
        print("🔧 INSTALLING WEBDRIVER-MANAGER")
        print("="*50)
        print("This will automatically manage ChromeDriver versions to match your Chrome browser.")
        
        # Install webdriver-manager
        print("\n📦 Installing webdriver-manager...")
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "webdriver-manager"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ webdriver-manager installed successfully!")
            print(result.stdout)
        else:
            print("❌ Failed to install webdriver-manager:")
            print(result.stderr)
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Error installing webdriver-manager: {e}")
        return False

def test_chromedriver_fix():
    """Test the ChromeDriver fix with automatic driver management"""
    try:
        print("\n🧪 TESTING CHROMEDRIVER FIX")
        print("="*50)
        
        # Test basic WebDriver setup
        print("🔧 Testing basic WebDriver setup...")
        
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.chrome.options import Options
        
        # Setup Chrome options
        options = Options()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--headless")  # Run headless for testing
        
        driver = None
        try:
            # Try with webdriver-manager
            try:
                from webdriver_manager.chrome import ChromeDriverManager
                print("   🔄 Using webdriver-manager for automatic ChromeDriver...")
                
                service = Service(ChromeDriverManager().install())
                driver = webdriver.Chrome(service=service, options=options)
                print("   ✅ webdriver-manager setup successful!")
                
                # Test basic functionality
                driver.get("https://www.google.com")
                print(f"   ✅ Browser test successful - Title: {driver.title}")
                
            except ImportError:
                print("   ⚠️ webdriver-manager not available, trying system ChromeDriver...")
                driver = webdriver.Chrome(options=options)
                print("   ✅ System ChromeDriver setup successful!")
                
                # Test basic functionality
                driver.get("https://www.google.com")
                print(f"   ✅ Browser test successful - Title: {driver.title}")
                
        except Exception as driver_error:
            print(f"   ❌ WebDriver test failed: {driver_error}")
            return False
            
        finally:
            if driver:
                driver.quit()
                print("   🧹 WebDriver cleaned up")
        
        print("✅ ChromeDriver fix test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing ChromeDriver fix: {e}")
        return False

def test_sikkim_with_fixed_chromedriver():
    """Test SIKKIM processing with the fixed ChromeDriver"""
    try:
        print("\n🎯 TESTING SIKKIM WITH FIXED CHROMEDRIVER")
        print("="*50)
        
        # Import the processor
        from State_processor_Multi import SequentialStateProcessor
        
        processor = SequentialStateProcessor()
        
        print("🔧 Testing Phase 1 WebDriver setup for SIKKIM...")
        
        # Test just the WebDriver setup part
        from State_processor_Multi import EnhancedStatewiseSchoolScraper
        
        scraper = EnhancedStatewiseSchoolScraper()
        
        # Test driver setup
        setup_success = scraper.setup_driver()
        
        if setup_success:
            print("✅ Phase 1 WebDriver setup successful!")
            print("🌐 ChromeDriver version compatibility resolved!")
            
            # Test basic navigation
            try:
                scraper.driver.get("https://www.google.com")
                print(f"✅ Navigation test successful - Title: {scraper.driver.title}")
            except Exception as nav_error:
                print(f"⚠️ Navigation test failed: {nav_error}")
            
            # Cleanup
            scraper.driver.quit()
            print("🧹 WebDriver cleaned up")
            
            print("\n🎉 SIKKIM processing should now work with fixed ChromeDriver!")
            return True
        else:
            print("❌ Phase 1 WebDriver setup failed")
            return False
            
    except Exception as e:
        print(f"❌ Error testing SIKKIM with fixed ChromeDriver: {e}")
        import traceback
        traceback.print_exc()
        return False

def show_chrome_version_info():
    """Show Chrome and ChromeDriver version information"""
    try:
        print("\n🔍 CHROME VERSION INFORMATION")
        print("="*50)
        
        # Try to get Chrome version
        try:
            import subprocess
            import platform
            
            if platform.system() == "Windows":
                # Windows Chrome version check
                result = subprocess.run([
                    "reg", "query", 
                    "HKEY_CURRENT_USER\\Software\\Google\\Chrome\\BLBeacon", 
                    "/v", "version"
                ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    version_line = [line for line in result.stdout.split('\n') if 'version' in line.lower()]
                    if version_line:
                        chrome_version = version_line[0].split()[-1]
                        print(f"🌐 Chrome Browser Version: {chrome_version}")
                else:
                    print("⚠️ Could not detect Chrome version automatically")
            else:
                print("ℹ️ Chrome version detection only implemented for Windows")
                
        except Exception as version_error:
            print(f"⚠️ Error detecting Chrome version: {version_error}")
        
        # Show webdriver-manager info
        try:
            from webdriver_manager.chrome import ChromeDriverManager
            print("✅ webdriver-manager is available")
            print("   This will automatically download the correct ChromeDriver version")
        except ImportError:
            print("❌ webdriver-manager is not installed")
            print("   Install with: pip install webdriver-manager")
            
    except Exception as e:
        print(f"❌ Error showing version info: {e}")

def main():
    """Main function to fix ChromeDriver issues"""
    print("🔧 CHROMEDRIVER VERSION FIX TOOL")
    print("="*60)
    print("This tool will fix the ChromeDriver version mismatch issue:")
    print("- Install webdriver-manager for automatic ChromeDriver management")
    print("- Test the fix with basic WebDriver functionality")
    print("- Verify SIKKIM processing compatibility")
    
    try:
        # Show current version info
        show_chrome_version_info()
        
        # Ask user what to do
        print("\nSelect action:")
        print("1. Install webdriver-manager and test fix")
        print("2. Test current ChromeDriver setup")
        print("3. Test SIKKIM processing with current setup")
        print("4. Show version information only")
        
        choice = input("\nEnter choice (1-4): ").strip()
        
        if choice == "1":
            # Install webdriver-manager and test
            if install_webdriver_manager():
                print("\n" + "="*50)
                test_chromedriver_fix()
                print("\n" + "="*50)
                test_sikkim_with_fixed_chromedriver()
            else:
                print("❌ Installation failed")
                
        elif choice == "2":
            # Test current setup
            test_chromedriver_fix()
            
        elif choice == "3":
            # Test SIKKIM processing
            test_sikkim_with_fixed_chromedriver()
            
        elif choice == "4":
            # Show version info only
            show_chrome_version_info()
            
        else:
            print("❌ Invalid choice")
            
        print("\n🎯 NEXT STEPS:")
        print("1. If webdriver-manager was installed, SIKKIM processing should now work")
        print("2. Run: python State_processor_Multi.py")
        print("3. Choose option 6 to test SIKKIM processing")
        print("4. The ChromeDriver version will be automatically managed")
        
    except KeyboardInterrupt:
        print("\n\n👋 Cancelled by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()
