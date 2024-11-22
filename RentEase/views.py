from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import logout, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from .forms import RegisterForm, BookingForm, PropertyEditForm, ProfileForm
from .models import Property, PropertyImage, Booking, Profile
from django.core.paginator import Paginator
from django.db.models import Q
from datetime import date
import os

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
    
    return render(request, 'RentEase/property_detail.html', {
        'property': property,
        'booking_form': booking_form,
        'existing_bookings': existing_bookings
    })

@login_required
def property_create(request):
    if request.method == 'POST':
        # Handle property creation
        title = request.POST.get('title')
        description = request.POST.get('description')
        property_type = request.POST.get('property_type')
        price = request.POST.get('price')
        bedrooms = request.POST.get('bedrooms')
        bathrooms = request.POST.get('bathrooms')
        area = request.POST.get('area')
        address = request.POST.get('address')
        city = request.POST.get('city')
        state = request.POST.get('state')
        zip_code = request.POST.get('zip_code')
        
        property = Property.objects.create(
            owner=request.user,
            title=title,
            description=description,
            property_type=property_type,
            price=price,
            bedrooms=bedrooms,
            bathrooms=bathrooms,
            area=area,
            address=address,
            city=city,
            state=state,
            zip_code=zip_code
        )
        
        # Handle image uploads
        images = request.FILES.getlist('images')
        for image in images:
            PropertyImage.objects.create(
                property=property,
                image=image,
                is_main=PropertyImage.objects.filter(property=property).count() == 0
            )
        
        messages.success(request, 'Property listed successfully!')
        return redirect('rentease:property_detail', slug=property.slug)
    
    return render(request, 'RentEase/property_form.html')

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
def property_delete(request, pk):
    property = get_object_or_404(Property, pk=pk)
    
    # Ensure the user owns this property
    if property.owner != request.user:
        messages.error(request, "You don't have permission to delete this property.")
        return redirect('rentease:my_properties')
    
    if request.method == 'POST':
        # Delete all associated images first
        for image in property.images.all():
            try:
                # Try to delete the actual image file if it exists
                if image.image and hasattr(image.image, 'path') and os.path.isfile(image.image.path):
                    image.image.delete()
            except Exception as e:
                # Log the error but continue with deletion
                print(f"Error deleting image file: {e}")
            # Delete the image record
            image.delete()
        
        # Delete the property
        property.delete()
        messages.success(request, "Property has been deleted successfully.")
        return redirect('rentease:my_properties')
    
    return redirect('rentease:my_properties')

@login_required
def property_edit(request, pk):
    property = get_object_or_404(Property, pk=pk)
    
    # Ensure the user owns this property
    if property.owner != request.user:
        messages.error(request, "You don't have permission to edit this property.")
        return redirect('rentease:my_properties')
    
    if request.method == 'POST':
        form = PropertyEditForm(request.POST, instance=property)
        if form.is_valid():
            property = form.save(commit=False)
            property.save()
            
            # Handle image uploads
            images = request.FILES.getlist('images')
            current_image_count = property.images.count()
            remaining_slots = 5 - current_image_count  # Maximum 5 images allowed
            
            if len(images) > remaining_slots:
                messages.warning(request, f"Only {remaining_slots} more images allowed. Some images were not uploaded.")
                images = images[:remaining_slots]
            
            for image in images:
                PropertyImage.objects.create(property=property, image=image)
            
            messages.success(request, "Property updated successfully.")
            return redirect('rentease:property_detail', slug=property.slug)
    else:
        form = PropertyEditForm(instance=property)
    
    return render(request, 'RentEase/property_edit.html', {
        'form': form,
        'property': property
    })

@login_required
def delete_image(request, image_id):
    image = get_object_or_404(PropertyImage, id=image_id)
    property = image.property
    
    # Ensure the user owns this property
    if property.owner != request.user:
        messages.error(request, "You don't have permission to delete this image.")
        return redirect('rentease:property_edit', pk=property.pk)
    
    # Delete the image file and record
    if image.image:
        image.image.delete()
    image.delete()
    
    messages.success(request, "Image deleted successfully.")
    return redirect('rentease:property_edit', pk=property.pk)

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

def custom_logout(request):
    logout(request)
    return redirect('rentease:property_list')

def logout_view(request):
    return custom_logout(request)
