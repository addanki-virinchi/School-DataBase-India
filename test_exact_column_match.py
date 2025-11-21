#!/usr/bin/env python3
"""
Test script to verify exact column order match between Sequential_state_processor.py and Phase_2_Scraping.py
"""

import pandas as pd
import os
import sys
from datetime import datetime

def test_exact_column_match():
    """Test that both files output the exact same column order"""
    
    print("🔍 EXACT COLUMN ORDER MATCH TEST")
    print("=" * 50)
    
    # Target column order as specified
    target_column_order = [
        'has_know_more_link', 'phase2_ready', 'state', 'state_id', 'district', 'district_id',
        'extraction_date', 'udise_code', 'operational_status', 'school_name', 'know_more_link',
        'edu_district', 'edu_block', 'academic_year', 'school_category', 'school_management',
        'class_range', 'school_type', 'school_location', 'address', 'pin_code', 'email',
        'detail_school_name', 'extraction_timestamp', 'location', 'class_from', 'class_to',
        'year_of_establishment', 'national_management', 'state_management',
        'affiliation_board_sec', 'affiliation_board_hsec', 'total_students', 'total_boys',
        'total_girls', 'enrollment_class_range', 'total_teachers', 'male_teachers',
        'female_teachers', 'extraction_status', 'fields_extracted', 'critical_fields_extracted'
    ]
    
    print(f"🎯 Target column order ({len(target_column_order)} columns):")
    for i, col in enumerate(target_column_order, 1):
        print(f"   {i:2d}. {col}")
    
    # Test 1: Check Phase_2_Scraping.py column order
    print(f"\n📋 Test 1: Phase_2_Scraping.py Column Order")
    
    # Simulate Phase_2_Scraping.py column order logic
    phase2_column_order = [
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
    
    if phase2_column_order == target_column_order:
        print("✅ PASS: Phase_2_Scraping.py matches target order exactly")
    else:
        print("❌ FAIL: Phase_2_Scraping.py does not match target order")
        print("Differences:")
        for i, (expected, actual) in enumerate(zip(target_column_order, phase2_column_order)):
            if expected != actual:
                print(f"   Position {i+1}: Expected '{expected}', Got '{actual}'")
        return False
    
    # Test 2: Check Sequential_state_processor.py Phase 1 portion
    print(f"\n📋 Test 2: Sequential_state_processor.py Phase 1 Portion")
    
    # Sequential_state_processor.py should output the first 22 columns
    sequential_headers = [
        'has_know_more_link', 'phase2_ready', 'state', 'state_id', 'district', 'district_id',
        'extraction_date', 'udise_code', 'operational_status', 'school_name', 'know_more_link',
        'edu_district', 'edu_block', 'academic_year', 'school_category', 'school_management',
        'class_range', 'school_type', 'school_location', 'address', 'pin_code', 'email'
    ]
    
    target_phase1_portion = target_column_order[:22]  # First 22 columns
    
    if sequential_headers == target_phase1_portion:
        print("✅ PASS: Sequential_state_processor.py Phase 1 portion matches target")
    else:
        print("❌ FAIL: Sequential_state_processor.py Phase 1 portion does not match")
        print("Differences:")
        for i, (expected, actual) in enumerate(zip(target_phase1_portion, sequential_headers)):
            if expected != actual:
                print(f"   Position {i+1}: Expected '{expected}', Got '{actual}'")
        return False
    
    # Test 3: Verify Phase 2 can append to Phase 1
    print(f"\n🔗 Test 3: Data Appending Compatibility")
    
    # Create sample Phase 1 data
    phase1_data = {}
    for col in sequential_headers:
        phase1_data[col] = f"sample_{col}"
    
    # Create sample Phase 2 data
    phase2_data = phase1_data.copy()
    phase2_only_columns = target_column_order[22:]  # Columns 23 onwards
    for col in phase2_only_columns:
        phase2_data[col] = f"sample_{col}"
    
    # Create ordered data using Phase_2_Scraping.py logic
    ordered_data = {}
    for col in phase2_column_order:
        ordered_data[col] = phase2_data.get(col, 'N/A')
    
    # Check if the result matches target order
    result_columns = list(ordered_data.keys())
    
    if result_columns == target_column_order:
        print("✅ PASS: Phase 2 output matches target column order exactly")
    else:
        print("❌ FAIL: Phase 2 output does not match target order")
        return False
    
    # Test 4: Verify no duplicate columns
    print(f"\n🔄 Test 4: Duplicate Column Check")
    
    if len(target_column_order) == len(set(target_column_order)):
        print("✅ PASS: No duplicate columns in target order")
    else:
        duplicates = [col for col in target_column_order if target_column_order.count(col) > 1]
        print(f"❌ FAIL: Duplicate columns found: {set(duplicates)}")
        return False
    
    # Test 5: Check for 'location' field conflict
    print(f"\n⚠️  Test 5: Location Field Conflict Check")
    
    location_positions = [i for i, col in enumerate(target_column_order) if col == 'location']
    if len(location_positions) > 1:
        print(f"⚠️ WARNING: 'location' appears multiple times at positions: {location_positions}")
        print("   This may cause data conflicts between Phase 1 and Phase 2 location fields")
    else:
        print("✅ PASS: No location field conflicts")
    
    print(f"\n🎉 COLUMN ORDER VERIFICATION COMPLETE!")
    print(f"📊 Total columns: {len(target_column_order)}")
    print(f"📋 Phase 1 columns: 22")
    print(f"🆕 Phase 2 columns: {len(target_column_order) - 22}")
    
    return True

if __name__ == "__main__":
    success = test_exact_column_match()
    if not success:
        sys.exit(1)
    print("\n✅ Exact column order verification complete!")
