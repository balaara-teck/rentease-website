from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.utils.text import slugify
from django.db.models import Max
from PIL import Image
import os
from django.core.exceptions import ValidationError
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone
import tempfile

def validate_image_size(value):
    if value.size > settings.MAX_UPLOAD_SIZE:
        raise ValidationError(f'File size too large. Size should not exceed {settings.MAX_UPLOAD_SIZE/1024/1024:.1f} MB.')

def validate_video_size(value):
    # 20MB limit for videos
    max_size = 20 * 1024 * 1024  # 20MB in bytes
    if value.size > max_size:
        raise ValidationError(f'Video size must be less than 20MB. Your video is {value.size / (1024*1024):.1f}MB')

def validate_video_format(value):
    import os
    valid_extensions = ['.mp4']  # Only allow MP4 for better compatibility
    ext = os.path.splitext(value.name)[1].lower()
    if ext not in valid_extensions:
        raise ValidationError('Only MP4 video format is supported.')

class Property(models.Model):
    PROPERTY_TYPES = [
        ('house', 'House'),
        ('apartment', 'Apartment'),
        ('villa', 'Villa'),
        ('studio', 'Studio'),
        ('other', 'Other'),
    ]
    
    PROPERTY_STATUS = [
        ('available', 'Available'),
        ('booked', 'Booked'),
        ('unavailable', 'Unavailable'),
    ]
    
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='properties')
    title = models.CharField(max_length=200)
    description = models.TextField()
    property_type = models.CharField(max_length=20, choices=PROPERTY_TYPES)
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    bedrooms = models.PositiveIntegerField()
    bathrooms = models.PositiveIntegerField()
    area = models.DecimalField(max_digits=10, decimal_places=2, help_text="Area in square meters")
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=20)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    status = models.CharField(max_length=20, choices=PROPERTY_STATUS, default='available')
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    slug = models.SlugField(unique=True, blank=True)
    subscription_active = models.BooleanField(default=False)
    subscription_end_date = models.DateTimeField(null=True, blank=True)
    paypal_subscription_id = models.CharField(max_length=100, null=True, blank=True)
    video = models.FileField(
        upload_to='property_videos/', 
        null=True, 
        blank=True,
        validators=[validate_video_size, validate_video_format],
        help_text="Upload a video tour (max 20MB, MP4 format only)"
    )
    
    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            
            while Property.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            
            self.slug = slug
        super().save(*args, **kwargs)
    
    def is_listing_visible(self):
        if not self.subscription_active:
            return False
        if self.subscription_end_date and self.subscription_end_date < timezone.now():
            self.subscription_active = False
            self.save()
            return False
        return True
    
    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name_plural = "Properties"

class PropertyImage(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='property_images/', validators=[validate_image_size])
    is_main = models.BooleanField(default=False)
    caption = models.CharField(max_length=200, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        
        # Open the image
        img = Image.open(self.image.path)
        
        # Calculate new dimensions while maintaining aspect ratio
        max_size = (800, 600)
        ratio = min(max_size[0]/img.width, max_size[1]/img.height)
        new_size = (int(img.width * ratio), int(img.height * ratio))
        
        # Resize and save
        if img.width > max_size[0] or img.height > max_size[1]:
            img = img.resize(new_size, Image.Resampling.LANCZOS)
            # Convert to RGB if necessary (for PNG transparency)
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            img.save(self.image.path, quality=85, optimize=True)

    def __str__(self):
        return f"Image for {self.property.title}"

class PropertyAmenity(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='amenities')
    name = models.CharField(max_length=100)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Property Amenities"

class Booking(models.Model):
    BOOKING_STATUS = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]
    
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='bookings')
    tenant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    start_date = models.DateField()
    end_date = models.DateField()
    message = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=BOOKING_STATUS, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Booking for {self.property.title} by {self.tenant.username}"

@receiver(post_save, sender=Booking)
def booking_status_changed(sender, instance, created, **kwargs):
    """Handle booking status changes and notifications"""
    if created:
        # Update property status
        property_instance = instance.property
        property_instance.status = 'booked'
        property_instance.save()
        
        # Format dates nicely
        start_date = instance.start_date.strftime("%B %d, %Y")
        end_date = instance.end_date.strftime("%B %d, %Y")
        
        # Create context for email template
        context = {
            'booking': instance,
            'property': property_instance,
            'tenant': instance.tenant,
            'start_date': start_date,
            'end_date': end_date,
            'site_url': settings.SITE_URL,
        }
        
        # Send email to property owner
        subject = f'New Booking Request for {property_instance.title}'
        
        # Render both versions of the email
        html_message = render_to_string('RentEase/email/booking_notification.html', context)
        text_message = render_to_string('RentEase/email/booking_notification_plain.txt', context)
        
        # Create and send the email
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[property_instance.owner.email],
        )
        email.attach_alternative(html_message, "text/html")
        email.send(fail_silently=False)

class Subscription(models.Model):
    SUBSCRIPTION_STATUS = [
        ('active', 'Active'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=SUBSCRIPTION_STATUS, default='expired')
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    paypal_subscription_id = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s subscription ({self.status})"

    def is_active(self):
        if self.status == 'active' and self.end_date:
            return self.end_date > timezone.now()
        return False

    def activate(self, subscription_id, months=1):
        self.status = 'active'
        self.paypal_subscription_id = subscription_id
        self.start_date = timezone.now()
        self.end_date = self.start_date + timezone.timedelta(days=30 * months)
        self.save()

    def cancel(self):
        self.status = 'cancelled'
        self.save()

    def expire(self):
        self.status = 'expired'
        self.save()

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to='profile_avatars/', null=True, blank=True)
    phone_number = models.CharField(max_length=15, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    location = models.CharField(max_length=100, blank=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"
    
    def get_avatar_url(self):
        if self.avatar:
            return self.avatar.url
        return "https://ui-avatars.com/api/?name=" + self.user.get_full_name().replace(" ", "+")

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()
