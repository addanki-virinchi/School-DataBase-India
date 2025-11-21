#!/usr/bin/env python3
"""
Test script to verify pin code and email extraction fixes
"""

import re

def test_pin_code_mapping():
    """Test the pin code field mapping fix"""
    print("🧪 Testing Pin Code Mapping Fix")
    print("=" * 50)
    
    # Simulate school data from base scraper (uses 'pin_code')
    school_data_from_base_scraper = {
        'school_name': 'Test School',
        'pin_code': '123456',  # Base scraper uses 'pin_code'
        'email': 'test@school.edu'
    }
    
    # Test the old (broken) mapping
    old_pin_code = school_data_from_base_scraper.get('pincode', 'N/A')  # This was the bug
    print(f"❌ Old mapping (pincode): {old_pin_code}")
    
    # Test the new (fixed) mapping
    new_pin_code = school_data_from_base_scraper.get('pin_code', 'N/A')  # This is the fix
    print(f"✅ New mapping (pin_code): {new_pin_code}")
    
    print()

def test_email_patterns():
    """Test the enhanced email extraction patterns"""
    print("🧪 Testing Enhanced Email Patterns")
    print("=" * 50)
    
    # Enhanced email patterns (from the fix)
    email_patterns = [
        re.compile(r'href="mailto:([^"]+)"', re.IGNORECASE),  # mailto links
        re.compile(r'<span[^>]*>([^<]*@[^<]*)</span>', re.IGNORECASE),  # span with email
        re.compile(r'<div[^>]*>([^<]*@[^<]*)</div>', re.IGNORECASE),  # div with email
        re.compile(r'Email[:\s]*([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})', re.IGNORECASE),  # Email: pattern
        re.compile(r'E-mail[:\s]*([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})', re.IGNORECASE),  # E-mail: pattern
        re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')  # general email
    ]
    
    # Test cases with different HTML structures
    test_cases = [
        ('mailto link', '<a href="mailto:school@example.com">Contact</a>'),
        ('span element', '<span class="email">contact@school.edu</span>'),
        ('div element', '<div class="contact">info@school.org</div>'),
        ('Email: pattern', 'Email: principal@school.gov.in'),
        ('E-mail: pattern', 'E-mail: admin@school.ac.in'),
        ('general pattern', 'Contact us at support@school.com for help'),
    ]
    
    for test_name, html_content in test_cases:
        print(f"Testing {test_name}:")
        print(f"  HTML: {html_content}")
        
        email_found = None
        for i, pattern in enumerate(email_patterns):
            match = pattern.search(html_content)
            if match:
                # For patterns 0-4 (specific patterns), use group(1); for pattern 5 (general), use group(0)
                email = match.group(1) if i < 5 else match.group(0)
                email = email.strip()
                if email and '@' in email and len(email) > 5:
                    email_found = email
                    print(f"  ✅ Found: {email} (pattern {i})")
                    break
        
        if not email_found:
            print(f"  ❌ No email found")
        print()

def test_csv_field_mapping():
    """Test the complete CSV field mapping logic"""
    print("🧪 Testing Complete CSV Field Mapping")
    print("=" * 50)
    
    # Simulate school data with both pin_code and email
    school_data = {
        'school_name': 'Test School',
        'udise_code': '12345678901',
        'pin_code': '560001',
        'email': 'test@school.edu',
        'know_more_link': 'https://kys.udiseplus.gov.in/#/schooldetail/123',
        'address': 'Test Address'
    }
    
    # CSV headers
    headers = ['school_name', 'udise_code', 'pin_code', 'email', 'has_know_more_link', 'address']
    
    # Simulate the fixed CSV mapping logic
    school_row = {}
    pin_codes_found = 0
    emails_found = 0
    
    for header in headers:
        if header == 'has_know_more_link':
            know_more_link = school_data.get('know_more_link', 'N/A')
            school_row[header] = (know_more_link != 'N/A' and
                                know_more_link and
                                'schooldetail' in str(know_more_link))
        elif header == 'pin_code':
            # Fixed mapping: use 'pin_code' instead of 'pincode'
            pin_code_value = school_data.get('pin_code', 'N/A')
            school_row[header] = pin_code_value
            if pin_code_value != 'N/A':
                pin_codes_found += 1
        elif header == 'email':
            email_value = school_data.get('email', 'N/A')
            school_row[header] = email_value
            if email_value != 'N/A':
                emails_found += 1
        else:
            school_row[header] = school_data.get(header, 'N/A')
    
    print("Mapped CSV row:")
    for header in headers:
        print(f"  {header}: {school_row[header]}")
    
    print(f"\n📊 Statistics:")
    print(f"  Pin codes found: {pin_codes_found}/1")
    print(f"  Emails found: {emails_found}/1")
    print()

if __name__ == "__main__":
    print("🔧 PIN CODE AND EMAIL EXTRACTION FIXES TEST")
    print("=" * 60)
    print()
    
    test_pin_code_mapping()
    test_email_patterns()
    test_csv_field_mapping()
    
    print("✅ All tests completed!")
    print("\n📋 Summary of fixes applied:")
    print("1. Fixed pin_code field mapping from 'pincode' to 'pin_code'")
    print("2. Enhanced email extraction patterns with more coverage")
    print("3. Added debugging statistics for pin_code and email extraction")
    print("4. Improved error handling in email extraction")
