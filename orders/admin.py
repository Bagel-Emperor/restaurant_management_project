from django.contrib import admin
from django.contrib import messages
from .models import Customer, Order, OrderStatus, LoyaltyProgram
from .choices import OrderStatusChoices


def mark_orders_processed(modeladmin, request, queryset):
    """
    Custom admin action to mark selected orders as 'Processed' (Processing status).
    
    This action allows administrators to bulk update multiple orders to the 
    'Processing' status in one operation, streamlining order management workflows.
    
    Args:
        modeladmin: The ModelAdmin instance
        request: The current HttpRequest object
        queryset: QuerySet of selected Order objects to update
    
    Returns:
        None - Updates are applied directly and success message is displayed
    """
    # Get or create the Processing status
    processing_status, created = OrderStatus.objects.get_or_create(
        name=OrderStatusChoices.PROCESSING
    )
    
    # Update only orders that aren't already in Processing status
    # The update() method returns the number of rows affected
    updated_count = queryset.exclude(status=processing_status).update(status=processing_status)
    
    # Provide feedback to the admin user
    if updated_count == 0:
        modeladmin.message_user(
            request,
            "All selected orders were already in 'Processing' status.",
            level=messages.WARNING
        )
    elif updated_count == 1:
        modeladmin.message_user(
            request,
            "1 order was successfully marked as 'Processing'.",
            level=messages.SUCCESS
        )
    else:
        modeladmin.message_user(
            request,
            f"{updated_count} orders were successfully marked as 'Processing'.",
            level=messages.SUCCESS
        )


# Set a user-friendly display name for the action
mark_orders_processed.short_description = "Mark selected orders as Processed"


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """
    Enhanced Django admin configuration for the Order model.
    
    Provides a comprehensive admin interface with custom actions, filtering,
    searching, and display options for efficient order management.
    """
    
    # Register the custom action
    actions = [mark_orders_processed]
    
    # Display these fields in the list view
    list_display = [
        'order_id',
        'customer',
        'user',
        'status',
        'total_amount',
        'created_at',
        'updated_at'
    ]
    
    # Add filters for easy data segmentation
    list_filter = [
        'status',
        'created_at',
        'updated_at'
    ]
    
    # Enable search functionality
    search_fields = [
        'order_id',
        'customer__name',
        'customer__email',
        'user__username',
        'user__email'
    ]
    
    # Set default ordering (most recent first)
    ordering = ['-created_at']
    
    # Make certain fields read-only
    readonly_fields = [
        'order_id',
        'created_at',
        'updated_at'
    ]
    
    # Optimize database queries
    list_select_related = ['customer', 'user', 'status']
    
    # Number of items per page
    list_per_page = 25


@admin.register(LoyaltyProgram)
class LoyaltyProgramAdmin(admin.ModelAdmin):
    """
    Django admin configuration for the LoyaltyProgram model.
    
    Provides an organized admin interface for managing customer loyalty
    program tiers with filtering, searching, and display options.
    """
    
    # Display these fields in the list view
    list_display = [
        'name',
        'points_required',
        'discount_percentage',
        'created_at',
        'updated_at'
    ]
    
    # Add filters for easy data segmentation
    list_filter = [
        'created_at',
        'updated_at'
    ]
    
    # Enable search functionality
    search_fields = [
        'name',
        'description'
    ]
    
    # Set default ordering (by points required)
    ordering = ['points_required']
    
    # Make certain fields read-only
    readonly_fields = [
        'created_at',
        'updated_at'
    ]
    
    # Fieldsets for organized form display
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description')
        }),
        ('Requirements & Benefits', {
            'fields': ('points_required', 'discount_percentage')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


# Register Customer with basic admin
admin.site.register(Customer)
