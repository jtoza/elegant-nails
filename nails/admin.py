from django.contrib import admin
from django.utils.html import format_html
from .models import Service, PortfolioItem, Appointment, WorkingHours

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'duration', 'is_active')
    list_editable = ('price', 'duration', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')

@admin.register(PortfolioItem)
class PortfolioItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'nail_shape', 'featured')
    list_filter = ('nail_shape', 'featured')
    search_fields = ('title', 'tags')
    list_editable = ('featured',)

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('client_name', 'service', 'appointment_date', 'appointment_time', 'status', 'quick_actions')
    list_filter = ('status', 'appointment_date', 'service')
    search_fields = ('client_name', 'client_email', 'client_phone')
    list_editable = ('status',)
    date_hierarchy = 'appointment_date'
    
    def quick_actions(self, obj):
        return format_html(
            '<a href="/admin/nails/appointment/{}/change/">✏️ Edit</a>',
            obj.id
        )
    quick_actions.short_description = 'Actions'

@admin.register(WorkingHours)
class WorkingHoursAdmin(admin.ModelAdmin):
    list_display = ('day_of_week', 'start_time', 'end_time', 'is_working')
    list_editable = ('is_working',)
    list_filter = ('is_working',)
    ordering = ('day_of_week',)