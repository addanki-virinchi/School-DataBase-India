#!/usr/bin/env python3
"""
Test script to verify pin code extraction from address field
"""

import re
import pandas as pd

def extract_pin_code_from_address(address):
    """Extract pin code from address field using regex patterns"""
    if not address or address == 'N/A':
        return 'N/A'
    
    # Look for pin code patterns in address
    pin_match = re.search(r'(?:pin|PIN)\s*[:\-]?\s*(\d{6})', address)
    if not pin_match:
        # Look for 6-digit numbers at the end of address
        pin_match = re.search(r'\b(\d{6})\b', address)
    
    if pin_match:
        return pin_match.group(1)
    else:
        return 'N/A'

def test_pin_code_extraction():
    """Test pin code extraction with sample data from Tripura CSV"""
    
    print("🧪 TESTING PIN CODE EXTRACTION FROM ADDRESS FIELD")
    print("="*60)
    
    # Test cases from actual Tripura CSV data
    test_cases = [
        {
            'address': 'Village Mechuria, Pin 799286',
            'expected': '799286'
        },
        {
            'address': 'PURBA MASLI, MANU, 799275',
            'expected': '799275'
        },
        {
            'address': 'NALKATA LTV DHALAI TRIPURA PIN 799266',
            'expected': '799266'
        },
        {
            'address': 'NALKATA, MANU, 799266',
            'expected': '799266'
        },
        {
            'address': 'ICHAI LALCHERRA, KALACHERRA BLOCK, DHARMANAGAR, NORTH TRIPURA',
            'expected': 'N/A'  # No pin code in this address
        },
        {
            'address': 'N/A',
            'expected': 'N/A'
        },
        {
            'address': '',
            'expected': 'N/A'
        }
    ]
    
    all_passed = True
    
    for i, test_case in enumerate(test_cases, 1):
        address = test_case['address']
        expected = test_case['expected']
        
        extracted = extract_pin_code_from_address(address)
        
        status = "✅ PASS" if extracted == expected else "❌ FAIL"
        if extracted != expected:
            all_passed = False
        
        print(f"\nTest {i}: {status}")
        print(f"   Address: {address}")
        print(f"   Expected: {expected}")
        print(f"   Extracted: {extracted}")
    
    print("\n" + "="*60)
    if all_passed:
        print("🎉 ALL TESTS PASSED! Pin code extraction is working correctly.")
    else:
        print("❌ SOME TESTS FAILED! Please check the extraction logic.")
    
    return all_passed

def test_with_real_csv():
    """Test with actual CSV data"""
    
    print("\n🔍 TESTING WITH REAL CSV DATA")
    print("="*60)
    
    try:
        # Load the input CSV
        df = pd.read_csv("Tripura_phase1_complete_20250905_142317.csv")
        print(f"📊 Loaded {len(df)} records from input CSV")
        
        # Test first 5 records
        print("\nTesting first 5 records:")
        
        for i in range(min(5, len(df))):
            row = df.iloc[i]
            address = row.get('address', 'N/A')
            current_pin = row.get('pin_code', 'N/A')
            
            extracted_pin = extract_pin_code_from_address(address)
            
            print(f"\nRecord {i+1}:")
            print(f"   School: {row.get('school_name', 'N/A')}")
            print(f"   Address: {address}")
            print(f"   Current pin_code: {current_pin}")
            print(f"   Extracted pin_code: {extracted_pin}")
            
            if extracted_pin != 'N/A':
                print(f"   ✅ Pin code successfully extracted!")
            else:
                print(f"   ⚠️ No pin code found in address")
        
        return True
        
    except FileNotFoundError:
        print("❌ Input CSV file not found. Please ensure 'Tripura_phase1_complete_20250905_142317.csv' exists.")
        return False
    except Exception as e:
        print(f"❌ Error testing with real CSV: {e}")
        return False

if __name__ == "__main__":
    # Run unit tests
    test_passed = test_pin_code_extraction()
    
    # Test with real CSV data
    csv_test_passed = test_with_real_csv()
    
    print(f"\n🏁 FINAL RESULTS:")
    print(f"   Unit Tests: {'✅ PASSED' if test_passed else '❌ FAILED'}")
    print(f"   CSV Tests: {'✅ PASSED' if csv_test_passed else '❌ FAILED'}")
    
    if test_passed and csv_test_passed:
        print(f"\n🎉 ALL TESTS PASSED! The pin code extraction fix is ready for use.")
        print(f"📝 You can now run Phase_2_Scraping.py and pin codes will be extracted from address fields.")
    else:
        print(f"\n❌ Some tests failed. Please review the extraction logic.")
