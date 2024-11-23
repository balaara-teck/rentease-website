# RentEase - House Rental Platform

RentEase is a user-friendly platform that connects house owners with potential tenants, streamlining the house rental process. Our platform focuses exclusively on residential properties, making it easier for homeowners to list their houses and for tenants to find their perfect home.

## Features

### For House Owners
- House Management
  * List your house with detailed information
  * Upload multiple house photos
  * Set house availability status
  * Update house details and pricing
  * Track rental history

- Tenant Management
  * Review tenant applications
  * Approve/reject rental requests
  * Communicate with potential tenants
  * Manage rental agreements
  * Receive instant notifications

### For Tenants
- House Search
  * Browse available houses
  * Search by location and preferences
  * View detailed house information
  * Check real-time availability
  * Save favorite houses

- Rental Process
  * Submit rental applications
  * Track application status
  * Communicate with house owners
  * Manage active rentals
  * View rental history

### Platform Features
- User Profiles
  * Secure registration and login
  * Verified user accounts
  * Profile customization
  * Rental history tracking
  * Communication preferences

- Communication System
  * In-app messaging
  * Email notifications
  * Application updates
  * Custom message templates
  * Read receipts

- Modern Interface
  * Clean, intuitive design
  * Mobile-responsive layout
  * Easy navigation
  * Dark/light mode
  * Accessibility features

## Technical Details

### Built With
- Backend:
  * Django 5.1.3
  * Python 3.12
  * SQLite database

- Frontend:
  * HTML5/CSS3
  * JavaScript
  * Bootstrap 5.3.2
  * Font Awesome 6.0.0

### Security Features
- Secure user authentication
- Data encryption
- CSRF protection
- XSS prevention
- Input validation

## Getting Started

1. Clone the repository:
```bash
git clone https://github.com/yourusername/rentease-website.git
cd rentease-website
```

2. Set up virtual environment:
```bash
python -m venv v
source v/bin/activate  # On Windows: v\Scripts\activate
```

3. Install requirements:
```bash
pip install -r requirements.txt
```

4. Configure settings:
```bash
cp .env.example .env
# Update .env with your settings
```

5. Initialize database:
```bash
python manage.py migrate
```

6. Create admin account:
```bash
python manage.py createsuperuser
```

7. Start development server:
```bash
python manage.py runserver
```

## Usage

### For House Owners
1. Create an account and verify your email
2. Complete your profile with personal details
3. Add your house listing with photos and details
4. Review and respond to tenant applications
5. Manage your rental agreements

### For Tenants
1. Register and verify your account
2. Set up your tenant profile
3. Search for available houses
4. Submit rental applications
5. Communicate with house owners

## Contributing

We welcome contributions to RentEase! Please follow these steps:

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contact

SolTeck - [GitHub](https://github.com/soltech)

Project Link: [https://github.com/yourusername/rentease-website](https://github.com/yourusername/rentease-website)