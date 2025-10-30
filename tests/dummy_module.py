"""
Dummy Module for Testing - Contains intentional syntax error for Cursor Bridge testing
"""

# This file will be intentionally broken by the test harness
# Cursor Bridge should detect and fix it

def test_function():
    # Missing closing parenthesis - intentional error
    return "test" 

def another_function():
    # This should be fine after Cursor Bridge fixes the above
    return True




