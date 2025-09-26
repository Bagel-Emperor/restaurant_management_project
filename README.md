# Restaurant Management Project
This repository contains the code for a restaurant management web application, developed as part of an internship assignment for educational purposes.

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
   pip install django python-dotenv djangorestframework
   ```
5. Run migrations:
   ```bash
   python manage.py migrate
   ```
6. Start the development server:
   ```bash
   python manage.py runserver
   ```

### Security Note
- Never commit the `.env` file to version control
- Generate a new SECRET_KEY for production use
- Set DEBUG=False in production environments

## API Endpoints

### User Order History
Authenticated users can retrieve their order history with full details.

**Endpoint:** `GET /PerpexBistro/orders/history/`

**Authentication:** Required (Session or Token)

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

## Purpose
Educational Use Only:
This project is not intended for production use. It was created to practice and demonstrate skills in Django, Python, Git, and web development workflows.
Internship Assignment:
The codebase reflects the requirements and learning objectives of a weekly internship project, including tasks such as custom error page creation, static file management, and Git best practices.
Disclaimer
There may be mistakes, incomplete features, or areas for improvement.
Code review suggestions and automated feedback are welcome and expected.
Security, scalability, and production-readiness were not primary goals.
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

## Production Deployment Checklist

Before deploying to production, ensure you have:

### Security
- [ ] Set `DEBUG=False` in production
- [ ] Generated a strong `SECRET_KEY` (min 50 characters)
- [ ] Configured proper `ALLOWED_HOSTS`
- [ ] Set up HTTPS (SSL/TLS certificates)
- [ ] Configured secure session and CSRF cookies
- [ ] Enabled security headers (HSTS, XSS protection, etc.)

### Database
- [ ] Set up production database (PostgreSQL recommended)
- [ ] Run `python manage.py migrate` on production
- [ ] Set up database backups

### Infrastructure
- [ ] Configure email backend for notifications
- [ ] Set up static file serving (nginx/Apache)
- [ ] Configure logging and monitoring
- [ ] Set up error reporting (Sentry, etc.)

### Dependencies
- [ ] Install all requirements: `pip install -r requirements.txt`
- [ ] Use a WSGI server like Gunicorn or uWSGI
- [ ] Configure reverse proxy (nginx recommended)

---
**Educational Project Notice:**
This project was developed for educational purposes. Please do not use this code as-is for any production environment without proper security auditing and additional hardening.

Feedback and suggestions for improvement are encouraged as part of the learning process.
