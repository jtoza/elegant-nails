from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from datetime import datetime, date, time, timedelta
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from .models import Service, PortfolioItem, Appointment, WorkingHours
from .forms import AppointmentForm
from .emails import send_appointment_confirmation, send_admin_notification
from django.utils import timezone
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
def home(request):
    # Show featured portfolio items on the homepage
    featured_nails = PortfolioItem.objects.filter(featured=True)[:6]  # Show 6 featured items
    services = Service.objects.filter(is_active=True)
    return render(request, 'nails/home.html', {'featured_nails': featured_nails, 'services': services})

def services(request):
    service_list = Service.objects.filter(is_active=True)
    return render(request, 'nails/services.html', {'services': service_list})

def portfolio(request):
    portfolio_items = PortfolioItem.objects.all()
    return render(request, 'nails/portfolio.html', {'portfolio_items': portfolio_items})

def book_appointment(request):
    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            # Calculate duration from the selected service
            service = form.cleaned_data['service']
            appointment = form.save(commit=False)
            appointment.duration = service.duration
            
            # Check for overlapping appointments - FIXED QUERY
            appointment_end_time = calculate_end_time(appointment.appointment_time, service.duration)
            
            # Simplified overlapping check
            overlapping = Appointment.objects.filter(
                appointment_date=appointment.appointment_date,
                status__in=['PENDING', 'CONFIRMED']
            ).filter(
                Q(appointment_time__lt=appointment_end_time) &
                Q(appointment_time__gte=appointment.appointment_time)
            )
            
            if overlapping.exists():
                messages.error(request, "Sorry, this time slot is no longer available. Please choose a different time.")
            else:
                appointment.save()
                
                # SEND EMAILS
                try:
                    # Send confirmation to client
                    send_appointment_confirmation(appointment)
                    
                    # Send notification to admin
                    send_admin_notification(appointment)
                    
                    messages.success(request, "Your appointment has been booked successfully! A confirmation email has been sent to you.")
                except Exception as e:
                    # If email fails, still show success but with a note
                    messages.success(request, "Your appointment has been booked! (There was an issue sending the confirmation email, but your booking is confirmed.)")
                    print(f"Email error: {e}")
                
                return redirect('home')
    else:
        form = AppointmentForm()
    
    return render(request, 'nails/book_appointment.html', {'form': form})

def calculate_end_time(start_time, duration_minutes):
    """Calculate end time given start time and duration in minutes"""
    start_datetime = datetime.combine(date.today(), start_time)
    end_datetime = start_datetime + timedelta(minutes=duration_minutes)
    return end_datetime.time()

def get_available_times(request):
    """API endpoint to get available times for a selected date"""
    selected_date = request.GET.get('date')
    service_id = request.GET.get('service_id')
    
    if not selected_date or not service_id:
        return JsonResponse({'error': 'Missing parameters'}, status=400)
    
    try:
        selected_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
        service = Service.objects.get(id=service_id)
        
        # Get working hours for that day of week
        day_of_week = selected_date.weekday()
        working_hours = WorkingHours.objects.filter(day_of_week=day_of_week, is_working=True).first()
        
        if not working_hours:
            return JsonResponse({'available_times': []})
        
        # Get booked appointments for that date
        booked_appointments = Appointment.objects.filter(
            appointment_date=selected_date,
            status__in=['PENDING', 'CONFIRMED']
        )
        
        # Generate available time slots (every 30 minutes)
        available_times = []
        current_time = working_hours.start_time
        
        while current_time < working_hours.end_time:
            # Check if this time slot is available
            slot_end = calculate_end_time(current_time, service.duration)
            
            # Check if this slot overlaps with any existing appointment
            is_available = True
            for appointment in booked_appointments:
                appointment_end = calculate_end_time(appointment.appointment_time, appointment.duration)
                
                # Check for time overlap
                if (current_time < appointment_end and slot_end > appointment.appointment_time):
                    is_available = False
                    break
            
            if is_available and slot_end <= working_hours.end_time:
                available_times.append(current_time.strftime('%H:%M'))
            
            # Move to next slot (30-minute increments)
            current_time_dt = datetime.combine(date.today(), current_time) + timedelta(minutes=30)
            current_time = current_time_dt.time()
        
        return JsonResponse({'available_times': available_times})
    
    except Service.DoesNotExist:
        return JsonResponse({'error': 'Service not found'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

# DASHBOARD VIEWS
@login_required
def dashboard(request):
    """Main dashboard for the business owner"""
    today = timezone.now().date()
    tomorrow = today + timedelta(days=1)
    
    # Get today's appointments
    todays_appointments = Appointment.objects.filter(
        appointment_date=today,
        status__in=['PENDING', 'CONFIRMED']
    ).order_by('appointment_time')
    
    # Get tomorrow's appointments
    tomorrows_appointments = Appointment.objects.filter(
        appointment_date=tomorrow,
        status__in=['PENDING', 'CONFIRMED']
    ).order_by('appointment_time')
    
    # Get statistics
    total_appointments = Appointment.objects.count()
    pending_appointments = Appointment.objects.filter(status='PENDING').count()
    confirmed_appointments = Appointment.objects.filter(status='CONFIRMED').count()
    completed_appointments = Appointment.objects.filter(status='COMPLETED').count()
    
    # Recent appointments (last 7 days)
    recent_appointments = Appointment.objects.filter(
        created_at__gte=today - timedelta(days=7)
    ).order_by('-created_at')[:10]
    
    context = {
        'todays_appointments': todays_appointments,
        'tomorrows_appointments': tomorrows_appointments,
        'total_appointments': total_appointments,
        'pending_appointments': pending_appointments,
        'confirmed_appointments': confirmed_appointments,
        'completed_appointments': completed_appointments,
        'recent_appointments': recent_appointments,
        'today': today,
        'tomorrow': tomorrow,
    }
    
    return render(request, 'nails/dashboard.html', context)

@login_required
def appointment_list(request):
    """View all appointments with filtering and search"""
    appointments = Appointment.objects.all().order_by('-appointment_date', '-appointment_time')
    
    # Get filter parameters
    status_filter = request.GET.get('status', '')
    date_filter = request.GET.get('date', '')
    search_query = request.GET.get('search', '')
    
    # Apply filters
    if status_filter:
        appointments = appointments.filter(status=status_filter)
    
    if date_filter:
        appointments = appointments.filter(appointment_date=date_filter)
    
    if search_query:
        appointments = appointments.filter(
            Q(client_name__icontains=search_query) |
            Q(client_email__icontains=search_query) |
            Q(client_phone__icontains=search_query) |
            Q(service__name__icontains=search_query)
        )
    
    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(appointments, 10)  # Show 10 appointments per page
    
    try:
        appointments_page = paginator.page(page)
    except PageNotAnInteger:
        appointments_page = paginator.page(1)
    except EmptyPage:
        appointments_page = paginator.page(paginator.num_pages)
    
    context = {
        'appointments': appointments_page,
        'status_choices': Appointment.STATUS_CHOICES,
        'status_filter': status_filter,
        'date_filter': date_filter,
        'search_query': search_query,
    }
    return render(request, 'nails/appointment_list.html', context)

@login_required
def appointment_detail(request, appointment_id):
    """View detailed information about a specific appointment"""
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Appointment.STATUS_CHOICES):
            appointment.status = new_status
            appointment.save()
            messages.success(request, f"Appointment status updated to {appointment.get_status_display()}.")
            return redirect('appointment_detail', appointment_id=appointment.id)
    
    context = {
        'appointment': appointment,
    }
    return render(request, 'nails/appointment_detail.html', context)

@login_required
def update_appointment_status(request, appointment_id):
    """Update appointment status via form submission"""
    if request.method == 'POST':
        appointment = get_object_or_404(Appointment, id=appointment_id)
        new_status = request.POST.get('status')
        
        if new_status in dict(Appointment.STATUS_CHOICES):
            appointment.status = new_status
            appointment.save()
            messages.success(request, f"Appointment status updated to {appointment.get_status_display()}.")
    
    # Redirect back to the previous page or dashboard
    referer = request.META.get('HTTP_REFERER', '/dashboard/')
    return redirect(referer)

@login_required
def client_list(request):
    """View all clients"""
    # Get unique clients from appointments
    clients_data = Appointment.objects.values(
        'client_name', 'client_email', 'client_phone'
    ).distinct()
    
    # Simple pagination without Paginator class
    clients_list = list(clients_data)
    
    context = {
        'clients': clients_list
    }
    return render(request, 'nails/client_list.html', context)

@login_required
def analytics(request):
    """Business analytics dashboard"""
    from django.db.models import Count, Sum
    
    # Basic stats
    total_appointments = Appointment.objects.count()
    total_revenue = Appointment.objects.aggregate(
        total=Sum('service__price')
    )['total'] or 0
    
    # Appointments by status
    status_stats = Appointment.objects.values('status').annotate(
        count=Count('id')
    )
    
    # Revenue by service
    service_stats = Appointment.objects.values(
        'service__name'
    ).annotate(
        count=Count('id'),
        revenue=Sum('service__price')
    )
    
    # Recent activity (last 30 days)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    recent_appointments = Appointment.objects.filter(
        created_at__gte=thirty_days_ago
    ).count()
    
    context = {
        'total_appointments': total_appointments,
        'total_revenue': total_revenue,
        'status_stats': status_stats,
        'service_stats': service_stats,
        'recent_appointments': recent_appointments,
    }
    return render(request, 'nails/analytics.html', context)

@login_required
def client_list(request):
    """View all clients with search functionality"""
    clients_data = Appointment.objects.values(
        'client_name', 'client_email', 'client_phone'
    ).distinct()
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        clients_data = clients_data.filter(
            Q(client_name__icontains=search_query) |
            Q(client_email__icontains=search_query) |
            Q(client_phone__icontains=search_query)
        )
    
    clients_list = list(clients_data)
    
    context = {
        'clients': clients_list,
        'search_query': search_query,
    }
    return render(request, 'nails/client_list.html', context)



def login_view(request):
    """Simple login view"""
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {username}!")
                return redirect('dashboard')
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
    
    return render(request, 'nails/login.html', {'form': form})

def logout_view(request):
    """Simple logout view"""
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('home')