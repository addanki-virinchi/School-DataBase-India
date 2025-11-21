#!/usr/bin/env python3
"""
Test script to verify Phase 1 processing with standard WebDriver (no undetected-chromedriver)
"""

import sys
import os
import logging
import time

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_standard_webdriver_phase1():
    """Test Phase 1 processing with standard WebDriver"""
    try:
        # Import the processor
        from State_processor_Multi import SequentialStateProcessor
        
        print("🧪 TESTING PHASE 1 WITH STANDARD WEBDRIVER")
        print("="*60)
        print("🌐 Using standard Chrome WebDriver (no undetected-chromedriver)")
        print("🎯 Testing with a small state for quick verification")
        
        # Create processor instance
        processor = SequentialStateProcessor()
        
        # Test with a small state (GOA is usually small and fast)
        test_states = ["GOA", "SIKKIM", "TRIPURA", "MIZORAM"]
        
        print(f"\n📋 Available test states:")
        for i, state in enumerate(test_states, 1):
            print(f"{i:2d}. {state}")
        
        while True:
            try:
                choice = input(f"\nSelect state to test (1-{len(test_states)}) or 'q' to quit: ").strip()
                if choice.lower() == 'q':
                    return
                
                state_index = int(choice) - 1
                if 0 <= state_index < len(test_states):
                    selected_state = test_states[state_index]
                    break
                else:
                    print(f"❌ Invalid choice. Please enter a number between 1 and {len(test_states)}.")
            except ValueError:
                print("❌ Invalid input. Please enter a number.")
            except KeyboardInterrupt:
                print("\n\n👋 Exiting test...")
                return
        
        print(f"\n🚀 Testing Phase 1 for: {selected_state}")
        print(f"🔧 Standard WebDriver configuration")
        print(f"🔄 Enhanced retry mechanism enabled")
        
        # Get retry configuration
        retry_config = processor.get_state_retry_config(selected_state)
        print(f"📊 Configuration:")
        print(f"   Max retries: {retry_config['max_retries']}")
        print(f"   Retry delay: {retry_config['retry_delay']} seconds")
        
        # Start timing
        start_time = time.time()
        
        print(f"\n🚀 Starting Phase 1 test with standard WebDriver...")
        success = processor.run_phase1_for_state(selected_state)
        
        # Calculate duration
        duration = time.time() - start_time
        
        if success:
            print(f"\n✅ Phase 1 test completed successfully!")
            print(f"⏱️ Duration: {duration/60:.1f} minutes")
            print(f"🌐 WebDriver: Standard Chrome (no undetected-chromedriver)")
            
            # Look for generated CSV
            csv_file = processor.find_phase1_csv_for_state(selected_state)
            if csv_file:
                print(f"📁 Generated CSV: {csv_file}")
                
                # Analyze CSV
                try:
                    import pandas as pd
                    df = pd.read_csv(csv_file)
                    
                    print(f"\n📊 CSV ANALYSIS:")
                    print(f"   📋 Total records: {len(df)}")
                    
                    if 'know_more_link' in df.columns:
                        phase2_ready = len(df[df['know_more_link'] != 'N/A'])
                        percentage = (phase2_ready / len(df)) * 100 if len(df) > 0 else 0
                        print(f"   🔗 Phase 2 ready: {phase2_ready}/{len(df)} ({percentage:.1f}%)")
                    
                    if 'district_name' in df.columns:
                        districts = df['district_name'].nunique()
                        print(f"   🏛️ Districts covered: {districts}")
                    
                    if 'email' in df.columns:
                        emails_found = len(df[df['email'] != 'N/A'])
                        email_percentage = (emails_found / len(df)) * 100 if len(df) > 0 else 0
                        print(f"   📧 Emails found: {emails_found}/{len(df)} ({email_percentage:.1f}%)")
                    
                    # Show sample data
                    if len(df) > 0:
                        print(f"\n📋 SAMPLE DATA:")
                        sample = df.iloc[0]
                        print(f"   🏫 School: {sample.get('school_name', 'N/A')}")
                        print(f"   🏛️ District: {sample.get('district_name', 'N/A')}")
                        print(f"   🆔 UDISE: {sample.get('udise_code', 'N/A')}")
                        print(f"   📧 Email: {sample.get('email', 'N/A')}")
                        print(f"   🔗 Link: {sample.get('know_more_link', 'N/A')[:50]}...")
                        
                except Exception as e:
                    print(f"   ⚠️ CSV analysis error: {e}")
                
                # Offer Phase 2 test
                print(f"\n🧪 PHASE 2 TEST OPTION:")
                test_phase2 = input(f"Test multi-threaded Phase 2 for {selected_state}? (y/n): ").strip().lower()
                if test_phase2 == 'y':
                    print(f"\n🧵 Testing multi-threaded Phase 2 for {selected_state}...")
                    print(f"🌐 Phase 2 will use standard WebDriver (no undetected-chromedriver)")
                    
                    phase2_start = time.time()
                    phase2_success = processor.run_phase2_for_state(selected_state, csv_file, use_multithreading=True)
                    phase2_duration = time.time() - phase2_start
                    
                    if phase2_success:
                        print(f"✅ Phase 2 test completed successfully!")
                        print(f"⏱️ Phase 2 duration: {phase2_duration/60:.1f} minutes")
                        print(f"⏱️ Total duration: {(duration + phase2_duration)/60:.1f} minutes")
                        print(f"🌐 Both phases used standard WebDriver successfully!")
                    else:
                        print(f"❌ Phase 2 test failed")
            else:
                print(f"⚠️ No CSV file found after Phase 1 completion")
                
        else:
            print(f"\n❌ Phase 1 test failed")
            print(f"⏱️ Failed after: {duration/60:.1f} minutes")
            print(f"\n💡 TROUBLESHOOTING:")
            print(f"   1. Ensure Chrome browser is installed and updated")
            print(f"   2. Check internet connection stability")
            print(f"   3. Try running as administrator")
            print(f"   4. Check if antivirus is blocking WebDriver")
            
            return False
            
        return True
        
    except Exception as e:
        logger.error(f"❌ Error in standard WebDriver Phase 1 test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 STANDARD WEBDRIVER PHASE 1 TEST")
    print("This tool tests Phase 1 processing using standard Chrome WebDriver")
    print("instead of undetected-chromedriver for better stability and compatibility.")
    print("\nPress Ctrl+C to cancel at any time.")
    
    try:
        input("\nPress Enter to start the test...")
        test_standard_webdriver_phase1()
    except KeyboardInterrupt:
        print("\n\n👋 Test cancelled by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
