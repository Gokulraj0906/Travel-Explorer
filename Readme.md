Travel Explorer - Modern Travel Booking System
A comprehensive full-stack travel booking application built with Flask (Python) backend and vanilla JavaScript frontend. This modern web application allows users to browse travel packages, make bookings, and provides administrators with a complete management dashboard.
🌟 Features
For Users

* User Authentication: Secure registration and login system with JWT tokens
* Browse Packages: View beautifully designed travel packages with detailed information
* Book Trips: Easy booking system with date selection and guest count
* Booking Management: View and manage personal bookings
* Responsive Design: Mobile-first design that works on all devices

For Administrators

* Admin Dashboard: Comprehensive statistics and analytics
* Package Management: Create, edit, and delete travel packages
* Booking Management: View all bookings and update their status
* User Management: Manage registered users
* Settings: Configure site settings and preferences

🛠️ Technology Stack
Backend

* Flask - Python web framework
* MongoDB - NoSQL database
* PyMongo - MongoDB driver for Python
* JWT - JSON Web Tokens for authentication
* Werkzeug - Password hashing and security
* Flask-CORS - Cross-Origin Resource Sharing

Frontend

* HTML5 - Semantic markup
* CSS3 - Modern styling with CSS Grid and Flexbox
* Vanilla JavaScript - No frameworks, pure JS
* Font Awesome - Icon library
* Google Fonts - Typography

📋 Prerequisites
Before running this application, make sure you have the following installed:

* Python 3.7 or higher
* MongoDB 4.0 or higher
* pip (Python package installer)

🚀 Installation & Setup
1. Clone the Repository
bashDownloadCopy code Wrapgit clone <repository-url>
cd travel-explorer
2. Install Python Dependencies
bashDownloadCopy code Wrappip install flask flask-cors flask-pymongo werkzeug pyjwt
3. Start MongoDB Service
Windows:
bashDownloadCopy code Wrapnet start MongoDB
macOS (with Homebrew):
bashDownloadCopy code Wrapbrew services start mongodb-community
Linux (Ubuntu/Debian):
bashDownloadCopy code Wrapsudo systemctl start mongod
sudo systemctl enable mongod
4. Configure Environment
The application uses default MongoDB connection settings:

* Host: localhost
* Port: 27017
* Database: travel_explorer

If you need to modify these settings, update the MONGO_URI in app.py:
pythonDownloadCopy code Wrapapp.config['MONGO_URI'] = 'mongodb://localhost:27017/travel_explorer'
5. Run the Application
bashDownloadCopy code Wrappython app.py
The application will start on http://localhost:5000
6. Initialize Database
Visit http://localhost:5000 and click the "Initialize DB" button, or make a POST request to:
bashDownloadCopy code Wrapcurl -X POST http://localhost:5000/api/seed
🔑 Default Credentials
After seeding the database, you can log in with these credentials:
Administrator Account

* Email: admin@example.com
* Password: admin123

Test User Account

* Email: user@example.com
* Password: user123

📁 Project Structure
travel-explorer/
│
├── app.py                 # Main Flask application
├── templates/
│   └── kayal.html        # Frontend HTML file
├── README.md             # Project documentation
└── requirements.txt      # Python dependencies (optional)

🔌 API Endpoints
Authentication

* POST /api/auth/register - User registration
* POST /api/auth/login - User login
* GET /api/auth/verify - Verify JWT token

Packages

* GET /api/packages - Get all packages
* POST /api/packages - Create package (Admin only)
* GET /api/packages/<id> - Get specific package
* PUT /api/packages/<id> - Update package (Admin only)
* DELETE /api/packages/<id> - Delete package (Admin only)

Bookings

* GET /api/bookings - Get user bookings (or all for admin)
* POST /api/bookings - Create new booking
* GET /api/bookings/<id> - Get specific booking
* PATCH /api/bookings/<id> - Update booking status
* DELETE /api/bookings/<id> - Delete booking

Admin

* GET /api/admin/stats - Get dashboard statistics
* GET /api/users - Get all users (Admin only)
* DELETE /api/users/<id> - Delete user (Admin only)

Settings

* GET /api/settings - Get site settings
* POST /api/settings - Update settings (Admin only)

Utilities

* POST /api/seed - Initialize database with sample data
* DELETE /api/clear-db - Clear database (Development only)
* GET /api/health - Health check endpoint

🎨 Features Breakdown
User Interface

* Modern Design: Clean, responsive design with smooth animations
* Mobile First: Optimized for mobile devices with responsive breakpoints
* Interactive Elements: Hover effects, loading states, and smooth transitions
* User Feedback: Toast notifications for all user actions

Security

* JWT Authentication: Secure token-based authentication system
* Password Hashing: Passwords are hashed using Werkzeug's security functions
* Role-Based Access: Different permissions for users and administrators
* Input Validation: Comprehensive validation on both frontend and backend

Database Design

* Users Collection: Stores user credentials and profile information
* Packages Collection: Travel package details with pricing and features
* Bookings Collection: User bookings with status tracking
* Settings Collection: Site configuration and settings

📱 Responsive Design
The application is fully responsive with breakpoints for:

* Mobile: < 768px
* Tablet: 768px - 1024px
* Desktop: > 1024px

🔧 Development
Adding New Features

1. Backend: Add new routes in app.py
2. Frontend: Update kayal.html with new functionality
3. Database: Modify MongoDB collections as needed

Environment Variables
For production deployment, consider using environment variables:
pythonDownloadCopy code Wrapimport os
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'fallback-secret-key')
app.config['MONGO_URI'] = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/travel_explorer')
🚀 Deployment
Development
The application runs in debug mode by default. For production:

1. Set Environment Variables:

bashDownloadCopy code Wrapexport FLASK_ENV=production
export SECRET_KEY=your-secret-key
export MONGO_URI=your-mongodb-connection-string

1. Use a Production WSGI Server:

bashDownloadCopy code Wrappip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
Production Considerations

* Use environment variables for sensitive configuration
* Implement proper logging
* Set up reverse proxy (nginx)
* Use SSL certificates
* Implement rate limiting
* Set up monitoring and error tracking

🧪 Testing
Manual Testing

1. Registration: Create new user accounts
2. Authentication: Test login/logout functionality
3. Booking Flow: Complete booking process
4. Admin Functions: Test admin dashboard features

API Testing
Use tools like Postman or curl to test API endpoints:
bashDownloadCopy code Wrap# Test health endpoint
curl http://localhost:5000/api/health

# Test package listing
curl http://localhost:5000/api/packages
🐛 Troubleshooting
Common Issues

1. 
MongoDB Connection Error:

Ensure MongoDB service is running
Check connection string in app.py
Verify MongoDB is accessible on port 27017


2. 
CORS Issues:

Flask-CORS is configured to allow all origins in development
For production, configure specific allowed origins


3. 
JWT Token Issues:

Check if token is being sent in Authorization header
Verify token hasn't expired (7-day expiration)


4. 
Database Not Seeding:

Ensure MongoDB is running and accessible
Check if collections already exist (seeding only works on empty database)



📝 Contributing

1. Fork the repository
2. Create a feature branch: git checkout -b feature-name
3. Make your changes and test thoroughly
4. Commit your changes: git commit -am 'Add new feature'
5. Push to the branch: git push origin feature-name
6. Submit a pull request

📄 License
This project is licensed under the MIT License - see the LICENSE file for details.
👥 Support
For support, please contact:

* Email: gokulsenthil0906@gmail.com
* Issues: GitHub Issues

🎯 Future Enhancements

* Payment Integration: Stripe/PayPal integration
* Email Notifications: Booking confirmations and updates
* Reviews & Ratings: Package review system
* Advanced Search: Filter by price, location, duration
* Real-time Chat: Customer support chat
* Mobile App: React Native mobile application
* Multi-language Support: Internationalization
* Social Login: Google/Facebook authentication

📊 Monitoring
For production deployments, consider implementing:

* Application performance monitoring (APM)
* Error tracking (Sentry)
* Log aggregation (ELK stack)
* Uptime monitoring
* Database performance monitoring


Happy Traveling! 🌍✈️