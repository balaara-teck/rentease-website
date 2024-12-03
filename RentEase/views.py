from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from .models import Property, PropertyImage, Booking, Profile, Subscription
from .forms import RegisterForm, BookingForm, PropertyEditForm, ProfileForm
from django.contrib.auth import logout, update_session_auth_hash, login, authenticate
from django.contrib.auth.forms import PasswordChangeForm
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import os
from paypal.standard.forms import PayPalPaymentsForm
from paypal.standard.ipn.signals import valid_ipn_received
from django.dispatch import receiver
from django.contrib.auth.models import User
from datetime import date
from dateutil.relativedelta import relativedelta
import requests

def property_list(request):
    query = request.GET.get('q')
    properties = Property.objects.filter(is_available=True)
    
    if query:
        properties = properties.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(city__icontains=query) |
            Q(state__icontains=query)
        )
    
    paginator = Paginator(properties, 9)  # Show 9 properties per page
    page = request.GET.get('page')
    properties = paginator.get_page(page)
    
    return render(request, 'RentEase/property_list.html', {
        'properties': properties,
        'query': query
    })

def property_detail(request, slug):
    property = get_object_or_404(Property, slug=slug)
    booking_form = None
    existing_bookings = None
    
    if request.user.is_authenticated and request.user != property.owner:
        if request.method == 'POST':
            booking_form = BookingForm(request.POST)
            if booking_form.is_valid():
                # Check for booking conflicts
                start_date = booking_form.cleaned_data['start_date']
                end_date = booking_form.cleaned_data['end_date']
                
                conflicting_bookings = Booking.objects.filter(
                    property=property,
                    status='approved',
                    start_date__lte=end_date,
                    end_date__gte=start_date
                )
                
                if conflicting_bookings.exists():
                    messages.error(request, 'This property is already booked for the selected dates.')
                else:
                    booking = booking_form.save(commit=False)
                    booking.property = property
                    booking.tenant = request.user
                    booking.save()
                    
                    messages.success(request, 'Booking request sent successfully! The owner will review your request.')
                    return redirect('rentease:property_detail', slug=slug)
        else:
            booking_form = BookingForm()
            
        # Get existing bookings for the calendar
        existing_bookings = Booking.objects.filter(
            property=property,
            status='approved',
            end_date__gte=date.today()
        ).order_by('start_date')
    
    context = {
        'property': property,
        'booking_form': booking_form,
        'existing_bookings': existing_bookings,
        'google_maps_api_key': settings.GOOGLE_MAPS_API_KEY
    }
    return render(request, 'RentEase/property_detail.html', context)

@login_required
def property_create(request):
    # Check if user has an active subscription
    subscription = Subscription.objects.filter(user=request.user).first()
    user_properties = Property.objects.filter(owner=request.user).count()
    
    # If user has more than one property and no active subscription, redirect to subscribe
    if user_properties >= 1 and (not subscription or not subscription.is_active()):
        messages.warning(request, 'You need a subscription to list more than one property.')
        return redirect('rentease:subscribe')
        
    if request.method == 'POST':
        form = PropertyEditForm(request.POST, request.FILES)
        if form.is_valid():
            property = form.save(commit=False)
            property.owner = request.user
            property.save()
            
            # Handle image uploads
            images = request.FILES.getlist('images')
            for image in images:
                PropertyImage.objects.create(property=property, image=image)
            
            messages.success(request, 'Property listed successfully!')
            return redirect('rentease:property_detail', slug=property.slug)
    else:
        form = PropertyEditForm()

    # Get or create a temporary property for subscription
    temp_property_id = request.session.get('temp_property_id')
    if temp_property_id:
        try:
            property = Property.objects.get(id=temp_property_id, owner=request.user)
        except Property.DoesNotExist:
            property = None
    
    if not temp_property_id or not property:
        # Create a temporary property with minimum required fields
        property = Property.objects.create(
            owner=request.user,
            title="Temporary Property",
            description="Temporary description",
            price=0,  # Minimum price
            property_type="house",  # Default type
            bedrooms=1,
            bathrooms=1,
            area=1,
            address="Temporary address",
            city="Temporary city",
            state="Temporary state",
            zip_code="00000",
            status="available"
        )
        request.session['temp_property_id'] = property.id

    context = {
        'form': form,
        'title': 'List Your Property',
        'property': property,
        'paypal_client_id': settings.PAYPAL_CLIENT_ID,
        'is_temporary': True
    }
    return render(request, 'RentEase/property_form.html', context)

@login_required
def my_properties(request):
    properties = Property.objects.filter(owner=request.user)
    return render(request, 'RentEase/my_properties.html', {
        'properties': properties
    })

@login_required
def my_bookings(request):
    bookings = Booking.objects.filter(tenant=request.user)
    return render(request, 'RentEase/my_bookings.html', {
        'bookings': bookings
    })

@login_required
def cancel_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    
    # Ensure the user owns this booking
    if booking.tenant != request.user:
        messages.error(request, "You don't have permission to cancel this booking.")
        return redirect('rentease:my_bookings')
    
    # Only allow cancellation of pending bookings
    if booking.status != 'pending':
        messages.error(request, "You can only cancel pending booking requests.")
        return redirect('rentease:my_bookings')
    
    # Delete the booking
    booking.delete()
    messages.success(request, "Your booking request has been cancelled.")
    return redirect('rentease:my_bookings')

@login_required
def contact_owner(request, slug):
    property = get_object_or_404(Property, slug=slug)
    
    if request.method == 'POST' and request.user != property.owner:
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        
        if subject and message:
            # Prepare the email content
            email_subject = f"[RentEase] {subject} - Property: {property.title}"
            email_message = f"""
            New message from {request.user.get_full_name() or request.user.username}
            
            Property: {property.title}
            Message:
            {message}
            
            Reply to: {request.user.email}
            """
            
            # Send email to property owner
            try:
                send_mail(
                    email_subject,
                    email_message,
                    settings.DEFAULT_FROM_EMAIL,
                    [property.owner.email],
                    fail_silently=False,
                )
                messages.success(request, 'Your message has been sent to the owner.')
            except Exception as e:
                messages.error(request, 'Failed to send message. Please try again later.')
        else:
            messages.error(request, 'Please provide both subject and message.')
    
    return redirect('rentease:property_detail', slug=slug)

@login_required
def property_delete(request, slug):
    property = get_object_or_404(Property, slug=slug, owner=request.user)
    
    if request.method == 'POST':
        # Delete associated images
        for image in property.images.all():
            if image.image:
                if os.path.isfile(image.image.path):
                    os.remove(image.image.path)
        
        # Delete the video if it exists
        if property.video:
            if os.path.isfile(property.video.path):
                os.remove(property.video.path)
        
        # Delete the property
        property.delete()
        messages.success(request, 'Property deleted successfully!')
        return redirect('rentease:my_properties')
    
    return render(request, 'RentEase/property_confirm_delete.html', {
        'property': property
    })

@login_required
def delete_video(request, slug):
    property = get_object_or_404(Property, slug=slug, owner=request.user)
    
    if property.video:
        if os.path.isfile(property.video.path):
            os.remove(property.video.path)
        property.video = None
        property.save()
        
    return JsonResponse({'status': 'success'})

@login_required
def property_edit(request, slug):
    property = get_object_or_404(Property, slug=slug, owner=request.user)
    
    if request.method == 'POST':
        form = PropertyEditForm(request.POST, request.FILES, instance=property)
        if form.is_valid():
            property = form.save()
            
            # Handle image uploads
            images = request.FILES.getlist('images')
            for image in images:
                PropertyImage.objects.create(property=property, image=image)
            
            messages.success(request, 'Property updated successfully!')
            return redirect('rentease:property_detail', slug=property.slug)
    else:
        form = PropertyEditForm(instance=property)
    
    context = {
        'form': form,
        'title': 'Edit Property',
        'property': property,
        'paypal_client_id': settings.PAYPAL_CLIENT_ID,
        'is_temporary': False
    }
    return render(request, 'RentEase/property_form.html', context)

@login_required
def delete_image(request, image_id):
    image = get_object_or_404(PropertyImage, id=image_id)
    property = image.property
    
    # Ensure the user owns this property
    if property.owner != request.user:
        messages.error(request, "You don't have permission to delete this image.")
        return redirect('rentease:property_edit', slug=property.slug)
    
    # Delete the image file and record
    if image.image:
        if os.path.isfile(image.image.path):
            os.remove(image.image.path)
    image.delete()
    
    messages.success(request, "Image deleted successfully.")
    return redirect('rentease:property_edit', slug=property.slug)

@login_required
def profile_view(request):
    profile = request.user.profile
    context = {
        'profile': profile,
        'properties': Property.objects.filter(owner=request.user),
        'bookings': Booking.objects.filter(tenant=request.user),
    }
    return render(request, 'RentEase/profile.html', context)

@login_required
def profile_edit(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=request.user.profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated successfully.')
            return redirect('rentease:profile')
    else:
        form = ProfileForm(instance=request.user.profile)
    
    return render(request, 'RentEase/profile_edit.html', {'form': form})

@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password was successfully updated!')
            return redirect('rentease:profile')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'RentEase/change_password.html', {'form': form})

def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Account created successfully! You can now login.')
            return redirect('login')
    else:
        form = RegisterForm()
    return render(request, 'registration/register.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('rentease:property_list')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('rentease:property_list')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'registration/login.html')

def custom_logout(request):
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('rentease:property_list')

def logout_view(request):
    return custom_logout(request)

@login_required
def manage_bookings(request):
    """View for property owners to manage their bookings"""
    # Get all properties owned by the current user
    user_properties = Property.objects.filter(owner=request.user)
    
    # Get all bookings for these properties
    bookings = Booking.objects.filter(property__in=user_properties).order_by('-created_at')
    
    # Group bookings by status
    pending_bookings = bookings.filter(status='pending')
    approved_bookings = bookings.filter(status='approved')
    rejected_bookings = bookings.filter(status='rejected')
    
    context = {
        'pending_bookings': pending_bookings,
        'approved_bookings': approved_bookings,
        'rejected_bookings': rejected_bookings,
    }
    
    return render(request, 'RentEase/manage_bookings.html', context)

@login_required
def update_booking_status(request, booking_id):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'error': 'Invalid request method'})

    try:
        booking = Booking.objects.get(id=booking_id)
        
        # Check if the user is the property owner
        if booking.property.owner != request.user:
            return JsonResponse({'status': 'error', 'error': 'Unauthorized'})
        
        new_status = request.POST.get('status')
        if new_status not in ['approved', 'rejected']:
            return JsonResponse({'status': 'error', 'error': 'Invalid status'})
        
        # Update booking status
        booking.status = new_status
        booking.save()
        
        # Send email notification
        context = {
            'tenant': booking.tenant,
            'property': booking.property,
            'booking': booking,
            'site_url': settings.SITE_URL,
        }
        
        if new_status == 'approved':
            subject = 'Your Booking Request has been Approved!'
            html_template = 'RentEase/email/booking_approved_notification.html'
            text_template = 'RentEase/email/booking_approved_notification_plain.txt'
        else:  # rejected
            subject = 'Update on Your Booking Request'
            html_template = 'RentEase/email/booking_rejected_notification.html'
            text_template = 'RentEase/email/booking_rejected_notification_plain.txt'
        
        # Render email templates
        html_message = render_to_string(html_template, context)
        plain_message = render_to_string(text_template, context)
        
        # Send email
        msg = EmailMultiAlternatives(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [booking.tenant.email]
        )
        msg.attach_alternative(html_message, "text/html")
        msg.send()
        
        return JsonResponse({
            'status': 'success',
            'message': f'Booking has been {new_status}. Notification email sent to tenant.'
        })
        
    except Booking.DoesNotExist:
        return JsonResponse({'status': 'error', 'error': 'Booking not found'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'error': str(e)})

def create_subscription_plan(request, slug, plan_type):
    property = get_object_or_404(Property, slug=slug, owner=request.user)
    messages.error(request, 'This subscription method is no longer available.')
    return redirect('rentease:property_detail', slug=slug)

def create_subscription(request, slug, plan_id):
    property = get_object_or_404(Property, slug=slug, owner=request.user)
    messages.error(request, 'This subscription method is no longer available.')
    return redirect('rentease:property_detail', slug=slug)

def subscription_success(request, slug):
    property = get_object_or_404(Property, slug=slug, owner=request.user)
    messages.error(request, 'This subscription method is no longer available.')
    return redirect('rentease:property_detail', slug=slug)

def subscription_cancel(request, slug):
    property = get_object_or_404(Property, slug=slug, owner=request.user)
    messages.error(request, 'This subscription method is no longer available.')
    return redirect('rentease:property_detail', slug=slug)

@login_required
def subscribe(request):
    # Check if user already has an active subscription
    subscription = Subscription.objects.filter(user=request.user).first()
    user_properties = Property.objects.filter(owner=request.user).count()
    
    if subscription and subscription.is_active():
        messages.info(request, 'You already have an active subscription.')
        return redirect('rentease:my_properties')
    
    if user_properties <= 1:
        messages.info(request, 'You can list one property for free. Subscription is only needed for multiple properties.')
        return redirect('rentease:my_properties')

    # PayPal payment form
    paypal_dict = {
        "cmd": "_xclick-subscriptions",
        "business": settings.PAYPAL_RECEIVER_EMAIL,
        "a3": settings.PAYPAL_SUBSCRIPTION_PRICE,  # monthly price
        "p3": 1,  # duration of each unit (1 month)
        "t3": "M",  # duration unit (Month)
        "src": "1",  # make payments recur
        "sra": "1",  # reattempt payment on payment error
        "no_note": "1",  # remove extra notes (optional)
        "item_name": "RentEase Landlord Premium Subscription",
        "custom": request.user.id,  # Custom field to identify the user
        "currency_code": settings.PAYPAL_CURRENCY,
        "return": request.build_absolute_uri(reverse('rentease:payment_successful')),
        "cancel_return": request.build_absolute_uri(reverse('rentease:payment_cancelled')),
        "notify_url": request.build_absolute_uri(reverse('paypal-ipn')),
    }

    form = PayPalPaymentsForm(initial=paypal_dict)
    return render(request, 'RentEase/subscribe.html', {'form': form})

@login_required
def payment_successful(request):
    messages.success(request, 'Thank you for subscribing! Your payment is being processed.')
    return redirect('rentease:my_properties')

@login_required
def payment_cancelled(request):
    messages.warning(request, 'Your subscription payment was cancelled.')
    return redirect('rentease:my_properties')

@receiver(valid_ipn_received)
def ipn_receiver(sender, **kwargs):
    ipn_obj = sender
    
    if ipn_obj.payment_status == "Completed":
        # Check if it's a subscription payment
        if ipn_obj.txn_type == "subscr_payment":
            try:
                user = User.objects.get(id=ipn_obj.custom)
                subscription, created = Subscription.objects.get_or_create(user=user)
                subscription.activate(ipn_obj.subscr_id)
                
                # Send confirmation email
                subject = 'RentEase Subscription Activated'
                message = f'Your RentEase subscription has been activated. Valid until: {subscription.end_date}'
                user.email_user(subject, message)
                
            except User.DoesNotExist:
                # Log error or handle invalid user
                pass
        
        # Handle subscription cancellation
        elif ipn_obj.txn_type == "subscr_cancel":
            try:
                user = User.objects.get(id=ipn_obj.custom)
                subscription = Subscription.objects.get(user=user)
                subscription.cancel()
                
                # Send cancellation email
                subject = 'RentEase Subscription Cancelled'
                message = 'Your RentEase subscription has been cancelled.'
                user.email_user(subject, message)
                
            except (User.DoesNotExist, Subscription.DoesNotExist):
                # Log error or handle invalid user/subscription
                pass
