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
    get_logs_by_domain, get_all_config, set_config,
    # Profile operations
    create_profile, get_all_profiles, get_profile, update_profile,
    get_profile_stats,
    # Device operations
    get_all_devices, get_device_by_ip, update_device_profile, register_device,
    # Profile whitelist operations
    add_to_profile_whitelist, remove_from_profile_whitelist, get_profile_whitelist,
    toggle_profile_whitelist_entry, copy_whitelist_to_profile
)
from app.device_manager import clear_device_cache

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


# Profile management routes
@app.route('/profiles')
@login_required
def profiles():
    """List all profiles"""
    all_profiles = get_all_profiles(enabled_only=False)
    return render_template('profiles.html', profiles=all_profiles)


@app.route('/profiles/new', methods=['GET', 'POST'])
@login_required
def new_profile():
    """Create a new profile"""
    if request.method == 'POST':
        name = request.form.get('name')
        age = request.form.get('age', type=int)
        color = request.form.get('color', '#3B82F6')
        enabled = request.form.get('enabled') == '1'
        is_default = request.form.get('is_default') == '1'

        if not name:
            flash('Profile name is required', 'error')
            return redirect(url_for('new_profile'))

        profile_id = create_profile(name, age, color, is_default=is_default, enabled=enabled)
        flash(f'Profile "{name}" created successfully!', 'success')
        return redirect(url_for('profile_detail', profile_id=profile_id))

    return render_template('profile_form.html', profile=None)


@app.route('/profiles/<int:profile_id>')
@login_required
def profile_detail(profile_id):
    """Profile detail page"""
    profile = get_profile(profile_id)
    if not profile:
        flash('Profile not found', 'error')
        return redirect(url_for('profiles'))

    stats = get_profile_stats(profile_id)
    whitelist = get_profile_whitelist(profile_id, enabled_only=False)
    all_profiles = get_all_profiles(enabled_only=False)
    return render_template('profile_detail.html', profile=profile, stats=stats, whitelist=whitelist, all_profiles=all_profiles)


@app.route('/profiles/<int:profile_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_profile(profile_id):
    """Edit a profile"""
    profile = get_profile(profile_id)
    if not profile:
        flash('Profile not found', 'error')
        return redirect(url_for('profiles'))

    if request.method == 'POST':
        name = request.form.get('name')
        age = request.form.get('age', type=int)
        color = request.form.get('color')
        enabled = request.form.get('enabled') == '1'
        is_default = request.form.get('is_default') == '1'

        update_profile(profile_id, name=name, age=age, color=color, enabled=enabled, is_default=is_default)
        flash(f'Profile "{name}" updated successfully!', 'success')
        return redirect(url_for('profile_detail', profile_id=profile_id))

    return render_template('profile_form.html', profile=profile)


@app.route('/profiles/<int:profile_id>/delete', methods=['POST'])
@login_required
def delete_profile(profile_id):
    """Delete a profile"""
    from app.database import delete_profile as db_delete_profile
    profile = get_profile(profile_id)
    if profile:
        db_delete_profile(profile_id)
        clear_device_cache()  # Clear cache since profile assignments changed
        flash(f'Profile "{profile["name"]}" deleted', 'success')
    else:
        flash('Profile not found', 'error')

    return redirect(url_for('profiles'))


# Profile whitelist routes
@app.route('/profiles/<int:profile_id>/whitelist/add', methods=['POST'])
@login_required
def add_profile_domain(profile_id):
    """Add domain to profile whitelist"""
    domain = request.form.get('domain', '').strip().lower()
    description = request.form.get('description', '').strip()

    if not domain:
        flash('Domain cannot be empty', 'error')
        return redirect(url_for('profile_detail', profile_id=profile_id))

    if add_to_profile_whitelist(profile_id, domain, description, current_user.username):
        flash(f'Domain "{domain}" added to whitelist', 'success')
    else:
        flash(f'Domain "{domain}" already exists in whitelist', 'error')

    return redirect(url_for('profile_detail', profile_id=profile_id))


@app.route('/profiles/<int:profile_id>/whitelist/remove/<domain>', methods=['POST'])
@login_required
def remove_profile_domain(profile_id, domain):
    """Remove domain from profile whitelist"""
    if remove_from_profile_whitelist(profile_id, domain):
        flash(f'Domain "{domain}" removed from whitelist', 'success')
    else:
        flash(f'Domain "{domain}" not found', 'error')

    return redirect(url_for('profile_detail', profile_id=profile_id))


@app.route('/profiles/<int:profile_id>/whitelist/toggle/<domain>', methods=['POST'])
@login_required
def toggle_profile_domain(profile_id, domain):
    """Toggle domain in profile whitelist"""
    if toggle_profile_whitelist_entry(profile_id, domain):
        flash(f'Domain "{domain}" toggled', 'success')
    else:
        flash(f'Domain "{domain}" not found', 'error')

    return redirect(url_for('profile_detail', profile_id=profile_id))


@app.route('/profiles/<int:profile_id>/whitelist/copy', methods=['POST'])
@login_required
def copy_whitelist(profile_id):
    """Copy whitelist to another profile"""
    target_profile_id = request.form.get('target_profile_id', type=int)

    if not target_profile_id:
        flash('Please select a target profile', 'error')
        return redirect(url_for('profile_detail', profile_id=profile_id))

    count = copy_whitelist_to_profile(profile_id, target_profile_id)
    flash(f'Copied {count} domains to target profile', 'success')
    return redirect(url_for('profile_detail', profile_id=profile_id))


# Device management routes
@app.route('/devices')
@login_required
def devices():
    """List all devices"""
    all_devices = get_all_devices()
    all_profiles = get_all_profiles()
    return render_template('devices.html', devices=all_devices, profiles=all_profiles)


@app.route('/devices/<int:device_id>/assign', methods=['POST'])
@login_required
def assign_device(device_id):
    """Assign device to profile"""
    profile_id = request.form.get('profile_id', type=int)

    if update_device_profile(device_id, profile_id):
        clear_device_cache()  # Clear cache so new assignment takes effect
        flash('Device assigned to profile', 'success')
    else:
        flash('Failed to assign device', 'error')

    return redirect(url_for('devices'))


@app.route('/devices/<int:device_id>/delete', methods=['POST'])
@login_required
def delete_device(device_id):
    """Delete a device"""
    from app.database import delete_device as db_delete_device
    if db_delete_device(device_id):
        clear_device_cache()
        flash('Device deleted', 'success')
    else:
        flash('Device not found', 'error')

    return redirect(url_for('devices'))


@app.route('/devices/register', methods=['POST'])
@login_required
def register_device_manual():
    """Manually register a new device"""
    name = request.form.get('name', '').strip()
    ip_address = request.form.get('ip_address', '').strip()
    profile_id = request.form.get('profile_id', type=int)

    if not name or not ip_address:
        flash('Device name and IP address are required', 'error')
        return redirect(url_for('devices'))

    device_id = register_device(name, ip_address, profile_id)
    if device_id:
        clear_device_cache()
        flash(f'Device "{name}" registered successfully', 'success')
    else:
        flash('Failed to register device (IP address may already exist)', 'error')

    return redirect(url_for('devices'))


# API endpoints for profiles
@app.route('/api/profiles')
@login_required
def api_profiles():
    """Get all profiles as JSON"""
    return jsonify(get_all_profiles())


@app.route('/api/profile/<int:profile_id>/stats')
@login_required
def api_profile_stats(profile_id):
    """Get profile statistics as JSON"""
    return jsonify(get_profile_stats(profile_id))


@app.route('/api/devices')
@login_required
def api_devices():
    """Get all devices as JSON"""
    return jsonify(get_all_devices())


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
