#!/usr/bin/env python3
"""
Script to test the login process for Charon.
"""

import requests
import sys

def test_login(username, password, base_url="http://127.0.0.1:5000"):
    """Test the login process with the given credentials."""
    print(f"Testing login with username: {username}, password: {password}")
    
    # Start a session to maintain cookies
    session = requests.Session()
    
    # First, get the login page to receive any CSRF token if present
    response = session.get(f"{base_url}/login")
    
    # Submit login credentials
    login_data = {
        "username": username,
        "password": password
    }
    response = session.post(f"{base_url}/login", data=login_data, allow_redirects=False)
    
    # Check if we got a redirect (HTTP 302) which indicates successful login
    if response.status_code == 302:
        print("Login successful! Redirect URL:", response.headers.get('Location'))
        # Follow the redirect
        dashboard = session.get(f"{base_url}{response.headers.get('Location')}")
        print(f"Dashboard response status: {dashboard.status_code}")
        return True
    else:
        print(f"Login failed. Status code: {response.status_code}")
        print("Response content:", response.text[:500])  # Print first 500 chars of response
        return False

if __name__ == "__main__":
    username = "admin"
    password = "admin"
    
    if len(sys.argv) > 2:
        username = sys.argv[1]
        password = sys.argv[2]
        
    test_login(username, password) 