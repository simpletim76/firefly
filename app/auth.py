"""
Authentication module for Project Firefly
Handles user authentication and session management
"""

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash
from app.database import get_user_by_username, update_last_login


class User(UserMixin):
    """User class for Flask-Login"""

    def __init__(self, user_data):
        """
        Initialize user object

        Args:
            user_data: Dictionary containing user data from database
        """
        self.id = user_data['id']
        self.username = user_data['username']
        self.password_hash = user_data['password_hash']

    @staticmethod
    def get(user_id):
        """
        Get user by ID

        Args:
            user_id: User ID

        Returns:
            User object or None
        """
        # For simplicity, we'll load by username since we only have one user
        # In production, you'd query by ID
        user_data = get_user_by_username('admin')
        if user_data and user_data['id'] == int(user_id):
            return User(user_data)
        return None

    @staticmethod
    def authenticate(username, password):
        """
        Authenticate user with username and password

        Args:
            username: Username
            password: Plain text password

        Returns:
            User object if authentication successful, None otherwise
        """
        user_data = get_user_by_username(username)

        if not user_data:
            return None

        # Check password
        if check_password_hash(user_data['password_hash'], password):
            update_last_login(username)
            return User(user_data)

        return None

    def __repr__(self):
        return f'<User {self.username}>'


def hash_password(password):
    """
    Hash a password for storage

    Args:
        password: Plain text password

    Returns:
        Password hash
    """
    return generate_password_hash(password)
