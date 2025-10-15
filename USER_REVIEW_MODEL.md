# User Review Model Documentation

## Overview
The `UserReview` model allows users to rate and review menu items in the restaurant management system. Each review includes a rating (1-5 stars) and a comment.

## Model Structure

### Fields

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `user` | ForeignKey | Reference to the User who wrote the review | Required, CASCADE delete |
| `menu_item` | ForeignKey | Reference to the MenuItem being reviewed | Required, CASCADE delete |
| `rating` | IntegerField | Star rating from 1 to 5 | Required, 1-5 range |
| `comment` | TextField | Review text/feedback | Required |
| `review_date` | DateTimeField | When the review was created | Auto-generated |

### Key Features

- **Unique Constraint**: Each user can only review a menu item once (prevents duplicate reviews)
- **Rating Validation**: Ratings must be between 1 and 5 stars
- **Cascade Deletion**: Reviews are deleted when the associated user or menu item is deleted
- **Automatic Timestamps**: `review_date` is automatically set when a review is created
- **Ordering**: Reviews are ordered by most recent first (descending `review_date`)

### Related Names

- `user.reviews.all()` - Access all reviews by a specific user
- `menu_item.reviews.all()` - Access all reviews for a specific menu item

## Usage Examples

### Creating a Review

```python
from home.models import UserReview, MenuItem
from django.contrib.auth.models import User

# Get user and menu item
user = User.objects.get(username='johndoe')
menu_item = MenuItem.objects.get(name='Cheeseburger')

# Create a review
review = UserReview.objects.create(
    user=user,
    menu_item=menu_item,
    rating=5,
    comment='Absolutely delicious! Best burger in town.'
)
```

### Querying Reviews

```python
# Get all reviews for a menu item
burger = MenuItem.objects.get(name='Cheeseburger')
reviews = burger.reviews.all()

# Get all reviews by a user
user = User.objects.get(username='johndoe')
user_reviews = user.reviews.all()

# Get recent reviews (already ordered by default)
recent_reviews = UserReview.objects.all()[:10]

# Get high-rated reviews (4+ stars)
high_rated = UserReview.objects.filter(rating__gte=4)

# Get average rating for a menu item
from django.db.models import Avg
avg_rating = UserReview.objects.filter(menu_item=burger).aggregate(Avg('rating'))
```

### Updating a Review

```python
review = UserReview.objects.get(user=user, menu_item=menu_item)
review.rating = 4
review.comment = 'Updated: Still great, but service was slow today.'
review.save()
```

### Deleting a Review

```python
review = UserReview.objects.get(user=user, menu_item=menu_item)
review.delete()
```

## Validation

### Rating Range Validation
The model includes validation to ensure ratings are between 1 and 5:

```python
review = UserReview(
    user=user,
    menu_item=menu_item,
    rating=6,  # Invalid!
    comment='Too high'
)
review.full_clean()  # Raises ValidationError
```

### Unique User-MenuItem Validation
Users cannot review the same menu item twice:

```python
# First review - OK
UserReview.objects.create(user=user, menu_item=burger, rating=5, comment='Great!')

# Second review for same user/item - Raises IntegrityError
UserReview.objects.create(user=user, menu_item=burger, rating=4, comment='Changed my mind')
```

## Database Indexes

The model includes indexes on commonly queried fields for performance:
- `menu_item` - Fast lookup of all reviews for an item
- `user` - Fast lookup of all reviews by a user
- `rating` - Fast filtering by rating value
- `review_date` (descending) - Fast retrieval of recent reviews

## Admin Panel

The UserReview model is registered in the Django admin panel, allowing administrators to:
- View all reviews
- Create, edit, and delete reviews
- Filter reviews by user, menu item, or rating
- Search reviews by comment text

## String Representation

Reviews display as: `"{username}'s review of {menu_item_name} - {rating}/5"`

Example: `"johndoe's review of Cheeseburger - 5/5"`

## Best Practices

1. **Always validate user input**: Use `full_clean()` before saving to catch validation errors
2. **Handle duplicate reviews**: Check if a review exists before creating a new one
3. **Calculate aggregate ratings**: Use Django's `Avg()` aggregation for menu item ratings
4. **Pagination**: Use pagination when displaying large numbers of reviews
5. **Permissions**: Ensure only authenticated users can create reviews
6. **Moderation**: Consider adding a `is_approved` field for review moderation if needed

## Future Enhancements

Potential additions to the model:
- `helpful_count` - Track how many users found the review helpful
- `is_verified_purchase` - Indicate if the reviewer actually ordered the item
- `images` - Allow users to upload photos with their reviews
- `is_approved` - Add moderation workflow
- `updated_at` - Track when reviews are edited
