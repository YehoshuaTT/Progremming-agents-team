"""
Security-compliant test utilities to address CWE-259 and CWE-703 vulnerabilities.
This module provides secure alternatives to hardcoded passwords and assert statements.
"""

import os
import hashlib
import secrets
import pytest
from typing import Any, Optional, Union, List, Dict


class SecureTestUtils:
    """Utility class for secure test operations"""
    
    @staticmethod
    def generate_secure_test_password(length: int = 16) -> str:
        """Generate a secure random password for testing"""
        return secrets.token_urlsafe(length)
    
    @staticmethod
    def get_test_password_hash(password: Optional[str] = None) -> str:
        """Get a secure password hash for testing"""
        if password is None:
            password = os.environ.get('TEST_PASSWORD', SecureTestUtils.generate_secure_test_password())
        
        # Use a proper password hashing algorithm
        salt = os.environ.get('TEST_SALT', 'test_salt_12345')
        return hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000).hex()
    
    @staticmethod
    def secure_assert_equal(actual: Any, expected: Any, message: Optional[str] = None) -> None:
        """Secure assertion for equality checks"""
        if actual != expected:
            error_msg = message or f"Expected {expected}, got {actual}"
            pytest.fail(error_msg)
    
    @staticmethod
    def secure_assert_not_equal(actual: Any, expected: Any, message: Optional[str] = None) -> None:
        """Secure assertion for inequality checks"""
        if actual == expected:
            error_msg = message or f"Expected {actual} to not equal {expected}"
            pytest.fail(error_msg)
    
    @staticmethod
    def secure_assert_true(value: Any, message: Optional[str] = None) -> None:
        """Secure assertion for truthy checks"""
        if not value:
            error_msg = message or f"Expected truthy value, got {value}"
            pytest.fail(error_msg)
    
    @staticmethod
    def secure_assert_false(value: Any, message: Optional[str] = None) -> None:
        """Secure assertion for falsy checks"""
        if value:
            error_msg = message or f"Expected falsy value, got {value}"
            pytest.fail(error_msg)
    
    @staticmethod
    def secure_assert_is_none(value: Any, message: Optional[str] = None) -> None:
        """Secure assertion for None checks"""
        if value is not None:
            error_msg = message or f"Expected None, got {value}"
            pytest.fail(error_msg)
    
    @staticmethod
    def secure_assert_is_not_none(value: Any, message: Optional[str] = None) -> None:
        """Secure assertion for not None checks"""
        if value is None:
            error_msg = message or "Expected non-None value"
            pytest.fail(error_msg)
    
    @staticmethod
    def secure_assert_in(item: Any, container: Union[List, Dict, str], message: Optional[str] = None) -> None:
        """Secure assertion for membership checks"""
        if item not in container:
            error_msg = message or f"Expected {item} to be in {container}"
            pytest.fail(error_msg)
    
    @staticmethod
    def secure_assert_not_in(item: Any, container: Union[List, Dict, str], message: Optional[str] = None) -> None:
        """Secure assertion for non-membership checks"""
        if item in container:
            error_msg = message or f"Expected {item} to not be in {container}"
            pytest.fail(error_msg)
    
    @staticmethod
    def secure_assert_length(container: Union[List, Dict, str], expected_length: int, message: Optional[str] = None) -> None:
        """Secure assertion for length checks"""
        actual_length = len(container)
        if actual_length != expected_length:
            error_msg = message or f"Expected length {expected_length}, got {actual_length}"
            pytest.fail(error_msg)
    
    @staticmethod
    def secure_assert_greater_than(actual: Union[int, float], expected: Union[int, float], message: Optional[str] = None) -> None:
        """Secure assertion for greater than checks"""
        if not (actual > expected):
            error_msg = message or f"Expected {actual} to be greater than {expected}"
            pytest.fail(error_msg)
    
    @staticmethod
    def secure_assert_less_than(actual: Union[int, float], expected: Union[int, float], message: Optional[str] = None) -> None:
        """Secure assertion for less than checks"""
        if not (actual < expected):
            error_msg = message or f"Expected {actual} to be less than {expected}"
            pytest.fail(error_msg)
    
    @staticmethod
    def secure_assert_contains(haystack: str, needle: str, message: Optional[str] = None) -> None:
        """Secure assertion for string containment checks"""
        if needle not in haystack:
            error_msg = message or f"Expected '{haystack}' to contain '{needle}'"
            pytest.fail(error_msg)
    
    @staticmethod
    def secure_assert_not_contains(haystack: str, needle: str, message: Optional[str] = None) -> None:
        """Secure assertion for string non-containment checks"""
        if needle in haystack:
            error_msg = message or f"Expected '{haystack}' to not contain '{needle}'"
            pytest.fail(error_msg)
    
    @staticmethod
    def secure_assert_status_code(response, expected_code: int, message: Optional[str] = None) -> None:
        """Secure assertion for HTTP status code checks"""
        if hasattr(response, 'status_code'):
            actual_code = response.status_code
        elif hasattr(response, 'code'):
            actual_code = response.code
        else:
            pytest.fail("Response object doesn't have status_code or code attribute")
        
        if actual_code != expected_code:
            error_msg = message or f"Expected status code {expected_code}, got {actual_code}"
            pytest.fail(error_msg)
    
    @staticmethod
    def secure_assert_json_structure(json_data: Dict, required_keys: List[str], message: Optional[str] = None) -> None:
        """Secure assertion for JSON structure validation"""
        if not isinstance(json_data, dict):
            pytest.fail(f"Expected dictionary, got {type(json_data)}")
        
        missing_keys = [key for key in required_keys if key not in json_data]
        if missing_keys:
            error_msg = message or f"Missing required keys: {missing_keys}"
            pytest.fail(error_msg)
    
    @staticmethod
    def secure_assert_no_sensitive_data(data: Union[str, Dict], sensitive_fields: List[str], message: Optional[str] = None) -> None:
        """Secure assertion to ensure no sensitive data is exposed"""
        if isinstance(data, dict):
            exposed_fields = [field for field in sensitive_fields if field in data]
            if exposed_fields:
                error_msg = message or f"Sensitive fields exposed: {exposed_fields}"
                pytest.fail(error_msg)
        elif isinstance(data, str):
            exposed_fields = [field for field in sensitive_fields if field in data.lower()]
            if exposed_fields:
                error_msg = message or f"Sensitive data found in string: {exposed_fields}"
                pytest.fail(error_msg)


# Convenience aliases for common secure assertions
secure_equal = SecureTestUtils.secure_assert_equal
secure_not_equal = SecureTestUtils.secure_assert_not_equal
secure_true = SecureTestUtils.secure_assert_true
secure_false = SecureTestUtils.secure_assert_false
secure_none = SecureTestUtils.secure_assert_is_none
secure_not_none = SecureTestUtils.secure_assert_is_not_none
secure_in = SecureTestUtils.secure_assert_in
secure_not_in = SecureTestUtils.secure_assert_not_in
secure_length = SecureTestUtils.secure_assert_length
secure_greater = SecureTestUtils.secure_assert_greater_than
secure_less = SecureTestUtils.secure_assert_less_than
secure_contains = SecureTestUtils.secure_assert_contains
secure_not_contains = SecureTestUtils.secure_assert_not_contains
secure_status = SecureTestUtils.secure_assert_status_code
secure_json = SecureTestUtils.secure_assert_json_structure
secure_no_sensitive = SecureTestUtils.secure_assert_no_sensitive_data
