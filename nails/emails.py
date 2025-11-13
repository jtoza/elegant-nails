from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings

def send_appointment_confirmation(appointment):
    """Send confirmation email to client"""
    subject = f"✅ Appointment Confirmed - {appointment.service.name} - Elegant Nails"
    
    html_message = render_to_string('nails/emails/appointment_confirmation.html', {
        'appointment': appointment
    })
    
    plain_message = f"""
    Appointment Confirmation - Elegant Nails
    
    Hello {appointment.client_name},
    
    Your appointment has been confirmed!
    
    Service: {appointment.service.name}
    Date: {appointment.appointment_date}
    Time: {appointment.appointment_time}
    Duration: {appointment.duration} minutes
    Price: ${appointment.service.price}
    
    Please arrive 5-10 minutes before your appointment.
    
    We look forward to seeing you!
    
    The Elegant Nails Team
    """
    
    try:
        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [appointment.client_email],
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Error sending confirmation email: {e}")
        return False

def send_admin_notification(appointment):
    """Send notification email to admin about new booking"""
    subject = f"📋 New Booking: {appointment.client_name} - {appointment.appointment_date}"
    
    html_message = render_to_string('nails/emails/admin_notification.html', {
        'appointment': appointment
    })
    
    plain_message = f"""
    New Appointment Booking
    
    Client: {appointment.client_name}
    Email: {appointment.client_email}
    Phone: {appointment.client_phone}
    
    Service: {appointment.service.name}
    Date: {appointment.appointment_date}
    Time: {appointment.appointment_time}
    
    Special Requests: {appointment.special_requests or 'None'}
    """
    
    try:
        # Send to your brother's email - replace with his actual email
        admin_email = 'jnlearner22@gmail.com@email.com'  # CHANGE THIS!
        
        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [admin_email],
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Error sending admin notification: {e}")
        return False