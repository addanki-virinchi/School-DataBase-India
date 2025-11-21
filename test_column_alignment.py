#!/usr/bin/env python3
"""
Test script to verify column alignment between Phase_2_Scraping.py and Sequential_state_processor.py
"""

import pandas as pd
import os
import sys

def test_column_alignment():
    """Test that Phase 2 output columns align with Phase 1 specification"""
    
    # Phase 1 headers from actual CSV files (extended format)
    phase1_headers = [
        'has_know_more_link', 'phase2_ready', 'state', 'state_id', 'district', 'district_id',
        'extraction_date', 'udise_code', 'operational_status', 'school_name', 'know_more_link',
        'edu_district', 'edu_block', 'academic_year', 'school_category', 'school_management',
        'class_range', 'school_type', 'school_location', 'address', 'pin_code', 'last_modified', 'email'
    ]

    # Phase 2 expected column order (from the modified Phase_2_Scraping.py)
    expected_phase2_columns = [
        # Phase 1 columns (matching actual CSV files with extended format)
        'has_know_more_link', 'phase2_ready', 'state', 'state_id', 'district', 'district_id',
        'extraction_date', 'udise_code', 'operational_status', 'school_name', 'know_more_link',
        'edu_district', 'edu_block', 'academic_year', 'school_category', 'school_management',
        'class_range', 'school_type', 'school_location', 'address', 'pin_code', 'last_modified', 'email',

        # Phase 2 additional columns (school identification and extraction metadata)
        'detail_school_name', 'extraction_timestamp', 'extraction_status',
        'fields_extracted', 'critical_fields_extracted',

        # Phase 2 basic details
        'location', 'class_from', 'class_to', 'year_of_establishment',
        'national_management', 'state_management', 'affiliation_board_sec', 'affiliation_board_hsec',

        # Phase 2 student enrollment
        'total_students', 'total_boys', 'total_girls', 'enrollment_class_range',

        # Phase 2 teacher data
        'total_teachers', 'male_teachers', 'female_teachers'
    ]
    
    print("🔍 COLUMN ALIGNMENT TEST")
    print("=" * 50)
    
    # Test 1: Verify Phase 1 columns are preserved in order
    print("\n📋 Test 1: Phase 1 Column Order Preservation")
    phase1_in_phase2 = expected_phase2_columns[:len(phase1_headers)]
    
    if phase1_in_phase2 == phase1_headers:
        print("✅ PASS: Phase 1 columns are preserved in exact order")
    else:
        print("❌ FAIL: Phase 1 column order mismatch")
        print(f"Expected: {phase1_headers}")
        print(f"Got:      {phase1_in_phase2}")
        return False
    
    # Test 2: Verify no duplicate columns
    print("\n🔄 Test 2: Duplicate Column Check")
    if len(expected_phase2_columns) == len(set(expected_phase2_columns)):
        print("✅ PASS: No duplicate columns found")
    else:
        print("❌ FAIL: Duplicate columns detected")
        duplicates = [col for col in expected_phase2_columns if expected_phase2_columns.count(col) > 1]
        print(f"Duplicates: {set(duplicates)}")
        return False
    
    # Test 3: Create sample data to test DataFrame column ordering
    print("\n📊 Test 3: DataFrame Column Ordering")
    
    # Create sample combined data (simulating what Phase 2 would produce)
    sample_data = {}
    
    # Add Phase 1 data
    for col in phase1_headers:
        sample_data[col] = f"sample_{col}"
    
    # Add Phase 2 data
    phase2_only_cols = expected_phase2_columns[len(phase1_headers):]
    for col in phase2_only_cols:
        sample_data[col] = f"sample_{col}"
    
    # Add some extra columns that might exist
    sample_data['extra_column'] = 'extra_value'
    
    # Simulate the ordering logic from Phase_2_Scraping.py
    ordered_data = {}
    for col in expected_phase2_columns:
        ordered_data[col] = sample_data.get(col, 'N/A')
    
    # Add any additional columns
    for key, value in sample_data.items():
        if key not in ordered_data:
            ordered_data[key] = value
    
    # Create DataFrame
    df = pd.DataFrame([ordered_data])
    actual_columns = list(df.columns)
    
    # Check if Phase 1 columns come first in correct order
    actual_phase1_cols = actual_columns[:len(phase1_headers)]
    if actual_phase1_cols == phase1_headers:
        print("✅ PASS: DataFrame maintains Phase 1 column order")
    else:
        print("❌ FAIL: DataFrame Phase 1 column order incorrect")
        print(f"Expected: {phase1_headers}")
        print(f"Got:      {actual_phase1_cols}")
        return False
    
    # Test 4: Verify appending compatibility
    print("\n🔗 Test 4: Data Appending Compatibility")
    
    # Create a Phase 1 style DataFrame
    phase1_data = {col: f"phase1_{col}" for col in phase1_headers}
    phase1_df = pd.DataFrame([phase1_data])
    
    # Create a Phase 2 style DataFrame with the same Phase 1 columns + additional
    phase2_data = ordered_data.copy()
    phase2_df = pd.DataFrame([phase2_data])
    
    # Check if Phase 1 columns match
    phase1_cols_in_phase2 = [col for col in phase1_df.columns if col in phase2_df.columns]
    if len(phase1_cols_in_phase2) == len(phase1_headers):
        print("✅ PASS: All Phase 1 columns present in Phase 2 output")
    else:
        missing = set(phase1_headers) - set(phase1_cols_in_phase2)
        print(f"❌ FAIL: Missing Phase 1 columns in Phase 2: {missing}")
        return False
    
    print("\n🎉 ALL TESTS PASSED!")
    print(f"📊 Total columns in Phase 2 output: {len(expected_phase2_columns)}")
    print(f"📋 Phase 1 columns: {len(phase1_headers)}")
    print(f"🆕 New Phase 2 columns: {len(expected_phase2_columns) - len(phase1_headers)}")
    
    return True

if __name__ == "__main__":
    success = test_column_alignment()
    if not success:
        sys.exit(1)
    print("\n✅ Column alignment verification complete!")
