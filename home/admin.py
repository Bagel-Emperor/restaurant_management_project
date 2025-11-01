from django.contrib import admin
from .models import Restaurant, MenuItem, Feedback, Table, UserReview, DailySpecial


class RestaurantAdmin(admin.ModelAdmin):
    """
    Admin configuration for Restaurant model.
    
    Provides an enhanced admin interface with:
    - List display of key restaurant information
    - Search functionality by name and owner
    - Read-only fields for system-managed data
    - Ordering by restaurant name
    """
    list_display = ('name', 'owner_name', 'phone_number', 'email', 'created_at')
    search_fields = ('name', 'owner_name', 'email')
    readonly_fields = ('created_at',)
    ordering = ('name',)
    
    # Optional: Group fields in the edit form
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'owner_name')
        }),
        ('Contact Details', {
            'fields': ('email', 'phone_number')
        }),
        ('Operating Hours', {
            'fields': ('opening_hours',),
            'description': 'Store opening hours as JSON (e.g., {"Monday": "9am-5pm"})'
        }),
        ('System Information', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


class UserReviewAdmin(admin.ModelAdmin):
	"""Admin configuration for UserReview model"""
	list_display = ('user', 'menu_item', 'rating', 'review_date')
	list_filter = ('user', 'menu_item', 'rating', 'review_date')
	search_fields = ('comment', 'user__username', 'menu_item__name')
	readonly_fields = ('review_date',)
	ordering = ('-review_date',)


class DailySpecialAdmin(admin.ModelAdmin):
	"""
	Admin configuration for DailySpecial model.
	
	Provides an enhanced admin interface with:
	- List display of key special information
	- Filtering by date and menu item
	- Search functionality
	- Read-only system fields
	- Date-based ordering (most recent first)
	"""
	list_display = ('menu_item', 'special_date', 'is_upcoming', 'created_at')
	list_filter = ('special_date', 'menu_item__restaurant', 'menu_item__category')
	search_fields = ('menu_item__name', 'description')
	readonly_fields = ('created_at', 'updated_at')
	ordering = ('-special_date',)
	date_hierarchy = 'special_date'
	
	fieldsets = (
		('Special Information', {
			'fields': ('menu_item', 'special_date', 'description')
		}),
		('System Information', {
			'fields': ('created_at', 'updated_at'),
			'classes': ('collapse',)
		}),
	)
	
	def is_upcoming(self, obj):
		"""Display whether the special is upcoming in the list view."""
		return obj.is_upcoming()
	is_upcoming.boolean = True
	is_upcoming.short_description = 'Is Upcoming?'


admin.site.register(Restaurant, RestaurantAdmin)
admin.site.register(MenuItem)
admin.site.register(Feedback)
admin.site.register(Table)
admin.site.register(UserReview, UserReviewAdmin)
admin.site.register(DailySpecial, DailySpecialAdmin)