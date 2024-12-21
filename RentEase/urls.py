from django.urls import path
from . import views

app_name = 'rentease'

urlpatterns = [
    path('', views.property_list, name='property_list'),
    path('property/create/', views.property_create, name='property_create'),
    path('property/<slug:slug>/', views.property_detail, name='property_detail'),
    path('property/<slug:slug>/edit/', views.property_edit, name='property_edit'),
    path('property/<slug:slug>/delete/', views.property_delete, name='property_delete'),
    path('my-properties/', views.my_properties, name='my_properties'),
    path('delete-image/<int:image_id>/', views.delete_image, name='delete_image'),
    path('delete-video/<slug:slug>/', views.delete_video, name='delete_video'),
    
    # User profile and authentication
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    
    # Bookings
    path('manage-bookings/', views.manage_bookings, name='manage_bookings'),
    path('my-bookings/', views.my_bookings, name='my_bookings'),
    path('booking/<int:booking_id>/update/', views.update_booking_status, name='update_booking_status'),
    path('booking/<int:booking_id>/cancel/', views.cancel_booking, name='cancel_booking'),
    
    # Subscription URLs
    path('subscribe/', views.subscribe, name='subscribe'),
    path('payment-successful/', views.payment_successful, name='payment_successful'),
    path('payment-cancelled/', views.payment_cancelled, name='payment_cancelled'),
    
    # Subscription plan URLs
    path('property/<slug:slug>/create-plan/<str:plan_type>/', views.create_subscription_plan, name='create_subscription_plan'),
    path('property/<slug:slug>/create-subscription/<str:plan_id>/', views.create_subscription, name='create_subscription'),
    path('property/<slug:slug>/subscription-success/', views.subscription_success, name='subscription_success'),
    path('property/<slug:slug>/subscription-cancel/', views.subscription_cancel, name='subscription_cancel'),
    
    # Footer Static Pages
    path('about-us/', views.about_us, name='about_us'),
    path('how-it-works/', views.how_it_works, name='how_it_works'),
    path('careers/', views.careers, name='careers'),
    path('press/', views.press, name='press'),
    path('help-center/', views.help_center, name='help_center'),
    path('safety-info/', views.safety_info, name='safety_info'),
    path('contact-us/', views.contact_us, name='contact_us'),
    path('terms-of-service/', views.terms_of_service, name='terms_of_service'),
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
    path('cookie-policy/', views.cookie_policy, name='cookie_policy'),
]
