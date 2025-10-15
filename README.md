# Restaurant Management & Ride-Sharing Platform
This repository contains the code for a comprehensive restaurant management and ride-sharing platform, developed as part of an internship assignment for educational purposes. The platform combines traditional restaurant management features with modern ride-sharing capabilities, providing a complete end-to-end solution.

## 🚀 Platform Overview

### Restaurant Management System
- **Menu Management**: Dynamic menu categories and items with availability tracking
- **Order Processing**: Complete order lifecycle management with status tracking
- **Shopping Cart**: Session-based cart system with real-time updates
- **User Profiles**: Customer account management and order history

### Ride-Sharing Platform (Uber Clone)
- **Driver & Rider Registration**: Separate registration systems with role-specific validation
- **JWT Authentication**: Secure, stateless authentication with token refresh
- **User Management**: Comprehensive user profiles and account management
- **API-First Design**: RESTful APIs ready for mobile app integration

## Environment Setup

### Prerequisites
- Python 3.8+
- pip (Python package manager)

### Installation
1. Clone this repository
2. Copy `.env.example` to `.env` and configure your environment variables:
   ```bash
   cp .env.example .env
   ```
3. Edit `.env` file with your specific configuration (generate a new SECRET_KEY)
4. Install dependencies:
   ```bash
   pip install django python-dotenv djangorestframework djangorestframework-simplejwt PyJWT
   ```
5. Run migrations:
   ```bash
   python manage.py migrate
   ```
6. Create a superuser (optional):
   ```bash
   python manage.py createsuperuser
   ```
7. Start the development server:
   ```bash
   python manage.py runserver
   ```

### Security Note
- Never commit the `.env` file to version control
- Generate a new SECRET_KEY for production use
- Set DEBUG=False in production environments

## 🔧 Core Features

### Restaurant Management
- **Dynamic Menu System**: Categories and items with real-time availability
- **Order Management**: Complete order lifecycle with status tracking
- **Shopping Cart**: Session-based cart with add/remove/update functionality
- **Search & Filtering**: Advanced search across menu items and categories
- **Email Notifications**: Order confirmations and status updates

### Ride-Sharing Platform
- **User Registration**: Separate registration flows for riders and drivers
- **JWT Authentication**: Secure token-based authentication with refresh capability
- **Role-Based Access**: Different permissions for riders, drivers, and admin users
- **User Profiles**: Comprehensive profile management with validation
- **API Documentation**: Complete API documentation with examples

## 📚 Documentation

- **[JWT Authentication Guide](JWT_AUTHENTICATION.md)** - Complete JWT implementation guide
- **[Registration API Docs](REGISTRATION_API_DOCS.md)** - Rider and driver registration APIs
- **[Order API Guide](ORDER_API_GUIDE.md)** - Complete order management API documentation
- **[Order Cancellation API](ORDER_CANCELLATION_API.md)** - Order cancellation endpoint details
- **[Order Manager Guide](ORDER_MANAGER_GUIDE.md)** - Custom order manager implementation
- **[Order Total Calculation Guide](ORDER_TOTAL_CALCULATION_GUIDE.md)** - Order total with discount support
- **[Menu Item API Guide](MENU_ITEM_API_GUIDE.md)** - Menu management APIs
- **[Category API Guide](CATEGORY_API_GUIDE.md)** - Menu category CRUD operations
- **[Daily Specials API Guide](DAILY_SPECIALS_API_GUIDE.md)** - Daily specials endpoint documentation
- **[Shopping Cart Guide](SHOPPING_CART_GUIDE.md)** - Cart functionality documentation
- **[Search API Guide](SEARCH_API_GUIDE.md)** - Search and filtering APIs
- **[Ride Booking Documentation](RIDE_BOOKING_DOCS.md)** - Ride-sharing platform APIs
- **[Production Readiness Audit](PRODUCTION_READINESS_AUDIT.md)** - Security and deployment checklist

## 🚀 API Endpoints

### Authentication Endpoints

#### JWT Authentication
- **`POST /api/token/`** - Obtain JWT tokens
- **`POST /api/token/refresh/`** - Refresh access token
- **`POST /PerpexBistro/orders/auth/login/`** - Enhanced login with user data
- **`POST /PerpexBistro/orders/auth/logout/`** - Secure logout with token blacklisting
- **`GET /PerpexBistro/orders/auth/profile/`** - Get current user profile

#### Registration
- **`POST /PerpexBistro/orders/register/rider/`** - Rider registration
- **`POST /PerpexBistro/orders/register/driver/`** - Driver registration with vehicle info

### Restaurant Management Endpoints

#### Orders
- **`GET /PerpexBistro/orders/orders/`** - List orders
- **`POST /PerpexBistro/orders/orders/create/`** - Create new order
- **`GET /PerpexBistro/orders/orders/history/`** - User order history
- **`GET /PerpexBistro/orders/orders/<id>/`** - Order details
- **`POST /PerpexBistro/orders/orders/update-status/`** - Update order status
- **`DELETE /PerpexBistro/orders/orders/<id>/cancel/`** - Cancel order

#### Menu Management
- **`GET /PerpexBistro/api/menu-items/`** - List menu items (with filtering)
- **`POST /PerpexBistro/api/menu-items/`** - Create menu item
- **`GET /PerpexBistro/api/menu-items/<id>/`** - Get menu item details
- **`PUT/PATCH /PerpexBistro/api/menu-items/<id>/`** - Update menu item
- **`DELETE /PerpexBistro/api/menu-items/<id>/`** - Delete menu item
- **`GET /PerpexBistro/api/menu-categories/`** - List menu categories
- **`POST /PerpexBistro/api/menu-categories/`** - Create category
- **`GET /PerpexBistro/api/menu-categories/<id>/`** - Get category details
- **`PUT/PATCH /PerpexBistro/api/menu-categories/<id>/`** - Update category
- **`DELETE /PerpexBistro/api/menu-categories/<id>/`** - Delete category
- **`GET /PerpexBistro/menu/search/`** - Search menu items
- **`GET /PerpexBistro/api/daily-specials/`** - Get daily specials (public, no auth required)

### User Order History
Authenticated users can retrieve their order history with full details.

**Endpoint:** `GET /PerpexBistro/orders/history/`

**Authentication:** Required (Session, Token, or JWT)

**Response Format:**
```json
{
  "count": 2,
  "orders": [
    {
      "id": 1,
      "created_at": "2025-09-19T14:30:00Z",
      "total_amount": "25.99",
      "status": {
        "id": 1,
        "name": "completed"
      },
      "items_count": 2,
      "order_items": [
        {
          "id": 1,
          "menu_item": {
            "id": 1,
            "name": "Margherita Pizza",
            "price": "12.99"
          },
          "quantity": 1,
          "price": "12.99",
          "total_price": "12.99"
        }
      ]
    }
  ]
}
```

**Features:**
- Returns orders for the authenticated user only
- Includes nested order items with menu item details
- Ordered by most recent first
- Includes total item count and calculated totals

## 🛠️ Technology Stack

### Backend
- **Django 5.2.5** - Web framework
- **Django REST Framework 3.16.1** - API framework
- **djangorestframework-simplejwt 5.5.1** - JWT authentication
- **PyJWT 2.10.1** - JWT token handling
- **python-dotenv** - Environment variable management

### Database
- **SQLite** (Development) - Default database
- **PostgreSQL** (Production) - Recommended production database

### Authentication & Security
- **JWT (JSON Web Tokens)** - Stateless authentication
- **Token Blacklisting** - Secure logout functionality
- **Django Built-in Validation** - Email, password, and form validation
- **CSRF Protection** - Cross-site request forgery protection
- **Security Headers** - HSTS, XSS protection, content type sniffing protection

### Testing
- **Django TestCase** - Unit and integration tests
- **Django REST Framework Test Client** - API endpoint testing
- **Custom Test Utilities** - JWT authentication testing tools

## 🧪 Testing

The platform includes comprehensive test coverage:

### Running Tests
```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test orders
python manage.py test home

# Run with verbose output
python manage.py test -v 2

# Run specific test cases
python manage.py test orders.test_jwt_auth
python manage.py test orders.tests.RegistrationAPITestCase
```

### Test Coverage
- **JWT Authentication**: Token generation, refresh, login/logout flows
- **User Registration**: Rider and driver registration with validation
- **Order Management**: Order creation, retrieval, and status updates
- **Menu System**: Menu item and category management
- **Shopping Cart**: Cart operations and session handling
- **API Endpoints**: Complete API functionality testing

### Test Files
- `orders/test_jwt_auth.py` - JWT authentication tests
- `orders/tests.py` - Registration and order management tests
- `home/tests.py` - Menu and cart functionality tests

## 🔐 Security Features

### Authentication Security
- **JWT Token Security**: HS256 algorithm with configurable expiration
- **Token Rotation**: New refresh tokens on each refresh request
- **Token Blacklisting**: Invalidated tokens cannot be reused
- **Password Validation**: Django's built-in password validators
- **Account Status Checking**: Active account validation

### API Security
- **CSRF Protection**: Enabled for web forms
- **CORS Configuration**: Configurable cross-origin requests
- **Rate Limiting**: (Recommended for production)
- **Input Validation**: Comprehensive data validation on all endpoints
- **Error Handling**: Secure error messages without sensitive data exposure

### Production Security
- **HTTPS Enforcement**: SSL redirect in production
- **Security Headers**: HSTS, XSS protection, frame options
- **Secret Key Management**: Environment-based configuration
- **Debug Mode Control**: Environment-controlled debug setting

## 🚀 Getting Started

### Quick Start for Restaurant Management
1. Follow the installation steps above
2. Create menu categories and items via Django Admin
3. Test the shopping cart functionality
4. Place test orders through the web interface

### Quick Start for Ride-Sharing APIs
1. Set up JWT authentication
2. Register test riders and drivers via API endpoints
3. Test authentication flows with JWT tokens
4. Explore the API documentation for integration

### API Testing Examples

#### Register a New Rider
```bash
curl -X POST http://localhost:8000/PerpexBistro/orders/register/rider/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "rider123",
    "email": "rider@example.com",
    "password": "securepassword123",
    "first_name": "John",
    "last_name": "Doe"
  }'
```

#### Login and Get JWT Tokens
```bash
curl -X POST http://localhost:8000/PerpexBistro/orders/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "rider123",
    "password": "securepassword123"
  }'
```

#### Access Protected Endpoint
```bash
curl -X GET http://localhost:8000/PerpexBistro/orders/auth/profile/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## 🎯 Purpose & Scope

### Educational Use
This project was created to practice and demonstrate advanced skills in:
- **Django & Python**: Web framework mastery and API development
- **REST API Design**: RESTful architecture and API best practices
- **Authentication Systems**: JWT implementation and security patterns
- **Database Design**: Model relationships and data validation
- **Testing**: Comprehensive test coverage and quality assurance
- **Git Workflows**: Version control and collaborative development

### Internship Assignment Evolution
The project has evolved through multiple phases:
1. **Phase 1**: Basic restaurant management system
2. **Phase 2**: Advanced menu and cart functionality  
3. **Phase 3**: User registration and role-based access
4. **Phase 4**: JWT authentication and ride-sharing platform APIs

### Current Capabilities
- **Production-Ready Authentication**: Secure JWT implementation
- **Comprehensive APIs**: Full CRUD operations with proper validation
- **Multi-Platform Support**: Web interface + mobile-ready APIs
- **Security Focus**: Following Django security best practices
- **Documentation**: Complete API documentation and guides

### Disclaimer
- This is an educational project demonstrating modern web development practices
- Code reviews and improvement suggestions are welcome
- Some features may require additional hardening for production use
- The project showcases learning progression from basic to advanced concepts
Features
Django-based backend
Custom 404 error page with Bootstrap styling
Static file handling and .gitignore configuration
Example views, templates, and URL routing

# How to Add Menu Items

You can add menu items to the site using either the Django admin interface or the Django shell. Both methods update the database and make items visible on the homepage and menu page.

## Using Django Admin (Recommended)
1. Start the development server:
	```
	python manage.py runserver
	```
2. Open your browser and go to [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)
3. Log in with your superuser credentials (create one with `python manage.py createsuperuser` if needed).
4. Click on **Restaurants** to add a restaurant if none exist.
5. Click on **Menu items** to add menu items. Fill in the details and make sure **Is available** is checked.
6. Save. The items will now appear on the homepage and menu page.

## Using Django Shell
1. Open a terminal in your project directory (where `manage.py` is located).
2. Start the Django shell:
	```
	python manage.py shell
	```
3. Run the following code to create a restaurant (if you don't have one):
	```python
	from home.models import Restaurant
	Restaurant.objects.create(
		 name="Perpex Bistro",
		 owner_name="Owner Name",
		 email="owner@example.com",
		 phone_number="555-1234",
		 address="123 Main St",
		 city="Springfield"
	)
	```
4. Then add menu items:
	```python
	from home.models import MenuItem, Restaurant
	restaurant = Restaurant.objects.first()
	MenuItem.objects.create(name="Margherita Pizza", description="Classic pizza with tomato, mozzarella, and basil.", price=12.99, restaurant=restaurant, is_available=True)
	MenuItem.objects.create(name="Caesar Salad", description="Crisp romaine, parmesan, croutons, and Caesar dressing.", price=8.99, restaurant=restaurant, is_available=True)
	MenuItem.objects.create(name="Grilled Salmon", description="Fresh salmon fillet with lemon butter sauce.", price=16.99, restaurant=restaurant, is_available=True)
	```
5. Type `exit()` to leave the shell.

## 🚢 Production Deployment Checklist

Before deploying to production, ensure you have:

### Security
- [ ] Set `DEBUG=False` in production environment
- [ ] Generated a strong `SECRET_KEY` (min 50 characters, use Django's get_random_secret_key())
- [ ] Configured proper `ALLOWED_HOSTS` for your domain
- [ ] Set up HTTPS (SSL/TLS certificates) - **Required for JWT tokens**
- [ ] Configured secure session and CSRF cookies (`SECURE_SSL_REDIRECT=True`)
- [ ] Enabled security headers (HSTS, XSS protection, frame options)
- [ ] **JWT Security**: Verify `SIMPLE_JWT` settings for production use
- [ ] Configure CORS settings if serving frontend from different domain

### Authentication & JWT
- [ ] **JWT Secret Key**: Use a different signing key than Django's SECRET_KEY (recommended)
- [ ] **Token Lifetimes**: Adjust access/refresh token lifetimes for your security needs
- [ ] **Token Blacklisting**: Ensure token blacklist database tables are migrated
- [ ] **Rate Limiting**: Implement rate limiting on authentication endpoints
- [ ] Test JWT authentication flow in production environment

### Database
- [ ] Set up production database (PostgreSQL recommended)
- [ ] Run all migrations: `python manage.py migrate`
- [ ] **JWT Migrations**: Ensure token blacklist tables are created
- [ ] Set up database backups and recovery procedures
- [ ] Configure database connection pooling

### Infrastructure
- [ ] Configure email backend for notifications and password resets
- [ ] Set up static file serving (nginx/Apache with proper headers)
- [ ] Configure logging and monitoring (structured logging recommended)
- [ ] Set up error reporting (Sentry, Rollbar, etc.)
- [ ] **API Monitoring**: Monitor JWT authentication success/failure rates
- [ ] Configure health check endpoints

### Dependencies & Environment
- [ ] Install all requirements: `pip install django python-dotenv djangorestframework djangorestframework-simplejwt PyJWT`
- [ ] Use a WSGI server like Gunicorn or uWSGI
- [ ] Configure reverse proxy (nginx recommended)
- [ ] Set up environment variable management
- [ ] **JWT Dependencies**: Verify simplejwt and PyJWT versions are compatible

### Testing in Production
- [ ] **API Testing**: Test all authentication endpoints in production
- [ ] **JWT Flow Testing**: Verify complete login/logout/refresh flow
- [ ] **Registration Testing**: Test rider and driver registration flows
- [ ] **Performance Testing**: Load test authentication endpoints
- [ ] **Security Testing**: Penetration test authentication system

---
**Educational Project Notice:**
This project was developed for educational purposes. Please do not use this code as-is for any production environment without proper security auditing and additional hardening.

Feedback and suggestions for improvement are encouraged as part of the learning process.
