# Registration API Documentation

## Overview

The Registration API provides endpoints for creating new rider and driver accounts in the ride-sharing platform. These endpoints handle user account creation, profile setup, and comprehensive validation.

## Base URL
```
http://your-domain.com/PerpexBistro/orders/
```

## Endpoints

---

### POST /register/rider/
Creates a new rider account with associated user profile.

#### Request Headers
```
Content-Type: application/json
```

#### Request Body
```json
{
  "username": "john_rider",
  "email": "john@example.com",
  "password": "securepassword123",
  "first_name": "John",
  "last_name": "Doe",
  "phone": "+1234567890",
  "preferred_payment": "card",
  "default_pickup_address": "123 Main St, City",
  "default_pickup_latitude": 40.7128,
  "default_pickup_longitude": -74.0060
}
```

#### Field Descriptions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `username` | string | Yes | Unique username (max 150 chars) |
| `email` | string | Yes | Valid email address |
| `password` | string | Yes | Minimum 8 characters |
| `first_name` | string | No | User's first name (max 150 chars) |
| `last_name` | string | No | User's last name (max 150 chars) |
| `phone` | string | Yes | Phone number (+999999999 format, 9-15 digits) |
| `preferred_payment` | string | No | Payment method: `card`, `cash`, `wallet`, `paypal` (default: `card`) |
| `default_pickup_address` | string | No | Default pickup location |
| `default_pickup_latitude` | decimal | No | Latitude (must be provided with longitude) |
| `default_pickup_longitude` | decimal | No | Longitude (must be provided with latitude) |

#### Success Response (201 Created)
```json
{
  "success": true,
  "message": "Rider registered successfully",
  "data": {
    "id": 1,
    "username": "john_rider",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "full_name": "John Doe",
    "rider_profile": {
      "id": 1,
      "phone": "+1234567890",
      "preferred_payment": "card",
      "default_pickup_address": "123 Main St, City",
      "average_rating": "0.00",
      "total_rides": 0,
      "is_active": true,
      "created_at": "2025-09-27T18:30:00Z"
    }
  }
}
```

#### Error Response (400 Bad Request)
```json
{
  "success": false,
  "message": "Registration failed due to validation errors",
  "errors": {
    "username": ["A user with this username already exists."],
    "email": ["Enter a valid email address."],
    "phone": ["Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."]
  }
}
```

---

### POST /register/driver/
Creates a new driver account with associated user profile and vehicle information.

#### Request Headers
```
Content-Type: application/json
```

#### Request Body
```json
{
  "username": "mike_driver",
  "email": "mike@example.com",
  "password": "securepassword123",
  "first_name": "Mike",
  "last_name": "Smith",
  "phone": "+1987654321",
  "license_number": "DL12345678",
  "license_expiry": "2025-12-31",
  "vehicle_make": "Toyota",
  "vehicle_model": "Camry",
  "vehicle_year": 2020,
  "vehicle_color": "Silver",
  "vehicle_type": "sedan",
  "license_plate": "ABC123"
}
```

#### Field Descriptions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `username` | string | Yes | Unique username (max 150 chars) |
| `email` | string | Yes | Valid email address |
| `password` | string | Yes | Minimum 8 characters |
| `first_name` | string | No | User's first name (max 150 chars) |
| `last_name` | string | No | User's last name (max 150 chars) |
| `phone` | string | Yes | Phone number (+999999999 format, 9-15 digits) |
| `license_number` | string | Yes | Driver's license number (5-20 chars, alphanumeric) |
| `license_expiry` | string | Yes | License expiry date (YYYY-MM-DD format, must be future) |
| `vehicle_make` | string | Yes | Vehicle manufacturer (max 50 chars) |
| `vehicle_model` | string | Yes | Vehicle model (max 50 chars) |
| `vehicle_year` | integer | Yes | Vehicle year (1980 to current year + 1) |
| `vehicle_color` | string | Yes | Vehicle color (max 30 chars) |
| `vehicle_type` | string | No | Vehicle type: `sedan`, `suv`, `hatchback`, `motorcycle`, `van` (default: `sedan`) |
| `license_plate` | string | Yes | License plate number (2-10 chars, alphanumeric) |

#### Success Response (201 Created)
```json
{
  "success": true,
  "message": "Driver registered successfully",
  "data": {
    "id": 2,
    "username": "mike_driver",
    "email": "mike@example.com",
    "first_name": "Mike",
    "last_name": "Smith",
    "full_name": "Mike Smith",
    "driver_profile": {
      "id": 1,
      "phone": "+1987654321",
      "license_number": "DL12345678",
      "license_expiry": "2025-12-31",
      "vehicle": {
        "make": "Toyota",
        "model": "Camry",
        "year": 2020,
        "color": "Silver",
        "type": "sedan",
        "license_plate": "ABC123",
        "full_name": "2020 Toyota Camry"
      },
      "average_rating": "0.00",
      "total_rides": 0,
      "availability_status": "offline",
      "is_active": true,
      "is_verified": false,
      "is_available_for_rides": false,
      "created_at": "2025-09-27T18:30:00Z"
    }
  }
}
```

#### Error Response (400 Bad Request)
```json
{
  "success": false,
  "message": "Registration failed due to validation errors",
  "errors": {
    "license_number": ["A driver with this license number already exists."],
    "license_expiry": ["License expiry date must be in the future."],
    "vehicle_year": ["Vehicle year must be 1980 or later."],
    "license_plate": ["A driver with this license plate already exists."]
  }
}
```

---

## Validation Rules

### Common Validations
- **Username**: Must be unique, max 150 characters
- **Email**: Must be valid email format and unique
- **Password**: Minimum 8 characters
- **Phone**: Must match pattern `+?1?\\d{9,15}$` and be unique per user type

### Rider-Specific Validations
- **Coordinates**: Both latitude and longitude must be provided together, or both left empty
- **Zero Coordinates**: (0,0) coordinates are rejected as invalid
- **Payment Method**: Must be one of: `card`, `cash`, `wallet`, `paypal`

### Driver-Specific Validations
- **License Number**: 5-20 characters, uppercase alphanumeric, unique
- **License Expiry**: Must be a future date
- **License Plate**: 2-10 characters, uppercase alphanumeric, unique
- **Vehicle Year**: Must be between 1980 and (current year + 1)
- **Vehicle Type**: Must be one of: `sedan`, `suv`, `hatchback`, `motorcycle`, `van`

---

## Error Codes

| HTTP Status | Description |
|-------------|-------------|
| 201 | Registration successful |
| 400 | Validation errors or bad request |
| 500 | Internal server error |

---

## Example Usage

### cURL Examples

#### Rider Registration
```bash
curl -X POST http://your-domain.com/PerpexBistro/orders/register/rider/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_rider",
    "email": "john@example.com",
    "password": "securepass123",
    "first_name": "John",
    "last_name": "Doe",
    "phone": "+1234567890",
    "preferred_payment": "card"
  }'
```

#### Driver Registration
```bash
curl -X POST http://your-domain.com/PerpexBistro/orders/register/driver/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "mike_driver",
    "email": "mike@example.com",
    "password": "securepass123",
    "first_name": "Mike",
    "last_name": "Smith",
    "phone": "+1987654321",
    "license_number": "DL12345678",
    "license_expiry": "2025-12-31",
    "vehicle_make": "Toyota",
    "vehicle_model": "Camry",
    "vehicle_year": 2020,
    "vehicle_color": "Silver",
    "vehicle_type": "sedan",
    "license_plate": "ABC123"
  }'
```

### JavaScript/Fetch Examples

#### Rider Registration
```javascript
const riderData = {
  username: "john_rider",
  email: "john@example.com",
  password: "securepass123",
  first_name: "John",
  last_name: "Doe",
  phone: "+1234567890",
  preferred_payment: "card"
};

fetch('/PerpexBistro/orders/register/rider/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify(riderData)
})
.then(response => response.json())
.then(data => {
  if (data.success) {
    console.log('Rider registered:', data.data);
  } else {
    console.error('Registration failed:', data.errors);
  }
});
```

#### Driver Registration
```javascript
const driverData = {
  username: "mike_driver",
  email: "mike@example.com",
  password: "securepass123",
  first_name: "Mike",
  last_name: "Smith",
  phone: "+1987654321",
  license_number: "DL12345678",
  license_expiry: "2025-12-31",
  vehicle_make: "Toyota",
  vehicle_model: "Camry",
  vehicle_year: 2020,
  vehicle_color: "Silver",
  vehicle_type: "sedan",
  license_plate: "ABC123"
};

fetch('/PerpexBistro/orders/register/driver/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify(driverData)
})
.then(response => response.json())
.then(data => {
  if (data.success) {
    console.log('Driver registered:', data.data);
  } else {
    console.error('Registration failed:', data.errors);
  }
});
```

---

## Testing

### Management Command
A management command is available for testing the registration functionality:

```bash
python manage.py test_registration
```

This command will:
- Test both rider and driver registration with sample data
- Validate all serializer functionality
- Display registration results and system statistics
- Clean up test data automatically

### Unit Tests
Comprehensive unit tests are available in `orders/tests.py`:

```bash
# Run all registration tests
python manage.py test orders.tests -v 2

# Run specific test classes
python manage.py test orders.tests.RiderRegistrationSerializerTest -v 2
python manage.py test orders.tests.DriverRegistrationSerializerTest -v 2
python manage.py test orders.tests.RiderRegistrationAPITest -v 2
python manage.py test orders.tests.DriverRegistrationAPITest -v 2
```

---

## Integration Notes

### Database Relationships
- Each registration creates a Django `User` instance
- Rider profiles are linked via `User.rider_profile` (one-to-one)
- Driver profiles are linked via `User.driver_profile` (one-to-one)
- Profiles inherit user authentication and permissions

### Authentication
- Users can authenticate using Django's built-in authentication system
- Compatible with session authentication and token authentication
- Passwords are automatically hashed using Django's secure hash algorithms

### Future Enhancements
- Email verification workflow
- Phone number verification via SMS
- Driver license verification integration
- Vehicle insurance validation
- Background check integration