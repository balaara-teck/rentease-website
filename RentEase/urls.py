from django.urls import path
from . import views

app_name = 'rentease'

urlpatterns = [
    path('', views.property_list, name='property_list'),
    path('property/create/', views.property_create, name='property_create'),
    path('property/<slug:slug>/', views.property_detail, name='property_detail'),
    path('property/<slug:slug>/contact/', views.contact_owner, name='contact_owner'),
    path('property/<int:pk>/edit/', views.property_edit, name='property_edit'),
    path('property/<int:pk>/delete/', views.property_delete, name='property_delete'),
    path('property/image/<int:image_id>/delete/', views.delete_image, name='delete_image'),
    path('my-properties/', views.my_properties, name='my_properties'),
    path('manage-bookings/', views.manage_bookings, name='manage_bookings'),
    path('booking/<int:booking_id>/update-status/', views.update_booking_status, name='update_booking_status'),
    path('my-bookings/', views.my_bookings, name='my_bookings'),
    path('booking/<int:booking_id>/cancel/', views.cancel_booking, name='cancel_booking'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('profile/change-password/', views.change_password, name='change_password'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.custom_logout, name='custom_logout'),
    path('property/<int:property_id>/create-plan/<str:plan_type>/', views.create_subscription_plan, name='create_subscription_plan'),
    path('property/<int:property_id>/subscribe/<str:plan_id>/', views.create_subscription, name='create_subscription'),
    path('property/<int:property_id>/subscription/success/', views.subscription_success, name='subscription_success'),
    path('property/<int:property_id>/subscription/cancel/', views.subscription_cancel, name='subscription_cancel'),
]
