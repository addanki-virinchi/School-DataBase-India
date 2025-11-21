#!/usr/bin/env python3
"""
Test script to specifically diagnose SIKKIM state Phase 1 processing issues
"""

import sys
import os
import logging
import time

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_sikkim_phase1():
    """Test SIKKIM state Phase 1 processing with enhanced diagnostics"""
    try:
        # Import the processor
        from State_processor_Multi import SequentialStateProcessor
        
        print("🔍 SIKKIM STATE PHASE 1 DIAGNOSTIC TEST")
        print("="*60)
        
        # Create processor instance
        processor = SequentialStateProcessor()
        
        # Test SIKKIM specifically
        state_name = "SIKKIM"
        
        print(f"🎯 Testing Phase 1 for: {state_name}")
        print(f"🔧 Enhanced WebDriver configuration enabled")
        print(f"🔄 Enhanced retry mechanism enabled")
        
        # Get retry configuration for SIKKIM
        retry_config = processor.get_state_retry_config(state_name)
        print(f"📊 SIKKIM Configuration:")
        print(f"   Max retries: {retry_config['max_retries']}")
        print(f"   Retry delay: {retry_config['retry_delay']} seconds")
        
        # Start timing
        start_time = time.time()
        
        print(f"\n🚀 Starting enhanced Phase 1 test for {state_name}...")
        success = processor.run_phase1_for_state(state_name)
        
        # Calculate duration
        duration = time.time() - start_time
        
        if success:
            print(f"\n✅ SIKKIM Phase 1 test completed successfully!")
            print(f"⏱️ Duration: {duration/60:.1f} minutes")
            
            # Look for generated CSV
            csv_file = processor.find_phase1_csv_for_state(state_name)
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
                    
                    # Show sample data
                    if len(df) > 0:
                        print(f"\n📋 SAMPLE DATA:")
                        sample = df.iloc[0]
                        print(f"   🏫 School: {sample.get('school_name', 'N/A')}")
                        print(f"   🏛️ District: {sample.get('district_name', 'N/A')}")
                        print(f"   🔗 Link: {sample.get('know_more_link', 'N/A')[:50]}...")
                        
                except Exception as e:
                    print(f"   ⚠️ CSV analysis error: {e}")
                
                # Offer Phase 2 test
                print(f"\n🧪 PHASE 2 TEST OPTION:")
                test_phase2 = input(f"Test multi-threaded Phase 2 for SIKKIM? (y/n): ").strip().lower()
                if test_phase2 == 'y':
                    print(f"\n🧵 Testing multi-threaded Phase 2 for SIKKIM...")
                    phase2_start = time.time()
                    
                    phase2_success = processor.run_phase2_for_state(state_name, csv_file, use_multithreading=True)
                    phase2_duration = time.time() - phase2_start
                    
                    if phase2_success:
                        print(f"✅ Phase 2 test completed successfully!")
                        print(f"⏱️ Phase 2 duration: {phase2_duration/60:.1f} minutes")
                        print(f"⏱️ Total duration: {(duration + phase2_duration)/60:.1f} minutes")
                    else:
                        print(f"❌ Phase 2 test failed")
            else:
                print(f"⚠️ No CSV file found after Phase 1 completion")
                
        else:
            print(f"\n❌ SIKKIM Phase 1 test failed")
            print(f"⏱️ Failed after: {duration/60:.1f} minutes")
            print(f"\n💡 TROUBLESHOOTING RECOMMENDATIONS:")
            print(f"   1. Check internet connection stability")
            print(f"   2. Ensure Chrome browser is updated")
            print(f"   3. Try running during off-peak hours (early morning/late night)")
            print(f"   4. Check if antivirus is blocking WebDriver")
            print(f"   5. Try running as administrator")
            print(f"   6. Check system resources (RAM/CPU usage)")
            
            return False
            
        return True
        
    except Exception as e:
        logger.error(f"❌ Error in SIKKIM Phase 1 test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔍 SIKKIM STATE DIAGNOSTIC TOOL")
    print("This tool will test Phase 1 processing specifically for SIKKIM state")
    print("with enhanced WebDriver stability and retry mechanisms.")
    print("\nPress Ctrl+C to cancel at any time.")
    
    try:
        input("\nPress Enter to start the test...")
        test_sikkim_phase1()
    except KeyboardInterrupt:
        print("\n\n👋 Test cancelled by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
