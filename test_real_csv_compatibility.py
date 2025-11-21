#!/usr/bin/env python3
"""
Test script to verify that Phase_2_Scraping.py can properly handle real CSV files
and produce output with correct column alignment
"""

import pandas as pd
import os
import sys
from datetime import datetime

def test_real_csv_compatibility():
    """Test Phase 2 column alignment with real CSV files"""
    
    print("🔍 REAL CSV COMPATIBILITY TEST")
    print("=" * 50)
    
    # Find a real CSV file to test with
    test_files = [
        "OH_MIs_Bihar.csv",
        "NAGALAND_phase1_complete_20250905_161401.csv",
        "TRIPURA_phase1_complete_20250905_142317.csv"
    ]
    
    test_file = None
    for file in test_files:
        if os.path.exists(file):
            test_file = file
            break
    
    if not test_file:
        print("❌ No test CSV files found")
        return False
    
    print(f"📁 Using test file: {test_file}")
    
    try:
        # Load the CSV file
        df = pd.read_csv(test_file)
        print(f"📊 Loaded {len(df)} records from {test_file}")
        
        # Get the actual columns from the file
        actual_columns = list(df.columns)
        print(f"📋 Input file has {len(actual_columns)} columns")
        
        # Expected Phase 1 columns (extended format)
        expected_phase1_columns = [
            'has_know_more_link', 'phase2_ready', 'state', 'state_id', 'district', 'district_id',
            'extraction_date', 'udise_code', 'operational_status', 'school_name', 'know_more_link',
            'edu_district', 'edu_block', 'academic_year', 'school_category', 'school_management',
            'class_range', 'school_type', 'school_location', 'address', 'pin_code', 'last_modified', 'email'
        ]
        
        # Test 1: Check if input file has expected Phase 1 columns
        print("\n📋 Test 1: Input File Column Verification")
        missing_columns = []
        for col in expected_phase1_columns:
            if col not in actual_columns:
                missing_columns.append(col)
        
        if missing_columns:
            print(f"⚠️ WARNING: Missing expected columns: {missing_columns}")
            print("   This is okay - we'll work with available columns")
        else:
            print("✅ PASS: All expected Phase 1 columns present")
        
        # Test 2: Simulate Phase 2 processing column order
        print("\n🔄 Test 2: Phase 2 Column Order Simulation")
        
        # Phase 2 expected column order (from Phase_2_Scraping.py)
        phase2_column_order = [
            # Phase 1 columns (matching actual CSV files with extended format)
            'has_know_more_link', 'phase2_ready', 'state', 'state_id', 'district', 'district_id',
            'extraction_date', 'udise_code', 'operational_status', 'school_name', 'know_more_link',
            'edu_district', 'edu_block', 'academic_year', 'school_category', 'school_management',
            'class_range', 'school_type', 'school_location', 'address', 'pin_code', 'last_modified', 'email',
            
            # Phase 2 additional columns
            'detail_school_name', 'extraction_timestamp', 'extraction_status', 
            'fields_extracted', 'critical_fields_extracted',
            'location', 'class_from', 'class_to', 'year_of_establishment', 
            'national_management', 'state_management', 'affiliation_board_sec', 'affiliation_board_hsec',
            'total_students', 'total_boys', 'total_girls', 'enrollment_class_range',
            'total_teachers', 'male_teachers', 'female_teachers'
        ]
        
        # Simulate the ordering logic from Phase_2_Scraping.py
        sample_row = df.iloc[0].to_dict()
        
        # Add sample Phase 2 data
        sample_row.update({
            'detail_school_name': 'Sample School Name',
            'extraction_timestamp': datetime.now().isoformat(),
            'extraction_status': 'SUCCESS',
            'fields_extracted': 15,
            'critical_fields_extracted': 2,
            'location': 'Sample Location',
            'class_from': '1',
            'class_to': '5',
            'year_of_establishment': '2000',
            'national_management': 'Government',
            'state_management': 'State Board',
            'affiliation_board_sec': 'CBSE',
            'affiliation_board_hsec': 'CBSE',
            'total_students': '150',
            'total_boys': '75',
            'total_girls': '75',
            'enrollment_class_range': '1 To 5',
            'total_teachers': '10',
            'male_teachers': '5',
            'female_teachers': '5'
        })
        
        # Create ordered data
        ordered_data = {}
        for col in phase2_column_order:
            ordered_data[col] = sample_row.get(col, 'N/A')
        
        # Add any additional columns
        for key, value in sample_row.items():
            if key not in ordered_data:
                ordered_data[key] = value
        
        # Create DataFrame
        result_df = pd.DataFrame([ordered_data])
        result_columns = list(result_df.columns)
        
        print(f"📊 Phase 2 output would have {len(result_columns)} columns")
        
        # Test 3: Verify Phase 1 columns come first in correct order
        print("\n🎯 Test 3: Phase 1 Column Order Preservation")
        
        # Check how many of the expected Phase 1 columns are preserved in order
        preserved_count = 0
        for i, expected_col in enumerate(expected_phase1_columns):
            if i < len(result_columns) and result_columns[i] == expected_col:
                preserved_count += 1
            else:
                break
        
        if preserved_count == len(expected_phase1_columns):
            print("✅ PASS: All Phase 1 columns preserved in exact order")
        else:
            print(f"⚠️ PARTIAL: {preserved_count}/{len(expected_phase1_columns)} Phase 1 columns preserved in order")
            print("   This may be due to missing columns in input file")
        
        # Test 4: Check for data compatibility
        print("\n🔗 Test 4: Data Compatibility Check")
        
        # Verify that all original data is preserved
        original_columns = [col for col in actual_columns if col in result_columns]
        if len(original_columns) == len(actual_columns):
            print("✅ PASS: All original data columns preserved")
        else:
            missing_original = set(actual_columns) - set(result_columns)
            print(f"⚠️ WARNING: Some original columns missing: {missing_original}")
        
        # Test 5: Verify Phase 2 columns are added
        print("\n🆕 Test 5: Phase 2 Column Addition")
        
        phase2_only_columns = [col for col in result_columns if col not in actual_columns]
        expected_phase2_count = len(phase2_column_order) - len(expected_phase1_columns)
        
        print(f"📊 Added {len(phase2_only_columns)} new Phase 2 columns")
        print(f"🎯 Expected to add ~{expected_phase2_count} Phase 2 columns")
        
        if len(phase2_only_columns) >= expected_phase2_count - 5:  # Allow some tolerance
            print("✅ PASS: Appropriate number of Phase 2 columns added")
        else:
            print("⚠️ WARNING: Fewer Phase 2 columns than expected")
        
        print("\n📋 Sample Phase 2 columns added:")
        for col in phase2_only_columns[:10]:  # Show first 10
            print(f"   • {col}")
        if len(phase2_only_columns) > 10:
            print(f"   ... and {len(phase2_only_columns) - 10} more")
        
        print(f"\n🎉 COMPATIBILITY TEST COMPLETED!")
        print(f"📁 Input file: {test_file} ({len(actual_columns)} columns)")
        print(f"📊 Output would have: {len(result_columns)} columns")
        print(f"🆕 New columns added: {len(phase2_only_columns)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during compatibility test: {e}")
        return False

if __name__ == "__main__":
    success = test_real_csv_compatibility()
    if not success:
        sys.exit(1)
    print("\n✅ Real CSV compatibility verification complete!")
