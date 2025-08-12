from django.contrib import admin
from .models import *

# Register your models here.

class ItemAdmin(admin.ModelAdmin):
    save_as = True  # Enables "Save as new" button in admin detail view

    list_display = (
        'title', 'category', 'price', 'is_active',
        'is_featured', 'is_available', 'location', 'owner',
    )
    list_filter = (
        'category', 'condition', 'is_active', 'is_featured', 'is_available',
        'created_at', 'location'
    )
    search_fields = (
        'title', 'description', 'tags', 'location', 'owner__email'
    )
    readonly_fields = ('created_at', 'updated_at', 'view_count', 'rating', 'review_count')

    # Group fields into logical sections
    fieldsets = (
        ('Basic Info', {
            'fields': ('title', 'description', 'category', 'condition', 'tags')
        }),
        ('Pricing & Availability', {
            'fields': ('price', 'min_rental_days', 'max_rental_days', 'is_available')
        }),
        ('Media', {
            'fields': ('image','images')
        }),
        ('Location Info', {
            'fields': ('location', 'latitude', 'longitude')
        }),
        ('Ownership & Status', {
            'fields': ('owner', 'is_active', 'is_featured')
        }),
        ('Ratings & Meta', {
            'fields': ('rating', 'review_count', 'view_count', 'created_at', 'updated_at')
        }),
    )

    actions = ['duplicate_items']

    def duplicate_items(self, request, queryset):
        for item in queryset:
            item.pk = None
            item.save()
        self.message_user(request, f"Successfully duplicated {queryset.count()} item(s).")
    duplicate_items.short_description = "Duplicate selected items"

# admin.site.register(category)
admin.site.register(Image)
admin.site.register(Item,ItemAdmin)
admin.site.register(Order)
admin.site.register(Review)
admin.site.register(category)
# admin.site.register(test)