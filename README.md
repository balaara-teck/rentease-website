# RentEase - Property Rental Management System

RentEase is a comprehensive property rental management system built with Django that enables property owners to list their properties and manage bookings while allowing tenants to browse and book properties.

## Features

### For Property Owners
- Property Management
  * List new properties with detailed information
  * Upload multiple property images
  * Set property status (available, booked, unavailable)
  * Edit property details
  * Delete properties

- Booking Management
  * View all booking requests
  * Approve/reject booking requests
  * Automatic email notifications
  * Booking status tracking

### For Tenants
- Property Search
  * Browse available properties
  * Search by location, price, and amenities
  * View property details and images
  * Check property availability

- Booking System
  * Request property bookings
  * View booking status
  * Cancel pending bookings
  * Contact property owners

### General Features
- User Authentication
  * User registration and login
  * Profile management
  * Password change functionality
  * Social authentication support

- Email Notifications
  * Booking request notifications
  * Booking status updates
  * HTML and plain text email support
  * Customized email templates

- Responsive Design
  * Mobile-first approach
  * Modern UI/UX
  * Bootstrap framework
  * Font Awesome icons

## Technical Stack

- Backend:
  * Django 5.1.3
  * Python 3.12
  * SQLite database

- Frontend:
  * HTML5/CSS3
  * JavaScript
  * Bootstrap
  * Font Awesome

- Image Processing:
  * Pillow for image optimization
  * Automatic image resizing
  * Format conversion

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/rentease-website.git
cd rentease-website
```

2. Create and activate virtual environment:
```bash
python -m venv v
source v/bin/activate  # On Windows: v\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your settings
```

5. Run migrations:
```bash
python manage.py migrate
```

6. Create superuser:
```bash
python manage.py createsuperuser
```

7. Run the development server:
```bash
python manage.py runserver
```

## Project Structure

```
rentease-website/
├── RentEase/
│   ├── migrations/
│   ├── management/
│   ├── templates/
│   │   └── RentEase/
│   │       ├── email/
│   │       └── ...
│   ├── models.py
│   ├── views.py
│   ├── forms.py
│   ├── urls.py
│   └── admin.py
├── engine/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── static/
├── media/
├── requirements.txt
└── manage.py
```

## Models

- **Property**: Stores property information including type, price, location, and status
- **PropertyImage**: Handles property images with automatic optimization
- **Booking**: Manages booking requests and their statuses
- **Profile**: Extends User model with additional information
- **PropertyAmenity**: Stores property amenities

## Views

- Property listing and detail views
- Booking management views
- User profile views
- Property management views
- Search and filter views

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Django documentation
- Bootstrap framework
- Font Awesome icons
- Pillow library