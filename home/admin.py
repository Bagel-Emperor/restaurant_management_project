from django.contrib import admin
from .models import Restaurant, MenuItem, Feedback, Table, UserReview


class UserReviewAdmin(admin.ModelAdmin):
	"""Admin configuration for UserReview model"""
	list_display = ['user', 'menu_item', 'rating', 'review_date']
	list_filter = ['user', 'menu_item', 'rating', 'review_date']
	search_fields = ['comment', 'user__username', 'menu_item__name']
	readonly_fields = ['review_date']
	ordering = ['-review_date']


admin.site.register(Restaurant)
admin.site.register(MenuItem)
admin.site.register(Feedback)
admin.site.register(Table)
admin.site.register(UserReview, UserReviewAdmin)
