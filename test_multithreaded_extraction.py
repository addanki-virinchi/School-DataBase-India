#!/usr/bin/env python3
"""
Test script to verify the multi-threaded Phase 2 extraction functionality
"""

import sys
import os
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_extraction():
    """Test the multi-threaded extraction with a sample CSV file"""
    try:
        # Import the processor
        from State_processor_Multi import SequentialStateProcessor
        
        print("🧪 TESTING MULTI-THREADED PHASE 2 EXTRACTION")
        print("="*60)
        
        # Create processor instance
        processor = SequentialStateProcessor()
        
        # Enable multi-threading
        processor.use_multithreading = True
        
        # Look for existing CSV files
        import glob
        pattern = "*_phase1_complete_*.csv"
        csv_files = glob.glob(pattern)
        
        if not csv_files:
            # Fallback: look for old naming convention
            pattern = "*_with_links_*.csv"
            csv_files = glob.glob(pattern)
            
        if not csv_files:
            print("❌ No Phase 1 CSV files found for testing!")
            print("Please run Phase 1 first to generate CSV files.")
            return False
        
        # Use the first available CSV file
        test_file = csv_files[0]
        print(f"📁 Testing with file: {test_file}")
        
        # Extract state name
        state_name = processor.extract_state_name_from_filename(test_file)
        print(f"🏛️ State: {state_name}")
        print(f"🧵 Mode: Multi-threaded (Standard WebDriver)")
        
        # Run the test
        print("\n🚀 Starting extraction test...")
        success = processor.run_phase2_for_state(state_name, test_file, use_multithreading=True)
        
        if success:
            print(f"\n✅ Multi-threaded extraction test completed successfully!")
            print(f"📊 Check the generated CSV file for results")
            
            # Look for the generated file
            import glob
            output_pattern = f"*_phase2_multithreaded_*.csv"
            output_files = glob.glob(output_pattern)
            if output_files:
                latest_output = max(output_files, key=os.path.getctime)
                print(f"📁 Generated file: {latest_output}")
                
                # Quick analysis of the output
                import pandas as pd
                df = pd.read_csv(latest_output)
                
                print(f"\n📊 EXTRACTION ANALYSIS:")
                print(f"   📋 Total records processed: {len(df)}")
                
                # Check key fields
                key_fields = ['total_students', 'total_teachers', 'detail_school_name', 'school_type', 
                             'affiliation_board_sec', 'affiliation_board_hsec', 'state_management', 
                             'national_management', 'total_boys', 'total_girls', 'male_teachers', 'female_teachers']
                
                for field in key_fields:
                    if field in df.columns:
                        non_na_count = len(df[df[field] != 'N/A'])
                        percentage = (non_na_count / len(df)) * 100
                        print(f"   📈 {field}: {non_na_count}/{len(df)} ({percentage:.1f}%) extracted")
                
                # Show sample data
                print(f"\n📋 SAMPLE EXTRACTED DATA:")
                if len(df) > 0:
                    sample = df.iloc[0]
                    print(f"   🏫 School: {sample.get('detail_school_name', 'N/A')}")
                    print(f"   👥 Students: {sample.get('total_students', 'N/A')}")
                    print(f"   👨‍🏫 Teachers: {sample.get('total_teachers', 'N/A')}")
                    print(f"   🏷️ Type: {sample.get('school_type', 'N/A')}")
                    print(f"   📋 Category: {sample.get('school_category', 'N/A')}")
                    print(f"   🎓 Affiliation Sec: {sample.get('affiliation_board_sec', 'N/A')}")
                    print(f"   🎓 Affiliation HSec: {sample.get('affiliation_board_hsec', 'N/A')}")
            
            return True
        else:
            print(f"\n❌ Multi-threaded extraction test failed")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error in extraction test: {e}")
        return False

if __name__ == "__main__":
    test_extraction()
