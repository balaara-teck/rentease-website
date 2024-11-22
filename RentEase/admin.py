from django.contrib import admin
from .models import Property, PropertyImage, PropertyAmenity, Booking


class PropertyImageInline(admin.TabularInline):
    model = PropertyImage
    extra = 1

class PropertyAmenityInline(admin.TabularInline):
    model = PropertyAmenity
    extra = 1

@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'property_type', 'price', 'city', 'is_available')
    list_filter = ('property_type', 'is_available', 'city')
    search_fields = ('title', 'description', 'address', 'city')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [PropertyImageInline, PropertyAmenityInline]

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('property', 'tenant', 'start_date', 'end_date', 'status')
    list_filter = ('status', 'start_date')
    search_fields = ('property__title', 'tenant__username')
