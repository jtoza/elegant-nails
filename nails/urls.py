from django.urls import path
from . import views

urlpatterns = [
    # Public URLs
    path('', views.home, name='home'),
    path('services/', views.services, name='services'),
    path('portfolio/', views.portfolio, name='portfolio'),
    path('book/', views.book_appointment, name='book_appointment'),
    path('get-available-times/', views.get_available_times, name='get_available_times'),
    
    # Authentication URLs
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Dashboard URLs
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/appointments/', views.appointment_list, name='appointment_list'),
    path('dashboard/appointments/<int:appointment_id>/', views.appointment_detail, name='appointment_detail'),
    path('dashboard/appointments/<int:appointment_id>/update-status/', 
         views.update_appointment_status, name='update_appointment_status'),
    path('dashboard/clients/', views.client_list, name='client_list'),
    path('dashboard/analytics/', views.analytics, name='analytics'),
]