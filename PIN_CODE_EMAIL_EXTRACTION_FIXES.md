# Pin Code and Email Extraction Fixes

## Issue Summary
When running `sequential_state_processor.py` with **Option 3** (per state per district processing mode), the scraper was failing to extract:
- **Pin codes** (showing as 'N/A')
- **Email addresses** (missing or not being extracted correctly)

## Root Cause Analysis

### 1. Pin Code Issue
**Problem**: Field mapping mismatch in CSV saving logic
- Base scraper (`phase1_statewise_scraper.py`) extracts pin code as `'pin_code'`
- CSV saving logic in `sequential_state_processor.py` was looking for `'pincode'`
- This mismatch caused all pin codes to show as 'N/A'

**Location**: `sequential_state_processor.py`, line 339 in `save_schools_to_csv_incremental` method

### 2. Email Extraction Issue
**Problem**: Limited email extraction patterns
- Only 3 basic patterns were being used
- Missing coverage for common email formats in school data
- No fallback to text content if HTML parsing failed

**Location**: `sequential_state_processor.py`, lines 558-563 in `extract_email_from_school_element` method

## Fixes Applied

### 1. Pin Code Field Mapping Fix
```python
# BEFORE (broken)
elif header == 'pin_code':
    # Map 'pincode' field to 'pin_code'
    school_row[header] = school.get('pincode', 'N/A')

# AFTER (fixed)
elif header == 'pin_code':
    # Map 'pin_code' field correctly (base scraper uses 'pin_code', not 'pincode')
    school_row[header] = school.get('pin_code', 'N/A')
```

### 2. Enhanced Email Extraction Patterns
```python
# BEFORE (limited patterns)
self._email_patterns = [
    re.compile(r'href="mailto:([^"]+)"', re.IGNORECASE),  # mailto links
    re.compile(r'<span[^>]*>([^<]*@[^<]*)</span>', re.IGNORECASE),  # span with email
    re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')  # general email
]

# AFTER (enhanced patterns)
self._email_patterns = [
    re.compile(r'href="mailto:([^"]+)"', re.IGNORECASE),  # mailto links
    re.compile(r'<span[^>]*>([^<]*@[^<]*)</span>', re.IGNORECASE),  # span with email
    re.compile(r'<div[^>]*>([^<]*@[^<]*)</div>', re.IGNORECASE),  # div with email
    re.compile(r'Email[:\s]*([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})', re.IGNORECASE),  # Email: pattern
    re.compile(r'E-mail[:\s]*([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})', re.IGNORECASE),  # E-mail: pattern
    re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')  # general email
]
```

### 3. Improved Email Extraction Logic
- Added fallback to text content if HTML parsing fails
- Enhanced error handling with debug logging
- Fixed pattern group extraction for additional patterns

### 4. Added Debugging Statistics
- Added pin code and email extraction counters
- Enhanced logging to show extraction success rates
- Better debugging information for troubleshooting

## Files Modified

1. **sequential_state_processor.py**
   - Fixed pin code field mapping (line 339)
   - Enhanced email extraction patterns (lines 560-565)
   - Improved email extraction logic (lines 549-591)
   - Added debugging statistics (lines 319-321, 367-369)

## Testing

Created `test_pin_email_extraction.py` to verify fixes:
- ✅ Pin code mapping fix confirmed
- ✅ Enhanced email patterns working correctly
- ✅ CSV field mapping logic validated
- ✅ All test cases passing

## Impact

### Before Fixes
- Pin codes: 0% extraction rate (always 'N/A')
- Emails: Limited extraction due to narrow patterns

### After Fixes
- Pin codes: Should now extract correctly when present in source data
- Emails: Improved extraction coverage with 6 different patterns
- Better debugging information for monitoring extraction success

## Verification Steps

To verify the fixes are working:

1. Run `sequential_state_processor.py`
2. Select **Option 3** (per state per district)
3. Choose any state and district
4. Monitor the logs for:
   ```
   📍 Pin codes found: X/Y schools
   📧 Emails found: X/Y schools
   ```
5. Check the generated CSV file for pin_code and email columns

## Notes

- The fixes apply to **all processing modes** (Options 1, 2, and 3) since they all use the same underlying extraction methods
- Pin code extraction depends on the source data having pin codes in the expected format
- Email extraction success will vary based on the actual email data available on the school pages
- The enhanced patterns should significantly improve email extraction rates compared to the previous implementation
