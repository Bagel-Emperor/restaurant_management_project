from django.contrib import admin
from .models import Restaurant, MenuItem, Feedback, Table, UserReview


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
	list_display = ['user', 'menu_item', 'rating', 'review_date']
	list_filter = ['user', 'menu_item', 'rating', 'review_date']
	search_fields = ['comment', 'user__username', 'menu_item__name']
	readonly_fields = ['review_date']
	ordering = ['-review_date']


admin.site.register(Restaurant, RestaurantAdmin)
admin.site.register(MenuItem)
admin.site.register(Feedback)
admin.site.register(Table)
admin.site.register(UserReview, UserReviewAdmin)
