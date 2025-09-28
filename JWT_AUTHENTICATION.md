# JWT Authentication Implementation for Ride-Sharing Platform

## Overview

This document describes the JWT (JSON Web Token) authentication implementation for the ride-sharing platform built with Django and Django REST Framework.

## Features

- **Secure JWT Authentication**: Industry-standard JWT tokens for stateless authentication
- **Token Refresh**: Automatic token refresh to maintain user sessions
- **Token Blacklisting**: Secure logout with token invalidation
- **Enhanced User Data**: Additional user information included in authentication responses
- **Comprehensive Error Handling**: Detailed error messages for different authentication scenarios
- **Multiple Authentication Methods**: JWT works alongside existing session and token authentication

## Endpoints

### Standard JWT Endpoints

#### 1. Token Obtain (Login)
- **URL**: `/api/token/`
- **Method**: `POST`
- **Description**: Obtain JWT tokens with username and password
- **Request Body**:
  ```json
  {
    "username": "your_username",
    "password": "your_password"
  }
  ```
- **Response (Success - 200)**:
  ```json
  {
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "user": {
      "id": 1,
      "username": "testuser",
      "email": "test@example.com",
      "first_name": "Test",
      "last_name": "User",
      "is_staff": false,
      "is_superuser": false,
      "is_active": true,
      "date_joined": "2025-01-01T00:00:00Z",
      "last_login": "2025-01-01T12:00:00Z"
    }
  }
  ```
- **Response (Error - 401)**:
  ```json
  {
    "detail": "No active account found with the given credentials"
  }
  ```

#### 2. Token Refresh
- **URL**: `/api/token/refresh/`
- **Method**: `POST`
- **Description**: Refresh access token using refresh token
- **Request Body**:
  ```json
  {
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
  }
  ```
- **Response (Success - 200)**:
  ```json
  {
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
  }
  ```
- **Response (Error - 401)**:
  ```json
  {
    "detail": "Token is invalid or expired",
    "code": "token_not_valid"
  }
  ```

### Custom JWT Endpoints

#### 3. Enhanced Login
- **URL**: `/PerpexBistro/orders/auth/login/`
- **Method**: `POST`
- **Description**: Enhanced login with detailed error handling and validation
- **Request Body**:
  ```json
  {
    "username": "your_username",
    "password": "your_password"
  }
  ```
- **Response (Success - 200)**:
  ```json
  {
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "user": {
      "id": 1,
      "username": "testuser",
      "email": "test@example.com",
      "first_name": "Test",
      "last_name": "User",
      "is_staff": false,
      "is_superuser": false,
      "is_active": true,
      "date_joined": "2025-01-01T00:00:00Z",
      "last_login": "2025-01-01T12:00:00Z"
    },
    "message": "Login successful"
  }
  ```
- **Response (Invalid Credentials - 401)**:
  ```json
  {
    "error": "Authentication failed",
    "message": "Invalid username or password"
  }
  ```
- **Response (Inactive Account - 403)**:
  ```json
  {
    "error": "Account disabled",
    "message": "Your account has been disabled. Please contact support."
  }
  ```
- **Response (Validation Error - 400)**:
  ```json
  {
    "error": "Validation failed",
    "message": "Invalid input data",
    "details": {
      "username": ["Username cannot be empty."],
      "password": ["Password must be at least 8 characters long."]
    }
  }
  ```

#### 4. Logout
- **URL**: `/PerpexBistro/orders/auth/logout/`
- **Method**: `POST`
- **Description**: Logout and blacklist refresh token
- **Headers**: `Authorization: Bearer <access_token>`
- **Request Body**:
  ```json
  {
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
  }
  ```
- **Response (Success - 200)**:
  ```json
  {
    "message": "Logout successful"
  }
  ```
- **Response (Missing Token - 400)**:
  ```json
  {
    "error": "Missing token",
    "message": "Refresh token is required for logout"
  }
  ```

#### 5. User Profile
- **URL**: `/PerpexBistro/orders/auth/profile/`
- **Method**: `GET`
- **Description**: Get current user profile information
- **Headers**: `Authorization: Bearer <access_token>`
- **Response (Success - 200)**:
  ```json
  {
    "user": {
      "id": 1,
      "username": "testuser",
      "email": "test@example.com",
      "first_name": "Test",
      "last_name": "User",
      "is_staff": false,
      "is_superuser": false,
      "is_active": true,
      "date_joined": "2025-01-01T00:00:00Z",
      "last_login": "2025-01-01T12:00:00Z"
    }
  }
  ```
- **Response (Unauthorized - 401)**:
  ```json
  {
    "detail": "Authentication credentials were not provided."
  }
  ```

#### 6. Custom Token Obtain
- **URL**: `/PerpexBistro/orders/auth/token/`
- **Method**: `POST`
- **Description**: Enhanced token obtain with custom error handling
- **Request/Response**: Same as standard token obtain endpoint

#### 7. Custom Token Refresh
- **URL**: `/PerpexBistro/orders/auth/token/refresh/`
- **Method**: `POST`
- **Description**: Enhanced token refresh with custom error handling
- **Request/Response**: Same as standard token refresh endpoint

## Authentication Usage

### Frontend Integration

#### JavaScript/TypeScript Example
```javascript
// Login function
async function login(username, password) {
  try {
    const response = await fetch('/PerpexBistro/orders/auth/login/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ username, password })
    });

    if (response.ok) {
      const data = await response.json();
      
      // Store tokens
      localStorage.setItem('access_token', data.access);
      localStorage.setItem('refresh_token', data.refresh);
      localStorage.setItem('user_data', JSON.stringify(data.user));
      
      console.log('Login successful:', data.message);
      return data;
    } else {
      const error = await response.json();
      throw new Error(error.message || 'Login failed');
    }
  } catch (error) {
    console.error('Login error:', error.message);
    throw error;
  }
}

// Make authenticated requests
async function makeAuthenticatedRequest(url, options = {}) {
  const token = localStorage.getItem('access_token');
  
  const headers = {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`,
    ...options.headers
  };

  try {
    const response = await fetch(url, {
      ...options,
      headers
    });

    if (response.status === 401) {
      // Token might be expired, try to refresh
      const refreshed = await refreshToken();
      if (refreshed) {
        // Retry with new token
        headers.Authorization = `Bearer ${localStorage.getItem('access_token')}`;
        return fetch(url, { ...options, headers });
      } else {
        // Refresh failed, redirect to login
        window.location.href = '/login';
      }
    }

    return response;
  } catch (error) {
    console.error('Request error:', error);
    throw error;
  }
}

// Token refresh function
async function refreshToken() {
  const refreshToken = localStorage.getItem('refresh_token');
  
  if (!refreshToken) {
    return false;
  }

  try {
    const response = await fetch('/api/token/refresh/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ refresh: refreshToken })
    });

    if (response.ok) {
      const data = await response.json();
      localStorage.setItem('access_token', data.access);
      return true;
    } else {
      // Refresh token is invalid, clear storage
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user_data');
      return false;
    }
  } catch (error) {
    console.error('Token refresh error:', error);
    return false;
  }
}

// Logout function
async function logout() {
  const refreshToken = localStorage.getItem('refresh_token');
  
  if (refreshToken) {
    try {
      await fetch('/PerpexBistro/orders/auth/logout/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        },
        body: JSON.stringify({ refresh: refreshToken })
      });
    } catch (error) {
      console.error('Logout error:', error);
    }
  }

  // Clear local storage
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('user_data');
  
  // Redirect to login
  window.location.href = '/login';
}
```

#### Python/Django Client Example
```python
import requests
import json

class JWTClient:
    def __init__(self, base_url='http://localhost:8000'):
        self.base_url = base_url
        self.access_token = None
        self.refresh_token = None
        
    def login(self, username, password):
        \"\"\"Login and store tokens.\"\"\"
        url = f"{self.base_url}/PerpexBistro/orders/auth/login/"
        data = {
            'username': username,
            'password': password
        }
        
        response = requests.post(url, json=data)
        
        if response.status_code == 200:
            data = response.json()
            self.access_token = data['access']
            self.refresh_token = data['refresh']
            return data
        else:
            raise Exception(f"Login failed: {response.json()}")
    
    def refresh_access_token(self):
        \"\"\"Refresh access token.\"\"\"
        if not self.refresh_token:
            raise Exception("No refresh token available")
            
        url = f"{self.base_url}/api/token/refresh/"
        data = {'refresh': self.refresh_token}
        
        response = requests.post(url, json=data)
        
        if response.status_code == 200:
            self.access_token = response.json()['access']
            return True
        else:
            return False
    
    def make_request(self, method, endpoint, **kwargs):
        \"\"\"Make authenticated request.\"\"\"
        if not self.access_token:
            raise Exception("Not authenticated")
            
        headers = kwargs.get('headers', {})
        headers['Authorization'] = f'Bearer {self.access_token}'
        kwargs['headers'] = headers
        
        url = f"{self.base_url}{endpoint}"
        response = requests.request(method, url, **kwargs)
        
        if response.status_code == 401:
            # Try to refresh token
            if self.refresh_access_token():
                headers['Authorization'] = f'Bearer {self.access_token}'
                response = requests.request(method, url, **kwargs)
            else:
                raise Exception("Authentication failed")
        
        return response
    
    def logout(self):
        \"\"\"Logout and blacklist tokens.\"\"\"
        if self.refresh_token:
            url = f"{self.base_url}/PerpexBistro/orders/auth/logout/"
            data = {'refresh': self.refresh_token}
            headers = {'Authorization': f'Bearer {self.access_token}'}
            
            requests.post(url, json=data, headers=headers)
        
        self.access_token = None
        self.refresh_token = None

# Usage example
client = JWTClient()
user_data = client.login('username', 'password')
print(f"Logged in as: {user_data['user']['username']}")

# Make authenticated request
response = client.make_request('GET', '/PerpexBistro/orders/auth/profile/')
profile = response.json()
print(f"User profile: {profile}")

# Logout
client.logout()
```

## Token Configuration

The JWT tokens are configured with the following settings:

- **Access Token Lifetime**: 1 hour
- **Refresh Token Lifetime**: 7 days
- **Token Rotation**: Enabled (new refresh token on each refresh)
- **Token Blacklisting**: Enabled (for secure logout)
- **Algorithm**: HS256
- **Header Type**: Bearer

## Security Features

1. **Token Blacklisting**: Refresh tokens are blacklisted on logout
2. **Token Rotation**: New refresh tokens generated on each refresh
3. **Secure Headers**: Proper authorization header validation
4. **Error Handling**: Detailed but secure error messages
5. **Input Validation**: Comprehensive validation of login credentials
6. **Account Status Check**: Validation of active account status

## Testing

The JWT authentication system includes comprehensive tests covering:

- Token generation and validation
- Token refresh functionality
- User login/logout flows
- Protected endpoint access
- Error handling scenarios
- Integration with existing authentication methods

Run tests with:
```bash
python manage.py test orders.test_jwt_auth
```

## Migration from Session Authentication

To migrate existing applications from session-based authentication to JWT:

1. **Gradual Migration**: JWT authentication works alongside existing session authentication
2. **Update Frontend**: Modify frontend to use JWT tokens instead of session cookies
3. **API Endpoints**: Use JWT authentication for API endpoints while maintaining session auth for web views
4. **Mobile Apps**: Use JWT tokens for mobile app authentication

## Troubleshooting

### Common Issues

1. **401 Unauthorized**: Check token format and expiration
2. **Token Refresh Failed**: Verify refresh token is valid and not blacklisted
3. **CORS Issues**: Ensure proper CORS headers for cross-origin requests
4. **URL Trailing Slash**: Django requires trailing slashes for POST requests

### Debug Mode

Set `DEBUG=True` in environment variables for detailed error messages during development.

### Logging

JWT authentication includes comprehensive logging for:
- Successful logins
- Failed authentication attempts
- Token refresh operations
- Logout operations

Check Django logs for authentication-related events.