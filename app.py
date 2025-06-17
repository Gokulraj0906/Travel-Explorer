from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from datetime import datetime, timedelta
from bson import ObjectId
import os
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = '3a8d7b9e5a65a15cf12fcb8db991c05ed720b7806b5468f0b52c1f6f3b2c36fa'
app.config['MONGO_URI'] = 'mongodb://localhost:27017/travel_explorer'

mongo = PyMongo(app)
CORS(app)

# JWT decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
        
        try:
            if token.startswith('Bearer '):
                token = token.split(' ')[1]
            
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user = mongo.db.users.find_one({'_id': ObjectId(data['user_id'])})
            if not current_user:
                return jsonify({'message': 'Invalid token'}), 401
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Token is invalid'}), 401
        except Exception as e:
            return jsonify({'message': 'Token validation failed'}), 401
        
        return f(current_user, *args, **kwargs)
    
    return decorated

# Admin required decorator
def admin_required(f):
    @wraps(f)
    def decorated(current_user, *args, **kwargs):
        if current_user.get('role') != 'admin':
            return jsonify({'message': 'Admin access required'}), 403
        return f(current_user, *args, **kwargs)
    
    return decorated

# Helper function to convert ObjectId to string
def serialize_doc(doc):
    if doc and '_id' in doc:
        doc['_id'] = str(doc['_id'])
    return doc

def serialize_docs(docs):
    return [serialize_doc(doc) for doc in docs]

# Routes
@app.route('/')
def index():
    return render_template('kayal.html')

# Authentication Routes
@app.route('/api/auth/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'message': 'No data provided'}), 400
        
        # Validate required fields
        required_fields = ['name', 'email', 'password']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'message': f'{field} is required'}), 400
        
        # Check if user exists
        if mongo.db.users.find_one({'email': data['email']}):
            return jsonify({'message': 'User already exists with this email'}), 400
        
        # Validate email format (basic)
        if '@' not in data['email']:
            return jsonify({'message': 'Invalid email format'}), 400
        
        # Validate password length
        if len(data['password']) < 6:
            return jsonify({'message': 'Password must be at least 6 characters long'}), 400
        
        # Create new user
        user = {
            'name': data['name'].strip(),
            'email': data['email'].lower().strip(),
            'password': generate_password_hash(data['password']),
            'role': 'user',
            'created_at': datetime.utcnow()
        }
        
        result = mongo.db.users.insert_one(user)
        
        return jsonify({'message': 'User created successfully', 'user_id': str(result.inserted_id)}), 201
    
    except Exception as e:
        return jsonify({'message': 'Registration failed', 'error': str(e)}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'message': 'No data provided'}), 400
        
        if 'email' not in data or 'password' not in data:
            return jsonify({'message': 'Email and password are required'}), 400
        
        user = mongo.db.users.find_one({'email': data['email'].lower().strip()})
        
        if not user or not check_password_hash(user['password'], data['password']):
            return jsonify({'message': 'Invalid email or password'}), 401
        
        token = jwt.encode({
            'user_id': str(user['_id']),
            'exp': datetime.utcnow() + timedelta(days=7) 
        }, app.config['SECRET_KEY'], algorithm='HS256')
        
        return jsonify({
            'token': token,
            'user': {
                'id': str(user['_id']),
                'name': user['name'],
                'email': user['email'],
                'role': user['role']
            }
        }), 200
    
    except Exception as e:
        return jsonify({'message': 'Login failed', 'error': str(e)}), 500

@app.route('/api/auth/verify', methods=['GET'])
@token_required
def verify_token(current_user):
    return jsonify({
        'user': {
            'id': str(current_user['_id']),
            'name': current_user['name'],
            'email': current_user['email'],
            'role': current_user['role']
        }
    }), 200

# Package Routes
@app.route('/api/packages', methods=['GET'])
def get_packages():
    try:
        packages = list(mongo.db.packages.find())
        return jsonify(serialize_docs(packages)), 200
    except Exception as e:
        return jsonify({'message': 'Failed to fetch packages', 'error': str(e)}), 500

@app.route('/api/packages', methods=['POST'])
@token_required
@admin_required
def create_package(current_user):
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'message': 'No data provided'}), 400
        
        required_fields = ['name', 'description', 'price', 'originalPrice', 'discount', 'image', 'features']
        for field in required_fields:
            if field not in data:
                return jsonify({'message': f'{field} is required'}), 400
        
        package = {
            'name': data['name'],
            'description': data['description'],
            'price': float(data['price']),
            'originalPrice': float(data['originalPrice']),
            'discount': int(data['discount']),
            'image': data['image'],
            'features': data['features'] if isinstance(data['features'], list) else [],
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        result = mongo.db.packages.insert_one(package)
        package['_id'] = str(result.inserted_id)
        
        return jsonify(package), 201
    
    except Exception as e:
        return jsonify({'message': 'Failed to create package', 'error': str(e)}), 500

@app.route('/api/packages/<package_id>', methods=['GET'])
def get_package(package_id):
    try:
        package = mongo.db.packages.find_one({'_id': ObjectId(package_id)})
        if not package:
            return jsonify({'message': 'Package not found'}), 404
        
        return jsonify(serialize_doc(package)), 200
    except Exception as e:
        return jsonify({'message': 'Failed to fetch package', 'error': str(e)}), 500

@app.route('/api/packages/<package_id>', methods=['PUT'])
@token_required
@admin_required
def update_package(current_user, package_id):
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'message': 'No data provided'}), 400
        
        # Update package
        update_data = {
            'name': data.get('name'),
            'description': data.get('description'),
            'price': float(data.get('price', 0)),
            'originalPrice': float(data.get('originalPrice', 0)),
            'discount': int(data.get('discount', 0)),
            'image': data.get('image'),
            'features': data.get('features', []),
            'updated_at': datetime.utcnow()
        }
        
        # Remove None values
        update_data = {k: v for k, v in update_data.items() if v is not None}
        
        result = mongo.db.packages.update_one(
            {'_id': ObjectId(package_id)},
            {'$set': update_data}
        )
        
        if result.matched_count == 0:
            return jsonify({'message': 'Package not found'}), 404
        
        # Get updated package
        package = mongo.db.packages.find_one({'_id': ObjectId(package_id)})
        
        return jsonify(serialize_doc(package)), 200
    
    except Exception as e:
        return jsonify({'message': 'Failed to update package', 'error': str(e)}), 500

@app.route('/api/packages/<package_id>', methods=['DELETE'])
@token_required
@admin_required
def delete_package(current_user, package_id):
    try:
        result = mongo.db.packages.delete_one({'_id': ObjectId(package_id)})
        
        if result.deleted_count == 0:
            return jsonify({'message': 'Package not found'}), 404
        
        return jsonify({'message': 'Package deleted successfully'}), 200
    
    except Exception as e:
        return jsonify({'message': 'Failed to delete package', 'error': str(e)}), 500

# Booking Routes
@app.route('/api/bookings', methods=['POST'])
@token_required
def create_booking(current_user):
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'message': 'No data provided'}), 400
        
        # Validate required fields
        required_fields = ['destination', 'guests', 'check_in', 'check_out']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'message': f'{field} is required'}), 400
        
        # Validate dates
        try:
            check_in = datetime.strptime(data['check_in'], '%Y-%m-%d')
            check_out = datetime.strptime(data['check_out'], '%Y-%m-%d')
            
            if check_in >= check_out:
                return jsonify({'message': 'Check-out date must be after check-in date'}), 400
            
            if check_in < datetime.now().replace(hour=0, minute=0, second=0, microsecond=0):
                return jsonify({'message': 'Check-in date cannot be in the past'}), 400
                
        except ValueError:
            return jsonify({'message': 'Invalid date format. Use YYYY-MM-DD'}), 400
        
        booking = {
            'user_id': str(current_user['_id']),
            'package_id': data.get('package_id'),  # Optional for custom bookings
            'destination': data['destination'],
            'guests': int(data['guests']),
            'check_in': data['check_in'],
            'check_out': data['check_out'],
            'status': 'pending',
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        result = mongo.db.bookings.insert_one(booking)
        booking['_id'] = str(result.inserted_id)
        
        return jsonify(booking), 201
    
    except Exception as e:
        return jsonify({'message': 'Failed to create booking', 'error': str(e)}), 500

@app.route('/api/bookings', methods=['GET'])
@token_required
def get_bookings(current_user):
    try:
        user_id = str(current_user['_id'])
        
        # If admin and requesting all bookings
        if current_user.get('role') == 'admin' and request.args.get('all') == 'true':
            bookings = list(mongo.db.bookings.find().sort('created_at', -1))
        else:
            # Regular users can only see their own bookings
            bookings = list(mongo.db.bookings.find({'user_id': user_id}).sort('created_at', -1))
        
        # Add package details and user details for admin
        for booking in bookings:
            booking['_id'] = str(booking['_id'])
            
            # Add package details if available
            if booking.get('package_id'):
                try:
                    package = mongo.db.packages.find_one({'_id': ObjectId(booking['package_id'])})
                    if package:
                        booking['package'] = {
                            'name': package['name'],
                            'price': package['price'],
                            'image': package['image']
                        }
                except:
                    pass  # Package might have been deleted
            
            # Add user details for admin view
            if current_user.get('role') == 'admin':
                try:
                    user = mongo.db.users.find_one({'_id': ObjectId(booking['user_id'])})
                    if user:
                        booking['user'] = {
                            'name': user['name'],
                            'email': user['email']
                        }
                except:
                    pass
        
        return jsonify(bookings), 200
    
    except Exception as e:
        return jsonify({'message': 'Failed to fetch bookings', 'error': str(e)}), 500

@app.route('/api/bookings/<booking_id>', methods=['GET'])
@token_required
def get_booking(current_user, booking_id):
    try:
        booking = mongo.db.bookings.find_one({'_id': ObjectId(booking_id)})
        
        if not booking:
            return jsonify({'message': 'Booking not found'}), 404
        
        # Check if user owns this booking or is admin
        if str(booking['user_id']) != str(current_user['_id']) and current_user.get('role') != 'admin':
            return jsonify({'message': 'Access denied'}), 403
        
        return jsonify(serialize_doc(booking)), 200
    
    except Exception as e:
        return jsonify({'message': 'Failed to fetch booking', 'error': str(e)}), 500

@app.route('/api/bookings/<booking_id>', methods=['PATCH'])
@token_required
def update_booking_status(current_user, booking_id):
    try:
        data = request.get_json()
        
        if not data or 'status' not in data:
            return jsonify({'message': 'Status is required'}), 400
        
        booking = mongo.db.bookings.find_one({'_id': ObjectId(booking_id)})
        if not booking:
            return jsonify({'message': 'Booking not found'}), 404
        
        # Only admin can update booking status, or user can cancel their own booking
        if current_user.get('role') != 'admin':
            if str(booking['user_id']) != str(current_user['_id']):
                return jsonify({'message': 'Access denied'}), 403
            if data['status'] not in ['cancelled']:
                return jsonify({'message': 'Users can only cancel their own bookings'}), 403
        
        valid_statuses = ['pending', 'confirmed', 'completed', 'cancelled']
        if data['status'] not in valid_statuses:
            return jsonify({'message': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'}), 400
        
        # Update booking status
        mongo.db.bookings.update_one(
            {'_id': ObjectId(booking_id)},
            {'$set': {
                'status': data['status'],
                'updated_at': datetime.utcnow()
            }}
        )
        
        return jsonify({'message': 'Booking status updated successfully'}), 200
    
    except Exception as e:
        return jsonify({'message': 'Failed to update booking', 'error': str(e)}), 500

@app.route('/api/bookings/<booking_id>', methods=['DELETE'])
@token_required
def delete_booking(current_user, booking_id):
    try:
        booking = mongo.db.bookings.find_one({'_id': ObjectId(booking_id)})
        
        if not booking:
            return jsonify({'message': 'Booking not found'}), 404
        
        # Only admin or booking owner can delete
        if current_user.get('role') != 'admin' and str(booking['user_id']) != str(current_user['_id']):
            return jsonify({'message': 'Access denied'}), 403
        
        mongo.db.bookings.delete_one({'_id': ObjectId(booking_id)})
        
        return jsonify({'message': 'Booking deleted successfully'}), 200
    
    except Exception as e:
        return jsonify({'message': 'Failed to delete booking', 'error': str(e)}), 500

# User Management Routes (Admin only)
@app.route('/api/users', methods=['GET'])
@token_required
@admin_required
def get_users(current_user):
    try:
        users = list(mongo.db.users.find({}, {'password': 0}).sort('created_at', -1))  # Exclude password
        
        return jsonify(serialize_docs(users)), 200
    
    except Exception as e:
        return jsonify({'message': 'Failed to fetch users', 'error': str(e)}), 500

@app.route('/api/users/<user_id>', methods=['GET'])
@token_required
@admin_required
def get_user(current_user, user_id):
    try:
        user = mongo.db.users.find_one({'_id': ObjectId(user_id)}, {'password': 0})
        
        if not user:
            return jsonify({'message': 'User not found'}), 404
        
        return jsonify(serialize_doc(user)), 200
    
    except Exception as e:
        return jsonify({'message': 'Failed to fetch user', 'error': str(e)}), 500

@app.route('/api/users/<user_id>', methods=['DELETE'])
@token_required
@admin_required
def delete_user(current_user, user_id):
    try:
        # Prevent self-deletion
        if str(current_user['_id']) == user_id:
            return jsonify({'message': 'Cannot delete your own account'}), 400
        
        result = mongo.db.users.delete_one({'_id': ObjectId(user_id)})
        
        if result.deleted_count == 0:
            return jsonify({'message': 'User not found'}), 404
        
        # Also delete user's bookings (optional - you might want to keep them for records)
        # mongo.db.bookings.delete_many({'user_id': user_id})
        
        return jsonify({'message': 'User deleted successfully'}), 200
    
    except Exception as e:
        return jsonify({'message': 'Failed to delete user', 'error': str(e)}), 500

# Admin Statistics
@app.route('/api/admin/stats', methods=['GET'])
@token_required
@admin_required
def get_admin_stats(current_user):
    try:
        # Get basic counts
        total_users = mongo.db.users.count_documents({})
        total_bookings = mongo.db.bookings.count_documents({})
        active_packages = mongo.db.packages.count_documents({})
        
        # Calculate total revenue from completed bookings with package info
        pipeline = [
            {'$match': {'status': 'completed', 'package_id': {'$exists': True, '$ne': None}}},
            {'$addFields': {
                'package_oid': {'$toObjectId': '$package_id'}
            }},
            {'$lookup': {
                'from': 'packages',
                'localField': 'package_oid',
                'foreignField': '_id',
                'as': 'package_info'
            }},
            {'$unwind': '$package_info'},
            {'$group': {
                '_id': None,
                'total_revenue': {'$sum': '$package_info.price'}
            }}
        ]
        
        revenue_result = list(mongo.db.bookings.aggregate(pipeline))
        total_revenue = revenue_result[0]['total_revenue'] if revenue_result else 0
        
        # Get recent booking counts by status
        booking_stats = list(mongo.db.bookings.aggregate([
            {'$group': {
                '_id': '$status',
                'count': {'$sum': 1}
            }}
        ]))
        
        status_counts = {item['_id']: item['count'] for item in booking_stats}
        
        return jsonify({
            'totalUsers': total_users,
            'totalBookings': total_bookings,
            'activePackages': active_packages,
            'totalRevenue': total_revenue,
            'bookingStats': status_counts
        }), 200
    
    except Exception as e:
        return jsonify({'message': 'Failed to fetch statistics', 'error': str(e)}), 500

# Settings Routes
@app.route('/api/settings', methods=['GET'])
@token_required
@admin_required
def get_settings(current_user):
    try:
        settings = mongo.db.settings.find_one({}) or {}
        return jsonify(serialize_doc(settings)), 200
    
    except Exception as e:
        return jsonify({'message': 'Failed to fetch settings', 'error': str(e)}), 500

@app.route('/api/settings', methods=['POST'])
@token_required
@admin_required
def update_settings(current_user):
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'message': 'No data provided'}), 400
        
        # Add timestamp
        data['updated_at'] = datetime.utcnow()
        data['updated_by'] = str(current_user['_id'])
        
        # Update settings (upsert)
        mongo.db.settings.update_one(
            {},
            {'$set': data},
            upsert=True
        )
        
        return jsonify({'message': 'Settings updated successfully'}), 200
    
    except Exception as e:
        return jsonify({'message': 'Failed to update settings', 'error': str(e)}), 500

# Database Seed Route
@app.route('/api/seed', methods=['POST'])
def seed_data():
    try:
        # Check if data already exists
        if mongo.db.users.count_documents({}) > 0:
            return jsonify({'message': 'Database already contains data. Clear it first if you want to reseed.'}), 400
        
        # Create admin user
        admin_user = {
            'name': 'Admin User',
            'email': 'admin@example.com',
            'password': generate_password_hash('admin123'),
            'role': 'admin',
            'created_at': datetime.utcnow()
        }
        mongo.db.users.insert_one(admin_user)
        
        # Create a regular test user
        test_user = {
            'name': 'Test User',
            'email': 'user@example.com',
            'password': generate_password_hash('user123'),
            'role': 'user',
            'created_at': datetime.utcnow()
        }
        mongo.db.users.insert_one(test_user)
        
        # Create sample packages
        sample_packages = [
            {
                'name': 'Tropical Paradise',
                'description': 'Escape to a tropical paradise with pristine beaches, crystal-clear waters, and luxurious resorts. Perfect for relaxation and adventure.',
                'price': 1299,
                'originalPrice': 1599,
                'discount': 19,
                'image': 'https://images.unsplash.com/photo-1540202404-1b927e27fa8b?ixlib=rb-4.0.3&auto=format&fit=crop&w=675&q=80',
                'features': [
                    '7 days, 6 nights accommodation',
                    'All-inclusive resort package',
                    'Private beach access',
                    'Guided snorkeling tours',
                    'Daily breakfast and dinner',
                    'Airport transfers included'
                ],
                'created_at': datetime.utcnow()
            },
            {
                'name': 'Mountain Retreat',
                'description': 'Experience the serenity of mountain landscapes with cozy lodges, hiking trails, and breathtaking views. Perfect for nature lovers.',
                'price': 899,
                'originalPrice': 1099,
                'discount': 18,
                'image': 'https://images.unsplash.com/photo-1486870591958-9b9d0d1dda99?ixlib=rb-4.0.3&auto=format&fit=crop&w=675&q=80',
                'features': [
                    '5 days, 4 nights stay',
                    'Luxury mountain cabin',
                    'Guided hiking trails',
                    'Spa and wellness services',
                    'Local cuisine experience',
                    'Photography workshop'
                ],
                'created_at': datetime.utcnow()
            },
            {
                'name': 'European Adventure',
                'description': 'Discover the rich history and vibrant culture of Europe\'s most beautiful cities. An unforgettable journey through time.',
                'price': 1899,
                'originalPrice': 2299,
                'discount': 17,
                'image': 'https://images.unsplash.com/photo-1519677100203-a0e668c92439?ixlib=rb-4.0.3&auto=format&fit=crop&w=675&q=80',
                'features': [
                    '10 days, 9 nights tour',
                    'Visit 3 countries',
                    'Professional tour guides',
                    'Premium hotel accommodations',
                    'Museum and attraction tickets',
                    'High-speed train travel'
                ],
                'created_at': datetime.utcnow()
            },
            {
                'name': 'Desert Safari',
                'description': 'Experience the magic of the desert with camel rides, traditional camps, and stunning sunsets. An adventure like no other.',
                'price': 799,
                'originalPrice': 999,
                'discount': 20,
                'image': 'https://images.unsplash.com/photo-1509316975850-ff9c5deb0cd9?ixlib=rb-4.0.3&auto=format&fit=crop&w=675&q=80',
                'features': [
                    '4 days, 3 nights experience',
                    'Luxury desert camp',
                    'Camel trekking adventure',
                    'Traditional Bedouin dinner',
                    'Star gazing sessions',
                    '4WD desert exploration'
                ],
                'created_at': datetime.utcnow()
            },
            {
                'name': 'City Explorer',
                'description': 'Dive into the urban jungle with guided city tours, cultural experiences, and modern attractions. Perfect for city lovers.',
                'price': 699,
                'originalPrice': 849,
                'discount': 18,
                'image': 'https://images.unsplash.com/photo-1449824913935-59a10b8d2000?ixlib=rb-4.0.3&auto=format&fit=crop&w=675&q=80',
                'features': [
                    '3 days, 2 nights stay',
                    'Boutique hotel accommodation',
                    'City walking tours',
                    'Local food experiences',
                    'Museum and gallery visits',
                    'Shopping district access'
                ],
                'created_at': datetime.utcnow()
            },
            {
                'name': 'Island Hopping',
                'description': 'Explore multiple tropical islands with boat tours, water sports, and beachside relaxation. The ultimate island experience.',
                'price': 1599,
                'originalPrice': 1999,
                'discount': 20,
                'image': 'https://images.unsplash.com/photo-1559827260-dc66d52bef19?ixlib=rb-4.0.3&auto=format&fit=crop&w=675&q=80',
                'features': [
                    '8 days, 7 nights adventure',
                    'Visit 4 different islands',
                    'Private boat transfers',
                    'Water sports equipment',
                    'Beachfront accommodations',
                    'Island hopping guide'
                ],
                'created_at': datetime.utcnow()
            }
        ]
        
        mongo.db.packages.insert_many(sample_packages)
        
        # Create sample bookings
        packages = list(mongo.db.packages.find())
        users = list(mongo.db.users.find())
        
        sample_bookings = [
            {
                'user_id': str(users[1]['_id']),  # Test user
                'package_id': str(packages[0]['_id']),
                'destination': packages[0]['name'],
                'guests': 2,
                'check_in': '2024-07-15',
                'check_out': '2024-07-22',
                'status': 'confirmed',
                'created_at': datetime.utcnow() - timedelta(days=5)
            },
            {
                'user_id': str(users[1]['_id']),  # Test user
                'package_id': str(packages[1]['_id']),
                'destination': packages[1]['name'],
                'guests': 1,
                'check_in': '2024-08-01',
                'check_out': '2024-08-05',
                'status': 'pending',
                'created_at': datetime.utcnow() - timedelta(days=2)
            }
        ]
        
        mongo.db.bookings.insert_many(sample_bookings)
        
        # Create site settings
        settings = {
            'siteName': 'Travel Explorer',
            'contactEmail': 'info@travelexplorer.com',
            'phone': '+1 (555) 123-4567',
            'address': '123 Adventure Lane, Travel City, TC 12345',
            'description': 'Your gateway to amazing travel experiences around the world.',
            'socialMedia': {
                'facebook': 'https://facebook.com/travelexplorer',
                'twitter': 'https://twitter.com/travelexplorer',
                'instagram': 'https://instagram.com/travelexplorer'
            },
            'created_at': datetime.utcnow()
        }
        mongo.db.settings.insert_one(settings)
        
        return jsonify({
            'message': 'Database seeded successfully',
            'data': {
                'users_created': 2,
                'packages_created': len(sample_packages),
                'bookings_created': len(sample_bookings),
                'admin_credentials': {
                    'email': 'admin@example.com',
                    'password': 'admin123'
                }
            }
        }), 201
    
    except Exception as e:
        return jsonify({'message': 'Failed to seed database', 'error': str(e)}), 500

# Clear database route (for development)
@app.route('/api/clear-db', methods=['DELETE'])
def clear_database():
    try:
        # Only allow in development mode
        if os.environ.get('FLASK_ENV') != 'development':
            return jsonify({'message': 'This endpoint is only available in development mode'}), 403
        
        # Clear all collections
        mongo.db.users.delete_many({})
        mongo.db.packages.delete_many({})
        mongo.db.bookings.delete_many({})
        mongo.db.settings.delete_many({})
        
        return jsonify({'message': 'Database cleared successfully'}), 200
    
    except Exception as e:
        return jsonify({'message': 'Failed to clear database', 'error': str(e)}), 500

# Health check route
@app.route('/api/health', methods=['GET'])
def health_check():
    try:
        # Test database connection
        mongo.db.command('ping')
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'timestamp': datetime.utcnow().isoformat()
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'database': 'disconnected',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'message': 'Endpoint not found'}), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({'message': 'Method not allowed'}), 405

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'message': 'Internal server error'}), 500

if __name__ == '__main__':
    # Set environment variable for development
    os.environ['FLASK_ENV'] = 'development'
    app.run(debug=True, host='0.0.0.0', port=5000)