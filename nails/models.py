from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import date, datetime

class Service(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=6, decimal_places=2)
    duration = models.PositiveIntegerField(help_text="Duration in minutes")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta:
        app_label = 'nails'  # This explicitly sets the app label

class PortfolioItem(models.Model):
    NAIL_SHAPE_CHOICES = [
        ('OVAL', 'Oval'),
        ('SQUARE', 'Square'),
        ('COFFIN', 'Coffin'),
        ('ALMOND', 'Almond'),
        ('STILETTO', 'Stiletto'),
    ]
    title = models.CharField(max_length=200)
    image = models.ImageField(upload_to='portfolio/')
    description = models.TextField(blank=True)
    nail_shape = models.CharField(max_length=20, choices=NAIL_SHAPE_CHOICES, blank=True)
    tags = models.CharField(max_length=200, help_text="Comma-separated, e.g., floral, summer, french tip")
    featured = models.BooleanField(default=False)

    def __str__(self):
        return self.title

    class Meta:
        app_label = 'nails'

class Appointment(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('CONFIRMED', 'Confirmed'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    client_name = models.CharField(max_length=100)
    client_email = models.EmailField()
    client_phone = models.CharField(max_length=20)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    appointment_date = models.DateField()
    appointment_time = models.TimeField()
    duration = models.PositiveIntegerField(help_text="Duration in minutes")
    special_requests = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-appointment_date', '-appointment_time']
        app_label = 'nails'
    
    def __str__(self):
        return f"{self.client_name} - {self.service.name} - {self.appointment_date}"

class WorkingHours(models.Model):
    DAY_CHOICES = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]
    day_of_week = models.IntegerField(choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_working = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['day_of_week']
        app_label = 'nails'
    
    def __str__(self):
        return f"{self.get_day_of_week_display()}: {self.start_time} - {self.end_time}"