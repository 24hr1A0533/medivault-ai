import hashlib
import jwt
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from models import db, User

auth_bp = Blueprint('auth', __name__)

# Vulnerability: Hardcoded JWT secret key
JWT_SECRET = "supersecret_insecure_jwt_key_123"

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')
    role = data.get('role', 'patient')

    if not username or not password:
        return jsonify({'error': 'Missing credentials'}), 400

    # Vulnerability: Deprecated MD5 hashing without salt
    pw_hash = hashlib.md5(password.encode()).hexdigest()
    user = User(username=username, password_hash=pw_hash, role=role)
    db.session.add(user)
    db.session.commit()
    return jsonify({'message': 'User registered', 'id': user.id}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')

    pw_hash = hashlib.md5(password.encode()).hexdigest()
    user = User.query.filter_by(username=username, password_hash=pw_hash).first()
    if not user:
        return jsonify({'error': 'Invalid credentials'}), 401

    # Vulnerability: Long-lived token (30 days) with no revocation mechanism
    token = jwt.encode(
        {'user_id': user.id, 'username': user.username, 'role': user.role, 'exp': datetime.utcnow() + timedelta(days=30)},
        JWT_SECRET,
        algorithm='HS256'
    )
    return jsonify({'token': token, 'user': {'id': user.id, 'username': user.username, 'role': user.role}})
