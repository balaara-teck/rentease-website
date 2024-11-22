from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Booking, Property, Profile
from datetime import date

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')

class BookingForm(forms.ModelForm):
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        help_text='Select the move-in date'
    )
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        help_text='Select the move-out date'
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        required=False,
        help_text='Any special requests or questions?'
    )

    class Meta:
        model = Booking
        fields = ['start_date', 'end_date', 'message']

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if start_date and end_date:
            # Check if start date is not in the past
            if start_date < date.today():
                raise forms.ValidationError("Start date cannot be in the past.")

            # Check if end date is after start date
            if end_date <= start_date:
                raise forms.ValidationError("End date must be after start date.")

            # Check if the duration is within reasonable limits (e.g., max 1 year)
            duration = (end_date - start_date).days
            if duration > 365:
                raise forms.ValidationError("Booking duration cannot exceed 1 year.")

        return cleaned_data

class PropertyEditForm(forms.ModelForm):
    class Meta:
        model = Property
        fields = ['title', 'description', 'price', 'bedrooms', 'bathrooms', 
                 'area', 'city', 'state', 'property_type', 'is_available']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'price': forms.NumberInput(attrs={'min': 0}),
            'bedrooms': forms.NumberInput(attrs={'min': 0}),
            'bathrooms': forms.NumberInput(attrs={'min': 0}),
            'area': forms.NumberInput(attrs={'min': 0}),
        }

    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price is not None and price < 0:
            raise forms.ValidationError("Price cannot be negative.")
        return price

    def clean(self):
        cleaned_data = super().clean()
        bedrooms = cleaned_data.get('bedrooms')
        bathrooms = cleaned_data.get('bathrooms')
        area = cleaned_data.get('area')

        if bedrooms is not None and bedrooms < 0:
            self.add_error('bedrooms', "Number of bedrooms cannot be negative.")
        if bathrooms is not None and bathrooms < 0:
            self.add_error('bathrooms', "Number of bathrooms cannot be negative.")
        if area is not None and area < 0:
            self.add_error('area', "Area cannot be negative.")

        return cleaned_data

class ProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)
    email = forms.EmailField(required=False)

    class Meta:
        model = Profile
        fields = ['avatar', 'phone_number', 'bio', 'location']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email

    def save(self, commit=True):
        profile = super().save(commit=False)
        if commit:
            # Save user info
            user = profile.user
            user.first_name = self.cleaned_data['first_name']
            user.last_name = self.cleaned_data['last_name']
            user.email = self.cleaned_data['email']
            user.save()
            profile.save()
        return profile
