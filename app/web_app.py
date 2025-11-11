"""
Web application module for Project Firefly
Provides admin interface for whitelist management
"""

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
import os

from app.auth import User
from app.database import (
    add_to_whitelist, remove_from_whitelist, get_whitelist,
    toggle_whitelist_entry, get_recent_logs, get_stats,
    get_logs_by_domain, get_all_config, set_config
)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'firefly-secret-key-change-in-production')

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'


@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login"""
    return User.get(user_id)


# Routes
@app.route('/')
def index():
    """Redirect to dashboard or login"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.authenticate(username, password)

        if user:
            login_user(user)
            flash('Successfully logged in!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page if next_page else url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    """Logout user"""
    logout_user()
    flash('Successfully logged out', 'success')
    return redirect(url_for('login'))


@app.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard"""
    stats = get_stats()
    recent_logs = get_recent_logs(limit=20)
    return render_template('dashboard.html', stats=stats, recent_logs=recent_logs)


@app.route('/whitelist')
@login_required
def whitelist():
    """Whitelist management page"""
    domains = get_whitelist(enabled_only=False)
    return render_template('whitelist.html', domains=domains)


@app.route('/whitelist/add', methods=['POST'])
@login_required
def add_domain():
    """Add domain to whitelist"""
    domain = request.form.get('domain', '').strip().lower()
    description = request.form.get('description', '').strip()

    if not domain:
        flash('Domain cannot be empty', 'error')
        return redirect(url_for('whitelist'))

    if add_to_whitelist(domain, description, current_user.username):
        flash(f'Domain "{domain}" added to whitelist', 'success')
    else:
        flash(f'Domain "{domain}" already exists in whitelist', 'error')

    return redirect(url_for('whitelist'))


@app.route('/whitelist/remove/<domain>', methods=['POST'])
@login_required
def remove_domain(domain):
    """Remove domain from whitelist"""
    if remove_from_whitelist(domain):
        flash(f'Domain "{domain}" removed from whitelist', 'success')
    else:
        flash(f'Domain "{domain}" not found', 'error')

    return redirect(url_for('whitelist'))


@app.route('/whitelist/toggle/<domain>', methods=['POST'])
@login_required
def toggle_domain(domain):
    """Enable/disable domain in whitelist"""
    if toggle_whitelist_entry(domain):
        flash(f'Domain "{domain}" toggled', 'success')
    else:
        flash(f'Domain "{domain}" not found', 'error')

    return redirect(url_for('whitelist'))


@app.route('/logs')
@login_required
def logs():
    """DNS query logs page"""
    page = request.args.get('page', 1, type=int)
    limit = 50
    offset = (page - 1) * limit

    search = request.args.get('search', '').strip()

    if search:
        log_entries = get_logs_by_domain(search, limit=limit)
    else:
        log_entries = get_recent_logs(limit=limit, offset=offset)

    return render_template('logs.html', logs=log_entries, page=page, search=search)


@app.route('/settings')
@login_required
def settings():
    """Settings page"""
    config = get_all_config()
    return render_template('settings.html', config=config)


@app.route('/settings/update', methods=['POST'])
@login_required
def update_settings():
    """Update settings"""
    config_keys = ['upstream_dns', 'block_response', 'log_retention_days']

    for key in config_keys:
        value = request.form.get(key)
        if value:
            set_config(key, value)

    flash('Settings updated successfully', 'success')
    return redirect(url_for('settings'))


# API endpoints for AJAX requests
@app.route('/api/stats')
@login_required
def api_stats():
    """Get statistics as JSON"""
    return jsonify(get_stats())


@app.route('/api/whitelist')
@login_required
def api_whitelist():
    """Get whitelist as JSON"""
    return jsonify(get_whitelist())


@app.route('/api/logs')
@login_required
def api_logs():
    """Get recent logs as JSON"""
    limit = request.args.get('limit', 20, type=int)
    logs = get_recent_logs(limit=limit)
    return jsonify(logs)


# Error handlers
@app.errorhandler(404)
def not_found(error):
    """404 error handler"""
    return render_template('error.html', error='Page not found', code=404), 404


@app.errorhandler(500)
def internal_error(error):
    """500 error handler"""
    return render_template('error.html', error='Internal server error', code=500), 500


def create_app():
    """Application factory"""
    return app
