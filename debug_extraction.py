#!/usr/bin/env python3
"""
Debug script to test single school extraction
"""

import sys
import os
import logging

# Setup logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def debug_single_extraction():
    """Debug extraction for a single school"""
    try:
        # Import the processor
        from State_processor_Multi import MultiThreadedPhase2Processor
        
        print("🔍 DEBUGGING SINGLE SCHOOL EXTRACTION")
        print("="*60)
        
        # Create processor instance
        processor = MultiThreadedPhase2Processor("TEST_STATE", "test.csv")
        
        # Setup driver
        driver = processor.setup_standard_driver()
        
        # Test URL (using one from the CSV)
        test_url = "https://kys.udiseplus.gov.in/#/schooldetail/5300150/12"
        
        print(f"🌐 Testing URL: {test_url}")
        
        # Extract data
        extracted_data = processor.extract_school_data_standard(driver, test_url)
        
        if extracted_data:
            print(f"\n✅ EXTRACTION SUCCESSFUL!")
            print(f"📊 Status: {extracted_data.get('extraction_status', 'N/A')}")
            print(f"📊 Fields extracted: {extracted_data.get('fields_extracted', 0)}")
            print(f"📊 Critical fields: {extracted_data.get('critical_fields_extracted', 0)}")
            
            print(f"\n📋 EXTRACTED DATA:")
            for key, value in extracted_data.items():
                if value != 'N/A':
                    print(f"   {key}: {value}")
            
            print(f"\n❌ MISSING DATA (N/A fields):")
            for key, value in extracted_data.items():
                if value == 'N/A':
                    print(f"   {key}: {value}")
        else:
            print(f"\n❌ EXTRACTION FAILED!")
        
        # Cleanup
        driver.quit()
        
    except Exception as e:
        logger.error(f"❌ Error in debug extraction: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_single_extraction()
