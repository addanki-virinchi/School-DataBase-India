#!/usr/bin/env python3
"""
Test script to verify the fixed SIKKIM state processing with enhanced WebDriver element selection
"""

import sys
import os
import logging
import time

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_sikkim_fixed_processing():
    """Test SIKKIM state processing with fixed element selection"""
    try:
        # Import the processor
        from State_processor_Multi import SequentialStateProcessor
        
        print("🔧 TESTING FIXED SIKKIM PROCESSING")
        print("="*60)
        print("🌐 Using standard Chrome WebDriver")
        print("🔧 Enhanced search button selectors")
        print("🔧 Fixed district selection logic")
        print("🔧 Added 100 results per page selection")
        
        # Create processor instance
        processor = SequentialStateProcessor()
        
        state_name = "SIKKIM"
        
        print(f"\n🎯 Testing fixed Phase 1 for: {state_name}")
        
        # Get retry configuration for SIKKIM
        retry_config = processor.get_state_retry_config(state_name)
        print(f"📊 SIKKIM Configuration:")
        print(f"   Max retries: {retry_config['max_retries']}")
        print(f"   Retry delay: {retry_config['retry_delay']} seconds")
        
        print(f"\n🔧 FIXES IMPLEMENTED:")
        print(f"   ✅ Enhanced search button selectors (11 fallback options)")
        print(f"   ✅ Fixed district selection value handling")
        print(f"   ✅ Added 100 results per page selection")
        print(f"   ✅ Enhanced error logging and debugging")
        print(f"   ✅ Multiple selection strategies for districts")
        
        # Start timing
        start_time = time.time()
        
        print(f"\n🚀 Starting fixed Phase 1 test for {state_name}...")
        success = processor.run_phase1_for_state(state_name)
        
        # Calculate duration
        duration = time.time() - start_time
        
        if success:
            print(f"\n✅ SIKKIM Phase 1 test completed successfully!")
            print(f"⏱️ Duration: {duration/60:.1f} minutes")
            print(f"🔧 All fixes working correctly!")
            
            # Look for generated CSV
            csv_file = processor.find_phase1_csv_for_state(state_name)
            if csv_file:
                print(f"📁 Generated CSV: {csv_file}")
                
                # Analyze CSV
                try:
                    import pandas as pd
                    df = pd.read_csv(csv_file)
                    
                    print(f"\n📊 DETAILED CSV ANALYSIS:")
                    print(f"   📋 Total records: {len(df)}")
                    
                    if 'know_more_link' in df.columns:
                        phase2_ready = len(df[df['know_more_link'] != 'N/A'])
                        percentage = (phase2_ready / len(df)) * 100 if len(df) > 0 else 0
                        print(f"   🔗 Phase 2 ready: {phase2_ready}/{len(df)} ({percentage:.1f}%)")
                    
                    if 'district_name' in df.columns:
                        districts = df['district_name'].nunique()
                        district_list = df['district_name'].unique()
                        print(f"   🏛️ Districts covered: {districts}")
                        print(f"   📋 District list: {', '.join(district_list)}")
                    
                    if 'email' in df.columns:
                        emails_found = len(df[df['email'] != 'N/A'])
                        email_percentage = (emails_found / len(df)) * 100 if len(df) > 0 else 0
                        print(f"   📧 Emails found: {emails_found}/{len(df)} ({email_percentage:.1f}%)")
                    
                    # Show sample data from each district
                    if len(df) > 0 and 'district_name' in df.columns:
                        print(f"\n📋 SAMPLE DATA BY DISTRICT:")
                        for district in df['district_name'].unique()[:3]:  # Show first 3 districts
                            district_data = df[df['district_name'] == district].iloc[0]
                            print(f"   🏛️ {district}:")
                            print(f"      🏫 School: {district_data.get('school_name', 'N/A')}")
                            print(f"      🆔 UDISE: {district_data.get('udise_code', 'N/A')}")
                            print(f"      📧 Email: {district_data.get('email', 'N/A')}")
                            print(f"      🔗 Link: {'Available' if district_data.get('know_more_link', 'N/A') != 'N/A' else 'N/A'}")
                        
                except Exception as e:
                    print(f"   ⚠️ CSV analysis error: {e}")
                
                # Test Phase 2 processing
                print(f"\n🧪 PHASE 2 TEST:")
                test_phase2 = input(f"Test multi-threaded Phase 2 for SIKKIM? (y/n): ").strip().lower()
                if test_phase2 == 'y':
                    print(f"\n🧵 Testing multi-threaded Phase 2 for SIKKIM...")
                    print(f"🔧 Using fixed Phase 1 CSV as input")
                    
                    phase2_start = time.time()
                    phase2_success = processor.run_phase2_for_state(state_name, csv_file, use_multithreading=True)
                    phase2_duration = time.time() - phase2_start
                    
                    if phase2_success:
                        print(f"✅ Phase 2 test completed successfully!")
                        print(f"⏱️ Phase 2 duration: {phase2_duration/60:.1f} minutes")
                        print(f"⏱️ Total duration: {(duration + phase2_duration)/60:.1f} minutes")
                        print(f"🎉 Complete SIKKIM processing successful!")
                    else:
                        print(f"❌ Phase 2 test failed")
            else:
                print(f"⚠️ No CSV file found after Phase 1 completion")
                
        else:
            print(f"\n❌ SIKKIM Phase 1 test failed")
            print(f"⏱️ Failed after: {duration/60:.1f} minutes")
            print(f"\n🔍 DEBUGGING INFORMATION:")
            print(f"   The fixes may need further refinement")
            print(f"   Check the logs above for specific error details")
            print(f"   Common issues:")
            print(f"   - Search button selector not matching page structure")
            print(f"   - District dropdown value format mismatch")
            print(f"   - Results per page dropdown not found")
            print(f"   - Network connectivity issues")
            
            return False
            
        return True
        
    except Exception as e:
        logger.error(f"❌ Error in SIKKIM fixed processing test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_district_selection_debug():
    """Debug district selection specifically"""
    try:
        from State_processor_Multi import EnhancedStatewiseSchoolScraper
        
        print("\n🔍 DISTRICT SELECTION DEBUG TEST")
        print("="*50)
        
        scraper = EnhancedStatewiseSchoolScraper()
        
        # Setup driver
        if not scraper.setup_driver():
            print("❌ Failed to setup driver")
            return False
        
        # Navigate to portal
        if not scraper.navigate_to_portal():
            print("❌ Failed to navigate to portal")
            return False
        
        # Extract states
        states = scraper.extract_states_data()
        if not states:
            print("❌ Failed to extract states")
            return False
        
        # Find SIKKIM
        sikkim_state = None
        for state in states:
            if state['stateName'] == 'SIKKIM':
                sikkim_state = state
                break
        
        if not sikkim_state:
            print("❌ SIKKIM state not found")
            return False
        
        print(f"✅ Found SIKKIM state: {sikkim_state}")
        
        # Select SIKKIM
        if not scraper.select_state(sikkim_state):
            print("❌ Failed to select SIKKIM state")
            return False
        
        # Extract districts
        districts = scraper.extract_districts_data()
        if not districts:
            print("❌ Failed to extract districts")
            return False
        
        print(f"✅ Found {len(districts)} districts:")
        for i, district in enumerate(districts):
            print(f"   {i+1}. {district}")
        
        # Test selecting first district
        if districts:
            first_district = districts[0]
            print(f"\n🧪 Testing selection of: {first_district}")
            
            success = scraper.select_district(first_district)
            if success:
                print("✅ District selection successful!")
            else:
                print("❌ District selection failed!")
        
        # Cleanup
        scraper.driver.quit()
        return True
        
    except Exception as e:
        print(f"❌ Debug test error: {e}")
        return False

if __name__ == "__main__":
    print("🔧 SIKKIM FIXED PROCESSING TEST")
    print("This tool tests the fixes for SIKKIM state processing issues:")
    print("- Enhanced search button selectors")
    print("- Fixed district selection logic") 
    print("- Added 100 results per page selection")
    print("\nPress Ctrl+C to cancel at any time.")
    
    try:
        print("\nSelect test mode:")
        print("1. Full SIKKIM processing test")
        print("2. District selection debug test")
        
        choice = input("\nEnter choice (1-2): ").strip()
        
        if choice == "1":
            test_sikkim_fixed_processing()
        elif choice == "2":
            test_district_selection_debug()
        else:
            print("Invalid choice")
            
    except KeyboardInterrupt:
        print("\n\n👋 Test cancelled by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
