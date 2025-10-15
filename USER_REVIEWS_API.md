# User Reviews API Documentation

## Overview
The User Reviews API allows users to create, read, update, and delete reviews for menu items. Reviews consist of a rating (1-5 stars) and a comment. Users can only review each menu item once and can only modify their own reviews.

## Base URL
```
/PerpexBistro/api/reviews/
```

## Authentication
- **Read Operations** (List, Retrieve): Public access - no authentication required
- **Write Operations** (Create, Update, Delete): Authentication required
- Users can only update/delete their own reviews

## Endpoints

### 1. List All Reviews
Retrieve a list of all reviews with optional filtering.

**Endpoint:** `GET /PerpexBistro/api/reviews/`

**Authentication:** Not required (public access)

**Query Parameters:**
- `menu_item` (optional): Filter by menu item ID
- `rating` (optional): Filter by rating (1-5)
- `user` (optional): Filter by user ID

**Example Requests:**
```bash
# Get all reviews
GET /PerpexBistro/api/reviews/

# Get reviews for a specific menu item
GET /PerpexBistro/api/reviews/?menu_item=5

# Get all 5-star reviews
GET /PerpexBistro/api/reviews/?rating=5

# Get reviews by a specific user
GET /PerpexBistro/api/reviews/?user=3
```

**Response (200 OK):**
```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 2,
      "user": 2,
      "user_username": "johndoe",
      "menu_item": 5,
      "menu_item_name": "Margherita Pizza",
      "rating": 5,
      "comment": "Absolutely delicious! Best pizza in town.",
      "review_date": "2025-10-14T15:30:00Z"
    },
    {
      "id": 1,
      "user": 1,
      "user_username": "janedoe",
      "menu_item": 3,
      "menu_item_name": "Classic Burger",
      "rating": 4,
      "comment": "Great burger but a bit pricey for the portion size.",
      "review_date": "2025-10-13T12:15:00Z"
    }
  ]
}
```

---

### 2. Retrieve Single Review
Get details of a specific review.

**Endpoint:** `GET /PerpexBistro/api/reviews/{id}/`

**Authentication:** Not required (public access)

**Example Request:**
```bash
GET /PerpexBistro/api/reviews/1/
```

**Response (200 OK):**
```json
{
  "id": 1,
  "user": 1,
  "user_username": "janedoe",
  "menu_item": 3,
  "menu_item_name": "Classic Burger",
  "rating": 4,
  "comment": "Great burger but a bit pricey for the portion size.",
  "review_date": "2025-10-13T12:15:00Z"
}
```

**Error Response (404 Not Found):**
```json
{
  "detail": "Not found."
}
```

---

### 3. Create New Review
Create a new review for a menu item.

**Endpoint:** `POST /PerpexBistro/api/reviews/`

**Authentication:** Required

**Request Headers:**
```
Authorization: Token your_auth_token_here
Content-Type: application/json
```

**Request Body:**
```json
{
  "menu_item": 5,
  "rating": 5,
  "comment": "Absolutely delicious! Best pizza I've ever had."
}
```

**Field Validations:**
- `menu_item` (required): Must be a valid, available menu item ID
- `rating` (required): Integer between 1 and 5
- `comment` (required): String with minimum 10 characters

**Example Request:**
```bash
curl -X POST /PerpexBistro/api/reviews/ \
  -H "Authorization: Token your_token" \
  -H "Content-Type: application/json" \
  -d '{
    "menu_item": 5,
    "rating": 5,
    "comment": "Absolutely delicious! Best pizza in town."
  }'
```

**Success Response (201 Created):**
```json
{
  "id": 3,
  "user": 2,
  "user_username": "johndoe",
  "menu_item": 5,
  "menu_item_name": "Margherita Pizza",
  "rating": 5,
  "comment": "Absolutely delicious! Best pizza in town.",
  "review_date": "2025-10-14T16:00:00Z"
}
```

**Error Responses:**

**401 Unauthorized:**
```json
{
  "detail": "Authentication credentials were not provided."
}
```

**400 Bad Request (Duplicate Review):**
```json
{
  "non_field_errors": [
    "You have already reviewed this menu item. Please update your existing review instead."
  ]
}
```

**400 Bad Request (Invalid Rating):**
```json
{
  "rating": ["Rating must be between 1 and 5"]
}
```

**400 Bad Request (Comment Too Short):**
```json
{
  "comment": ["Comment must be at least 10 characters long"]
}
```

**400 Bad Request (Unavailable Menu Item):**
```json
{
  "menu_item": ["Cannot review an unavailable menu item"]
}
```

---

### 4. Update Review (Full Update)
Update all fields of an existing review.

**Endpoint:** `PUT /PerpexBistro/api/reviews/{id}/`

**Authentication:** Required (must be review owner)

**Request Headers:**
```
Authorization: Token your_auth_token_here
Content-Type: application/json
```

**Request Body:**
```json
{
  "menu_item": 5,
  "rating": 4,
  "comment": "Updated review: Still great but service was slow today."
}
```

**Example Request:**
```bash
curl -X PUT /PerpexBistro/api/reviews/3/ \
  -H "Authorization: Token your_token" \
  -H "Content-Type: application/json" \
  -d '{
    "menu_item": 5,
    "rating": 4,
    "comment": "Updated review: Still great but service was slow."
  }'
```

**Success Response (200 OK):**
```json
{
  "id": 3,
  "user": 2,
  "user_username": "johndoe",
  "menu_item": 5,
  "menu_item_name": "Margherita Pizza",
  "rating": 4,
  "comment": "Updated review: Still great but service was slow.",
  "review_date": "2025-10-14T16:00:00Z"
}
```

**Error Response (403 Forbidden):**
```json
{
  "detail": "You can only update your own reviews."
}
```

---

### 5. Update Review (Partial Update)
Update specific fields of an existing review.

**Endpoint:** `PATCH /PerpexBistro/api/reviews/{id}/`

**Authentication:** Required (must be review owner)

**Request Headers:**
```
Authorization: Token your_auth_token_here
Content-Type: application/json
```

**Request Body (Update only rating):**
```json
{
  "rating": 5
}
```

**Request Body (Update only comment):**
```json
{
  "comment": "Changed my mind - it was excellent after all!"
}
```

**Example Request:**
```bash
curl -X PATCH /PerpexBistro/api/reviews/3/ \
  -H "Authorization: Token your_token" \
  -H "Content-Type: application/json" \
  -d '{"rating": 5}'
```

**Success Response (200 OK):**
```json
{
  "id": 3,
  "user": 2,
  "user_username": "johndoe",
  "menu_item": 5,
  "menu_item_name": "Margherita Pizza",
  "rating": 5,
  "comment": "Updated review: Still great but service was slow.",
  "review_date": "2025-10-14T16:00:00Z"
}
```

---

### 6. Delete Review
Delete an existing review.

**Endpoint:** `DELETE /PerpexBistro/api/reviews/{id}/`

**Authentication:** Required (must be review owner)

**Request Headers:**
```
Authorization: Token your_auth_token_here
```

**Example Request:**
```bash
curl -X DELETE /PerpexBistro/api/reviews/3/ \
  -H "Authorization: Token your_token"
```

**Success Response (204 No Content):**
```
(Empty response body)
```

**Error Response (403 Forbidden):**
```json
{
  "detail": "You can only delete your own reviews."
}
```

---

### 7. Get My Reviews
Retrieve all reviews created by the authenticated user.

**Endpoint:** `GET /PerpexBistro/api/reviews/my_reviews/`

**Authentication:** Required

**Request Headers:**
```
Authorization: Token your_auth_token_here
```

**Example Request:**
```bash
curl -X GET /PerpexBistro/api/reviews/my_reviews/ \
  -H "Authorization: Token your_token"
```

**Success Response (200 OK):**
```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 5,
      "user": 2,
      "user_username": "johndoe",
      "menu_item": 8,
      "menu_item_name": "Caesar Salad",
      "rating": 4,
      "comment": "Fresh and crispy, great dressing.",
      "review_date": "2025-10-14T17:00:00Z"
    },
    {
      "id": 3,
      "user": 2,
      "user_username": "johndoe",
      "menu_item": 5,
      "menu_item_name": "Margherita Pizza",
      "rating": 5,
      "comment": "Absolutely delicious! Best pizza in town.",
      "review_date": "2025-10-14T16:00:00Z"
    }
  ]
}
```

---

## Validation Rules

### Rating
- **Type:** Integer
- **Range:** 1 to 5 (inclusive)
- **Required:** Yes
- **Validation:** Field-level validator, database constraint, and serializer validation

### Comment
- **Type:** String (TextField)
- **Min Length:** 10 characters (trimmed)
- **Required:** Yes
- **Validation:** Cannot be empty or only whitespace

### Menu Item
- **Type:** Foreign Key to MenuItem
- **Required:** Yes
- **Validation:** Must exist and be available (`is_available=True`)

### Duplicate Prevention
- Users can only review each menu item once
- Enforced by database-level `UniqueConstraint` on `(user, menu_item)`
- Attempting to create a duplicate returns 400 Bad Request

---

## Permissions

### Public Access (No Authentication)
- `GET /api/reviews/` - List all reviews
- `GET /api/reviews/{id}/` - Retrieve single review

### Authenticated Access
- `POST /api/reviews/` - Create new review
- `GET /api/reviews/my_reviews/` - Get user's own reviews

### Owner-Only Access
- `PUT /api/reviews/{id}/` - Update own review (full update)
- `PATCH /api/reviews/{id}/` - Update own review (partial update)
- `DELETE /api/reviews/{id}/` - Delete own review

---

## Use Cases

### 1. Display Reviews for a Menu Item
```bash
# Get all reviews for menu item ID 5
GET /PerpexBistro/api/reviews/?menu_item=5
```

**Frontend Integration:**
```javascript
// Fetch reviews for a menu item
fetch('/PerpexBistro/api/reviews/?menu_item=5')
  .then(response => response.json())
  .then(data => {
    const reviews = data.results;
    const averageRating = reviews.reduce((sum, r) => sum + r.rating, 0) / reviews.length;
    console.log(`Average rating: ${averageRating.toFixed(1)}/5`);
  });
```

### 2. Submit a Review
```bash
# Authenticated user creates a review
POST /PerpexBistro/api/reviews/
Authorization: Token abc123xyz
Content-Type: application/json

{
  "menu_item": 5,
  "rating": 5,
  "comment": "Best pizza I've ever had! Will order again."
}
```

### 3. Calculate Average Rating
```python
# Backend: Calculate average rating for a menu item
from django.db.models import Avg
from home.models import UserReview

menu_item_id = 5
avg_rating = UserReview.objects.filter(menu_item_id=menu_item_id).aggregate(Avg('rating'))
print(f"Average rating: {avg_rating['rating__avg']:.1f}/5")
```

### 4. User Profile - My Reviews
```bash
# Get all reviews by authenticated user
GET /PerpexBistro/api/reviews/my_reviews/
Authorization: Token abc123xyz
```

### 5. Filter High-Rated Items
```bash
# Get all 5-star reviews to find popular items
GET /PerpexBistro/api/reviews/?rating=5
```

---

## Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | Integer | Unique review identifier |
| `user` | Integer | User ID of review author |
| `user_username` | String | Username of review author (read-only) |
| `menu_item` | Integer | Menu item ID being reviewed |
| `menu_item_name` | String | Menu item name (read-only) |
| `rating` | Integer | Star rating (1-5) |
| `comment` | String | Review text/comment |
| `review_date` | DateTime | When review was created (auto-generated) |

---

## Error Handling

### Common Error Codes

| Status Code | Meaning | Common Causes |
|-------------|---------|---------------|
| 400 Bad Request | Validation error | Invalid rating, short comment, duplicate review |
| 401 Unauthorized | Authentication required | Missing/invalid token |
| 403 Forbidden | Permission denied | Trying to modify another user's review |
| 404 Not Found | Resource not found | Invalid review ID or menu item ID |

### Error Response Format
```json
{
  "field_name": ["Error message"]
}
```

Or for non-field errors:
```json
{
  "non_field_errors": ["Error message"]
}
```

Or for detail errors:
```json
{
  "detail": "Error message"
}
```

---

## Best Practices

1. **Always authenticate write operations**: Use token authentication for creating/updating reviews
2. **Validate on client side**: Check rating range (1-5) and comment length (10+ chars) before submitting
3. **Handle duplicates gracefully**: If user tries to review twice, direct them to update existing review
4. **Calculate aggregate ratings**: Use Django's `Avg()` aggregation for menu item ratings
5. **Implement pagination**: For menu items with many reviews, implement pagination on frontend
6. **Show helpful error messages**: Display validation errors clearly to users
7. **Rate limiting**: Consider implementing rate limiting to prevent review spam

---

## Testing with curl

### Create Review
```bash
curl -X POST http://localhost:8000/PerpexBistro/api/reviews/ \
  -H "Authorization: Token your_token_here" \
  -H "Content-Type: application/json" \
  -d '{
    "menu_item": 1,
    "rating": 5,
    "comment": "Excellent food and great service!"
  }'
```

### Get Reviews for Menu Item
```bash
curl -X GET "http://localhost:8000/PerpexBistro/api/reviews/?menu_item=1"
```

### Update Review
```bash
curl -X PATCH http://localhost:8000/PerpexBistro/api/reviews/1/ \
  -H "Authorization: Token your_token_here" \
  -H "Content-Type: application/json" \
  -d '{"rating": 4, "comment": "Updated: Still good but a bit pricey"}'
```

### Delete Review
```bash
curl -X DELETE http://localhost:8000/PerpexBistro/api/reviews/1/ \
  -H "Authorization: Token your_token_here"
```

---

## Integration Examples

### React Component
```javascript
// ReviewForm.js
const ReviewForm = ({ menuItemId, onSuccess }) => {
  const [rating, setRating] = useState(5);
  const [comment, setComment] = useState('');
  const [error, setError] = useState(null);

  const submitReview = async (e) => {
    e.preventDefault();
    
    try {
      const response = await fetch('/PerpexBistro/api/reviews/', {
        method: 'POST',
        headers: {
          'Authorization': `Token ${localStorage.getItem('authToken')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          menu_item: menuItemId,
          rating: rating,
          comment: comment
        })
      });
      
      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.non_field_errors?.[0] || 'Failed to submit review');
      }
      
      onSuccess();
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <form onSubmit={submitReview}>
      <StarRating value={rating} onChange={setRating} />
      <textarea
        value={comment}
        onChange={(e) => setComment(e.target.value)}
        minLength={10}
        required
      />
      {error && <p className="error">{error}</p>}
      <button type="submit">Submit Review</button>
    </form>
  );
};
```

---

## Notes

- Reviews are ordered by most recent first (`-review_date`)
- The `user` field is automatically set from the authenticated user (cannot be manually set)
- The `review_date` is automatically generated on creation (cannot be manually set)
- Related objects (`user`, `menu_item`) are fetched efficiently using `select_related()`
- All write operations include logging for audit purposes
