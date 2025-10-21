"""
Quick test script for email validation function.
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'restaurant_management.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from home.utils import validate_email

print("Testing Email Validation Function")
print("=" * 50)

# Test cases
test_cases = [
    ("user@example.com", True, "Valid standard email"),
    ("test.user+tag@sub.example.co.uk", True, "Valid complex email"),
    ("simple@test.org", True, "Valid simple email"),
    ("invalid.email", False, "Missing @ symbol"),
    ("user@domain", False, "Missing TLD"),
    ("@example.com", False, "Missing local part"),
    ("user@", False, "Missing domain"),
    ("", False, "Empty string"),
    ("   ", False, "Only whitespace"),
    ("user name@example.com", False, "Contains space"),
    ("user@exam ple.com", False, "Space in domain"),
]

passed = 0
failed = 0

for email, expected, description in test_cases:
    result = validate_email(email)
    status = "✓ PASS" if result == expected else "✗ FAIL"
    
    if result == expected:
        passed += 1
    else:
        failed += 1
    
    print(f"{status} | {description}")
    print(f"       Email: '{email}'")
    print(f"       Expected: {expected}, Got: {result}")
    print()

print("=" * 50)
print(f"Results: {passed} passed, {failed} failed out of {len(test_cases)} tests")

if failed == 0:
    print("✓ All tests passed!")
    sys.exit(0)
else:
    print("✗ Some tests failed")
    sys.exit(1)
