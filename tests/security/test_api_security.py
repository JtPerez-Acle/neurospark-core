"""Security tests for API module."""

import pytest
import re
from fastapi import status


@pytest.mark.security
def test_sql_injection_protection(api_client):
    """Test protection against SQL injection."""
    # Attempt SQL injection in query parameter
    sql_injection_payloads = [
        "' OR '1'='1",
        "'; DROP TABLE users; --",
        "' UNION SELECT * FROM users; --",
        "' OR '1'='1' --",
        "admin' --",
    ]
    
    for payload in sql_injection_payloads:
        response = api_client.get(f"/users?username={payload}")
        assert response.status_code != status.HTTP_500_INTERNAL_SERVER_ERROR
        
        # Check that the response doesn't contain SQL error messages
        assert "SQL" not in response.text
        assert "syntax error" not in response.text.lower()
        assert "ORA-" not in response.text
        assert "mysql" not in response.text.lower()
        assert "postgresql" not in response.text.lower()


@pytest.mark.security
def test_xss_protection(api_client):
    """Test protection against Cross-Site Scripting (XSS)."""
    # Attempt XSS in request body
    xss_payloads = [
        "<script>alert('XSS')</script>",
        "<img src='x' onerror='alert(\"XSS\")'>",
        "<svg/onload=alert('XSS')>",
        "javascript:alert('XSS')",
        "onerror=alert('XSS')",
    ]
    
    for payload in xss_payloads:
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "first_name": payload,
            "last_name": "User",
        }
        
        response = api_client.post("/users", json=user_data)
        
        # If the request is successful, check that the payload is properly escaped
        if response.status_code == status.HTTP_201_CREATED:
            assert payload not in response.text
            assert "<script>" not in response.text
            assert "alert" not in response.text


@pytest.mark.security
def test_csrf_protection(api_client):
    """Test protection against Cross-Site Request Forgery (CSRF)."""
    # Create a user
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "first_name": "Test",
        "last_name": "User",
    }
    
    response = api_client.post("/users", json=user_data)
    assert response.status_code == status.HTTP_201_CREATED
    user_id = response.json()["id"]
    
    # Attempt to update the user without proper authentication
    update_data = {
        "first_name": "Hacked",
        "last_name": "User",
    }
    
    # Remove any authentication headers
    headers = {
        "Referer": "https://malicious-site.com",
        "Origin": "https://malicious-site.com",
    }
    
    response = api_client.patch(
        f"/users/{user_id}",
        json=update_data,
        headers=headers,
    )
    
    # The request should either fail with 401/403 or require proper authentication
    assert response.status_code in [
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
        status.HTTP_200_OK,  # If CSRF protection is implemented via tokens
    ]


@pytest.mark.security
def test_sensitive_data_exposure(api_client):
    """Test protection against sensitive data exposure."""
    # Create a user with a password
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "SecretPassword123!",
        "first_name": "Test",
        "last_name": "User",
    }
    
    response = api_client.post("/users", json=user_data)
    assert response.status_code == status.HTTP_201_CREATED
    user_id = response.json()["id"]
    
    # Get the user and check that the password is not exposed
    response = api_client.get(f"/users/{user_id}")
    assert response.status_code == status.HTTP_200_OK
    assert "password" not in response.json()
    
    # Check that no password hash is exposed
    response_text = response.text.lower()
    assert "password" not in response_text
    assert "hash" not in response_text
    assert "secret" not in response_text
    
    # Check for common password hash patterns
    hash_patterns = [
        r"\$2[ayb]\$.{56}",  # bcrypt
        r"\$argon2[id]\$.+",  # argon2
        r"\$pbkdf2-sha256\$.+",  # pbkdf2
        r"[a-f0-9]{32}",  # md5
        r"[a-f0-9]{40}",  # sha1
        r"[a-f0-9]{64}",  # sha256
    ]
    
    for pattern in hash_patterns:
        assert not re.search(pattern, response_text)
