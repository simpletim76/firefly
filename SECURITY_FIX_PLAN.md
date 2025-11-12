# Project Firefly - Security Fix Implementation Plan

**Created:** 2025-11-12
**Target Completion:** 2025-12-15
**Status:** 🟡 In Progress

---

## Executive Summary

This implementation plan addresses 11 security vulnerabilities and 6 efficiency issues identified in the comprehensive code review. The plan is divided into 4 phases over 6 weeks, with critical security fixes prioritized in Phase 1.

**Timeline:**
- **Phase 1 (Week 1):** Critical Security Fixes - 5 issues
- **Phase 2 (Week 2-3):** High Priority Security & Core Improvements - 4 issues
- **Phase 3 (Week 4-5):** Medium Priority & Performance - 4 issues
- **Phase 4 (Week 6):** Low Priority & Final Hardening - 4 issues

**Total Estimated Effort:** 25-30 developer days

---

## Table of Contents

1. [Phase 1: Critical Security Fixes](#phase-1-critical-security-fixes-week-1)
2. [Phase 2: High Priority Security](#phase-2-high-priority-security-week-2-3)
3. [Phase 3: Medium Priority & Performance](#phase-3-medium-priority--performance-week-4-5)
4. [Phase 4: Final Hardening](#phase-4-final-hardening-week-6)
5. [Dependencies & Packages](#dependencies--packages)
6. [Testing Strategy](#testing-strategy)
7. [Rollout Plan](#rollout-plan)
8. [Success Metrics](#success-metrics)

---

## Phase 1: Critical Security Fixes (Week 1)

**Goal:** Fix critical vulnerabilities that could lead to immediate compromise
**Duration:** 5 days
**Effort:** 3-4 developer days

### Task 1.1: Fix Open Redirect Vulnerability ⚠️ CRITICAL

**Priority:** P0 - Critical
**Effort:** 2 hours
**Risk:** High - Phishing attacks, credential theft

**Files to Modify:**
- `app/web_app.py`

**Implementation Steps:**

1. **Add URL validation helper function**
   ```python
   # Add to app/web_app.py after imports
   from urllib.parse import urlparse, urljoin

   def is_safe_url(target):
       """
       Validate that a redirect URL is safe (same domain)

       Args:
           target: URL to validate

       Returns:
           bool: True if URL is safe to redirect to
       """
       if not target:
           return False

       ref_url = urlparse(request.host_url)
       test_url = urlparse(urljoin(request.host_url, target))

       # Only allow http/https and same domain
       return (test_url.scheme in ('http', 'https') and
               ref_url.netloc == test_url.netloc)
   ```

2. **Update login route to validate next parameter**
   ```python
   # Replace lines 59-60 in app/web_app.py
   @app.route('/login', methods=['GET', 'POST'])
   def login():
       if current_user.is_authenticated:
           return redirect(url_for('dashboard'))

       if request.method == 'POST':
           username = request.form.get('username')
           password = request.form.get('password')

           user = User.authenticate(username, password)

           if user:
               login_user(user)
               flash('Successfully logged in!', 'success')

               # SECURITY FIX: Validate next parameter to prevent open redirect
               next_page = request.args.get('next')
               if next_page and not is_safe_url(next_page):
                   logger.warning(f"Blocked unsafe redirect to: {next_page}")
                   next_page = None

               return redirect(next_page if next_page else url_for('dashboard'))
           else:
               flash('Invalid username or password', 'error')

       return render_template('login.html')
   ```

3. **Add logging for blocked redirects**
   - Already included in code above

**Testing:**
```bash
# Test 1: Valid internal redirect
curl -X POST http://localhost:8080/login?next=/dashboard \
  -d "username=admin&password=admin123"
# Expected: Redirect to /dashboard

# Test 2: Blocked external redirect
curl -X POST http://localhost:8080/login?next=https://evil.com \
  -d "username=admin&password=admin123"
# Expected: Redirect to /dashboard (blocked)

# Test 3: Blocked protocol redirect
curl -X POST http://localhost:8080/login?next=javascript:alert(1) \
  -d "username=admin&password=admin123"
# Expected: Redirect to /dashboard (blocked)
```

**Verification:**
- [ ] Code changes implemented
- [ ] Manual testing completed
- [ ] Security audit logs show blocked attempts
- [ ] No broken redirects for legitimate flows

---

### Task 1.2: Add CSRF Protection ⚠️ HIGH

**Priority:** P0 - Critical
**Effort:** 4 hours
**Risk:** High - Cross-site request forgery attacks

**Files to Modify:**
- `requirements.txt`
- `app/web_app.py`
- `app/templates/login.html`
- `app/templates/whitelist.html`
- `app/templates/settings.html`

**Implementation Steps:**

1. **Add flask-wtf dependency**
   ```bash
   # Add to requirements.txt
   echo "flask-wtf==1.2.1" >> requirements.txt
   ```

2. **Initialize CSRF protection in web_app.py**
   ```python
   # Add import at top of app/web_app.py
   from flask_wtf.csrf import CSRFProtect, CSRFError

   # After app initialization (around line 19)
   app = Flask(__name__)
   app.secret_key = os.getenv('SECRET_KEY', 'firefly-secret-key-change-in-production')

   # Initialize CSRF protection
   csrf = CSRFProtect(app)

   # Configure CSRF
   app.config['WTF_CSRF_TIME_LIMIT'] = None  # No time limit
   app.config['WTF_CSRF_SSL_STRICT'] = False  # Allow HTTP in dev
   ```

3. **Add CSRF error handler**
   ```python
   # Add after existing error handlers in app/web_app.py
   @app.errorhandler(CSRFError)
   def handle_csrf_error(e):
       """Handle CSRF validation errors"""
       logger.warning(f"CSRF validation failed: {e.description}")
       flash('Security validation failed. Please try again.', 'error')
       return redirect(url_for('login')), 400
   ```

4. **Update login.html template**
   ```html
   <!-- Replace form in app/templates/login.html -->
   <form method="POST" action="{{ url_for('login') }}">
       <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>

       <div class="form-group">
           <label for="username">Username</label>
           <input type="text" id="username" name="username" required autofocus>
       </div>

       <div class="form-group">
           <label for="password">Password</label>
           <input type="password" id="password" name="password" required>
       </div>

       <button type="submit" class="btn btn-primary btn-block">Login</button>
   </form>
   ```

5. **Update whitelist.html template**
   ```html
   <!-- Update add domain form -->
   <form method="POST" action="{{ url_for('add_domain') }}" class="form-inline">
       <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
       <!-- rest of form -->
   </form>

   <!-- Update toggle form -->
   <form method="POST" action="{{ url_for('toggle_domain', domain=domain.domain) }}" style="display: inline;">
       <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
       <button type="submit" class="btn btn-sm btn-warning">
           {% if domain.enabled %}Disable{% else %}Enable{% endif %}
       </button>
   </form>

   <!-- Update remove form -->
   <form method="POST" action="{{ url_for('remove_domain', domain=domain.domain) }}" style="display: inline;">
       <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
       <button type="submit" class="btn btn-sm btn-danger" onclick="return confirm('Remove {{ domain.domain }}?')">Remove</button>
   </form>
   ```

6. **Update settings.html template**
   ```html
   <!-- Update settings form -->
   <form method="POST" action="{{ url_for('update_settings') }}">
       <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
       <!-- rest of form -->
   </form>
   ```

**Testing:**
```python
# tests/test_csrf.py
import pytest
from app.web_app import create_app

def test_csrf_protection_on_login():
    """Test that login requires CSRF token"""
    app = create_app()
    client = app.test_client()

    # Attempt login without CSRF token
    response = client.post('/login', data={
        'username': 'admin',
        'password': 'admin123'
    })

    assert response.status_code == 400
    assert b'CSRF' in response.data or b'Security validation failed' in response.data

def test_csrf_protection_on_whitelist():
    """Test that whitelist operations require CSRF token"""
    app = create_app()
    client = app.test_client()

    # Login first (with CSRF)
    with client.session_transaction() as sess:
        sess['_user_id'] = '1'

    # Attempt to add domain without CSRF token
    response = client.post('/whitelist/add', data={
        'domain': 'evil.com'
    })

    assert response.status_code == 400
```

**Verification:**
- [ ] CSRF tokens generated on all forms
- [ ] Requests without CSRF tokens are rejected
- [ ] Error messages don't expose internal details
- [ ] All existing functionality still works

---

### Task 1.3: Implement Authentication Rate Limiting ⚠️ HIGH

**Priority:** P0 - Critical
**Effort:** 3 hours
**Risk:** High - Brute force attacks

**Files to Modify:**
- `requirements.txt`
- `app/web_app.py`

**Implementation Steps:**

1. **Add flask-limiter dependency**
   ```bash
   # Add to requirements.txt
   echo "flask-limiter==3.5.0" >> requirements.txt
   ```

2. **Initialize rate limiter**
   ```python
   # Add import at top of app/web_app.py
   from flask_limiter import Limiter
   from flask_limiter.util import get_remote_address

   # After CSRF initialization
   limiter = Limiter(
       app=app,
       key_func=get_remote_address,
       default_limits=["200 per day", "50 per hour"],
       storage_uri="memory://",  # Use memory storage (Redis recommended for production)
       strategy="fixed-window"
   )

   # Configure rate limit headers
   app.config['RATELIMIT_HEADERS_ENABLED'] = True
   ```

3. **Apply rate limits to sensitive endpoints**
   ```python
   # Update login route
   @app.route('/login', methods=['GET', 'POST'])
   @limiter.limit("5 per minute")  # Max 5 login attempts per minute
   @limiter.limit("20 per hour")   # Max 20 login attempts per hour
   def login():
       # existing code
       pass

   # Add rate limit to API endpoints
   @app.route('/api/stats')
   @login_required
   @limiter.limit("60 per minute")
   def api_stats():
       # existing code
       pass

   @app.route('/api/whitelist')
   @login_required
   @limiter.limit("30 per minute")
   def api_whitelist():
       # existing code
       pass

   @app.route('/api/logs')
   @login_required
   @limiter.limit("30 per minute")
   def api_logs():
       # existing code
       pass
   ```

4. **Add custom rate limit handler**
   ```python
   # Add after error handlers in app/web_app.py
   @app.errorhandler(429)
   def ratelimit_handler(e):
       """Handle rate limit exceeded errors"""
       logger.warning(f"Rate limit exceeded: {request.remote_addr} - {request.endpoint}")
       flash('Too many requests. Please try again later.', 'error')
       return render_template('error.html',
                            error='Too many requests',
                            code=429), 429
   ```

5. **Add monitoring for failed login attempts**
   ```python
   # Update login route to track failures
   @app.route('/login', methods=['GET', 'POST'])
   @limiter.limit("5 per minute")
   @limiter.limit("20 per hour")
   def login():
       if current_user.is_authenticated:
           return redirect(url_for('dashboard'))

       if request.method == 'POST':
           username = request.form.get('username')
           password = request.form.get('password')

           user = User.authenticate(username, password)

           if user:
               login_user(user)
               logger.info(f"Successful login: {username} from {request.remote_addr}")
               flash('Successfully logged in!', 'success')

               next_page = request.args.get('next')
               if next_page and not is_safe_url(next_page):
                   logger.warning(f"Blocked unsafe redirect to: {next_page}")
                   next_page = None

               return redirect(next_page if next_page else url_for('dashboard'))
           else:
               # SECURITY: Log failed login attempts
               logger.warning(f"Failed login attempt: {username} from {request.remote_addr}")
               flash('Invalid username or password', 'error')

       return render_template('login.html')
   ```

**Testing:**
```bash
# Test rate limiting
for i in {1..6}; do
  curl -X POST http://localhost:8080/login \
    -d "username=admin&password=wrong" \
    -v 2>&1 | grep -E "HTTP/|X-RateLimit"
  sleep 1
done

# Expected: First 5 requests return 200/302, 6th returns 429
```

**Verification:**
- [ ] Rate limiting active on login endpoint
- [ ] Rate limit headers present in responses
- [ ] Failed attempts logged with IP addresses
- [ ] Rate limits reset after time window
- [ ] Legitimate users not blocked

---

### Task 1.4: Validate and Enforce SECRET_KEY ⚠️ HIGH

**Priority:** P0 - Critical
**Effort:** 2 hours
**Risk:** High - Session hijacking

**Files to Modify:**
- `app/web_app.py`
- `config/config.py`
- `docker-compose.yml`
- `.env.example`

**Implementation Steps:**

1. **Update config.py with validation**
   ```python
   # Replace config/config.py
   """
   Configuration module for Project Firefly
   """

   import os
   import secrets
   import sys

   class Config:
       """Base configuration"""

       # Flask settings
       SECRET_KEY = os.getenv('SECRET_KEY')
       DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

       # Validate SECRET_KEY
       if not SECRET_KEY:
           env = os.getenv('FLASK_ENV', 'production')
           if env == 'production':
               print("ERROR: SECRET_KEY environment variable must be set in production!")
               print("Generate a secure key with: openssl rand -hex 32")
               sys.exit(1)
           else:
               # Generate random key for development only
               SECRET_KEY = secrets.token_hex(32)
               print(f"WARNING: Using auto-generated SECRET_KEY for development")
               print(f"SECRET_KEY={SECRET_KEY}")

       # Validate SECRET_KEY strength
       if len(SECRET_KEY) < 32:
           print("WARNING: SECRET_KEY should be at least 32 characters")

       # DNS settings
       DNS_HOST = os.getenv('DNS_HOST', '0.0.0.0')
       DNS_PORT = int(os.getenv('DNS_PORT', '53'))

       # Web settings
       WEB_HOST = os.getenv('WEB_HOST', '0.0.0.0')
       WEB_PORT = int(os.getenv('WEB_PORT', '8080'))

       # Database settings
       DB_PATH = os.getenv('DB_PATH', '/app/data/firefly.db')

       # Logging
       LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')


   class DevelopmentConfig(Config):
       """Development configuration"""
       DEBUG = True


   class ProductionConfig(Config):
       """Production configuration"""
       DEBUG = False


   # Configuration dictionary
   config = {
       'development': DevelopmentConfig,
       'production': ProductionConfig,
       'default': ProductionConfig
   }
   ```

2. **Update web_app.py to use validated config**
   ```python
   # Replace line 20 in app/web_app.py
   from config.config import Config

   # Initialize Flask app
   app = Flask(__name__)

   # Load configuration
   app.config.from_object(Config)
   app.secret_key = Config.SECRET_KEY  # Use validated SECRET_KEY
   ```

3. **Update docker-compose.yml**
   ```yaml
   # Remove hardcoded SECRET_KEY from docker-compose.yml line 32
   # Change this:
   # - SECRET_KEY=change-this-secret-key-in-production

   # To this:
   # - SECRET_KEY=${SECRET_KEY}
   ```

4. **Update .env.example with instructions**
   ```bash
   # Add to .env.example

   # Security (REQUIRED IN PRODUCTION)
   # Generate with: openssl rand -hex 32
   SECRET_KEY=your-randomly-generated-secret-key-here
   ```

5. **Create setup script to generate SECRET_KEY**
   ```bash
   # Create scripts/generate-secrets.sh
   cat > scripts/generate-secrets.sh << 'EOF'
   #!/bin/bash

   echo "=== Project Firefly - Secret Key Generator ==="
   echo ""

   # Generate SECRET_KEY
   SECRET_KEY=$(openssl rand -hex 32)

   echo "Generated SECRET_KEY:"
   echo "SECRET_KEY=$SECRET_KEY"
   echo ""

   # Check if .env exists
   if [ -f .env ]; then
       echo "WARNING: .env file already exists!"
       read -p "Overwrite SECRET_KEY in .env? (y/N) " -n 1 -r
       echo
       if [[ $REPLY =~ ^[Yy]$ ]]; then
           # Update SECRET_KEY in existing .env
           if grep -q "SECRET_KEY=" .env; then
               sed -i "s/SECRET_KEY=.*/SECRET_KEY=$SECRET_KEY/" .env
               echo "✓ Updated SECRET_KEY in .env"
           else
               echo "SECRET_KEY=$SECRET_KEY" >> .env
               echo "✓ Added SECRET_KEY to .env"
           fi
       fi
   else
       # Create new .env from example
       cp .env.example .env
       sed -i "s/SECRET_KEY=.*/SECRET_KEY=$SECRET_KEY/" .env
       echo "✓ Created .env with generated SECRET_KEY"
   fi

   echo ""
   echo "Keep this key secure! Add .env to .gitignore"
   EOF

   chmod +x scripts/generate-secrets.sh
   ```

**Testing:**
```bash
# Test 1: Application fails without SECRET_KEY in production
FLASK_ENV=production python run.py
# Expected: Error message and exit

# Test 2: Application generates key in development
FLASK_ENV=development python run.py
# Expected: Warning message with generated key

# Test 3: Application accepts valid SECRET_KEY
SECRET_KEY=$(openssl rand -hex 32) python run.py
# Expected: Normal startup
```

**Verification:**
- [ ] Application fails to start in production without SECRET_KEY
- [ ] Development mode generates and displays key
- [ ] Docker-compose.yml doesn't contain hardcoded key
- [ ] .env.example has clear instructions
- [ ] Generate script creates secure keys

---

### Task 1.5: Remove Hardcoded Default Password ⚠️ CRITICAL

**Priority:** P0 - Critical
**Effort:** 4 hours
**Risk:** Critical - Unauthorized access

**Files to Modify:**
- `app/database.py`
- `app/auth.py`
- `setup.py` (create new)
- `app/templates/login.html`

**Implementation Steps:**

1. **Remove hardcoded password hash from database.py**
   ```python
   # Replace lines 92-97 in app/database.py

   # Check if any users exist
   cursor.execute('SELECT COUNT(*) as count FROM users')
   user_count = cursor.fetchone()['count']

   if user_count == 0:
       # No users exist - generate random password
       import secrets
       import string

       # Generate secure random password
       alphabet = string.ascii_letters + string.digits + string.punctuation
       temp_password = ''.join(secrets.choice(alphabet) for _ in range(16))

       # Hash the password
       from app.auth import hash_password
       password_hash = hash_password(temp_password)

       # Insert admin user with generated password
       cursor.execute('''
           INSERT INTO users (username, password_hash)
           VALUES ('admin', ?)
       ''', (password_hash,))

       # Write password to secure file (not in version control)
       import os
       password_file = os.path.join(os.path.dirname(DB_PATH), 'initial_password.txt')
       try:
           with open(password_file, 'w') as f:
               f.write(f"Initial Admin Password\n")
               f.write(f"=====================\n\n")
               f.write(f"Username: admin\n")
               f.write(f"Password: {temp_password}\n\n")
               f.write(f"IMPORTANT: Change this password immediately after first login!\n")
               f.write(f"This file will be deleted after you change the password.\n")

           os.chmod(password_file, 0o600)  # Only owner can read

           print("=" * 70)
           print("🔐 INITIAL ADMIN PASSWORD GENERATED")
           print("=" * 70)
           print(f"Username: admin")
           print(f"Password: {temp_password}")
           print(f"\nPassword also saved to: {password_file}")
           print("IMPORTANT: Change this password immediately after first login!")
           print("=" * 70)

       except Exception as e:
           print(f"ERROR: Could not write password file: {e}")
           print(f"IMPORTANT: Save this password now: {temp_password}")
   else:
       print("✓ Users already exist, skipping initial user creation")
   ```

2. **Add password change functionality**
   ```python
   # Add to app/database.py

   def change_password(username: str, new_password: str) -> bool:
       """
       Change a user's password

       Args:
           username: Username
           new_password: New password (plain text)

       Returns:
           bool: True if password changed successfully
       """
       from app.auth import hash_password

       password_hash = hash_password(new_password)

       with get_db() as conn:
           cursor = conn.cursor()
           cursor.execute('''
               UPDATE users
               SET password_hash = ?
               WHERE username = ?
           ''', (password_hash, username))

           if cursor.rowcount > 0:
               # Delete initial password file if it exists
               import os
               password_file = os.path.join(os.path.dirname(DB_PATH), 'initial_password.txt')
               if os.path.exists(password_file):
                   try:
                       os.remove(password_file)
                       print(f"✓ Deleted initial password file")
                   except Exception as e:
                       print(f"Warning: Could not delete password file: {e}")
               return True

           return False


   def is_default_password(username: str) -> bool:
       """
       Check if user is still using initial password
       (by checking if initial_password.txt exists)

       Args:
           username: Username to check

       Returns:
           bool: True if still using initial password
       """
       import os
       password_file = os.path.join(os.path.dirname(DB_PATH), 'initial_password.txt')
       return os.path.exists(password_file)
   ```

3. **Add password change route to web_app.py**
   ```python
   # Add to app/web_app.py

   from app.database import change_password, is_default_password

   @app.route('/change-password', methods=['GET', 'POST'])
   @login_required
   def change_password_route():
       """Change password page"""
       if request.method == 'POST':
           current_password = request.form.get('current_password')
           new_password = request.form.get('new_password')
           confirm_password = request.form.get('confirm_password')

           # Validate current password
           user = User.authenticate(current_user.username, current_password)
           if not user:
               flash('Current password is incorrect', 'error')
               return redirect(url_for('change_password_route'))

           # Validate new password
           if len(new_password) < 12:
               flash('New password must be at least 12 characters', 'error')
               return redirect(url_for('change_password_route'))

           if new_password != confirm_password:
               flash('New passwords do not match', 'error')
               return redirect(url_for('change_password_route'))

           # Change password
           if change_password(current_user.username, new_password):
               flash('Password changed successfully!', 'success')
               logger.info(f"Password changed for user: {current_user.username}")
               return redirect(url_for('dashboard'))
           else:
               flash('Failed to change password', 'error')

       force_change = is_default_password(current_user.username)
       return render_template('change_password.html', force_change=force_change)


   @app.route('/dashboard')
   @login_required
   def dashboard():
       """Main dashboard"""
       # Check if user needs to change password
       if is_default_password(current_user.username):
           flash('⚠️ You are using the initial password. Please change it immediately!', 'warning')

       stats = get_stats()
       recent_logs = get_recent_logs(limit=20)
       return render_template('dashboard.html', stats=stats, recent_logs=recent_logs)
   ```

4. **Create change_password.html template**
   ```html
   <!-- Create app/templates/change_password.html -->
   {% extends "base.html" %}

   {% block title %}Change Password - Project Firefly{% endblock %}

   {% block content %}
   <div class="page-header">
       <h2>Change Password</h2>
       {% if force_change %}
       <div class="alert alert-warning">
           <strong>⚠️ Password Change Required</strong>
           <p>You are using the initial password. Please change it immediately for security.</p>
       </div>
       {% endif %}
   </div>

   <div class="section">
       <form method="POST" action="{{ url_for('change_password_route') }}">
           <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>

           <div class="form-group">
               <label for="current_password">Current Password</label>
               <input type="password" id="current_password" name="current_password" required autofocus>
           </div>

           <div class="form-group">
               <label for="new_password">New Password</label>
               <input type="password" id="new_password" name="new_password" required minlength="12">
               <small>Minimum 12 characters</small>
           </div>

           <div class="form-group">
               <label for="confirm_password">Confirm New Password</label>
               <input type="password" id="confirm_password" name="confirm_password" required minlength="12">
           </div>

           <button type="submit" class="btn btn-primary">Change Password</button>
           {% if not force_change %}
           <a href="{{ url_for('dashboard') }}" class="btn btn-secondary">Cancel</a>
           {% endif %}
       </form>
   </div>

   <div class="info-box">
       <h4>Password Requirements</h4>
       <ul>
           <li>Minimum 12 characters long</li>
           <li>Use a mix of letters, numbers, and symbols</li>
           <li>Avoid common words or patterns</li>
           <li>Don't reuse passwords from other accounts</li>
       </ul>
   </div>
   {% endblock %}
   ```

5. **Update login.html to remove default password display**
   ```html
   <!-- Remove lines 25-30 from app/templates/login.html -->
   <!-- DELETE this section:
   <div class="login-info">
       <p><strong>Default credentials:</strong></p>
       <p>Username: <code>admin</code></p>
       <p>Password: <code>admin123</code></p>
       <p class="warning">⚠️ Please change the default password after first login!</p>
   </div>
   -->
   ```

6. **Update base.html to add change password link**
   ```html
   <!-- Add to navigation in app/templates/base.html -->
   <nav>
       <a href="{{ url_for('dashboard') }}">Dashboard</a>
       <a href="{{ url_for('whitelist') }}">Whitelist</a>
       <a href="{{ url_for('logs') }}">Logs</a>
       <a href="{{ url_for('settings') }}">Settings</a>
       <a href="{{ url_for('change_password_route') }}">Change Password</a>
       <a href="{{ url_for('logout') }}">Logout</a>
   </nav>
   ```

**Testing:**
```bash
# Test 1: Fresh install generates random password
rm -f data/firefly.db data/initial_password.txt
python setup.py
cat data/initial_password.txt
# Expected: Random password displayed and saved

# Test 2: Password change works
# Login with initial password, go to /change-password, change it
# Expected: Password changed, initial_password.txt deleted

# Test 3: Second startup doesn't regenerate password
python setup.py
# Expected: "Users already exist" message
```

**Verification:**
- [ ] No hardcoded passwords in source code
- [ ] Random password generated on first install
- [ ] Password saved to file with restricted permissions
- [ ] Change password page functional
- [ ] Initial password file deleted after change
- [ ] Warning shown on dashboard if using initial password
- [ ] Login page doesn't show default credentials

---

### Phase 1 Completion Checklist

- [ ] All 5 critical tasks completed
- [ ] Code reviewed and tested
- [ ] Documentation updated
- [ ] Security scan passed
- [ ] Ready for Phase 2

**Deliverables:**
- Open redirect fixed
- CSRF protection enabled
- Rate limiting active
- SECRET_KEY validated
- Default password removed

---

## Phase 2: High Priority Security (Week 2-3)

**Goal:** Address high-severity security issues and add essential protections
**Duration:** 10 days
**Effort:** 8-10 developer days

### Task 2.1: Fix SQL Injection in LIKE Patterns

**Priority:** P1 - High
**Effort:** 2 hours
**Files:** `app/database.py`

**Implementation:**

```python
# Add helper function to app/database.py

def escape_like_pattern(pattern: str) -> str:
    """
    Escape special characters in LIKE patterns

    Args:
        pattern: Search pattern

    Returns:
        Escaped pattern safe for LIKE queries
    """
    # Escape backslash first, then wildcards
    pattern = pattern.replace('\\', '\\\\')
    pattern = pattern.replace('%', '\\%')
    pattern = pattern.replace('_', '\\_')
    return pattern


# Update get_logs_by_domain function (lines 200-210)
def get_logs_by_domain(domain: str, limit: int = 100) -> List[Dict]:
    """Get logs for a specific domain"""
    with get_db() as conn:
        cursor = conn.cursor()

        # SECURITY FIX: Escape LIKE special characters
        safe_domain = escape_like_pattern(domain.lower())

        cursor.execute('''
            SELECT * FROM dns_logs
            WHERE domain LIKE ? ESCAPE '\\'
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (f'%{safe_domain}%', limit))
        return [dict(row) for row in cursor.fetchall()]
```

**Testing:**
```python
# Test LIKE escaping
def test_like_pattern_escaping():
    # These should not cause errors or unexpected matches
    test_cases = [
        "example.com%",  # Should not match all domains
        "test_domain",   # Underscore should be literal
        "evil\\malicious",  # Backslash should be escaped
        "%' OR '1'='1",  # SQL injection attempt
    ]

    for domain in test_cases:
        results = get_logs_by_domain(domain)
        # Should return safe results without errors
        assert isinstance(results, list)
```

---

### Task 2.2: Add Input Validation Framework

**Priority:** P1 - High
**Effort:** 6 hours
**Files:** `app/validation.py` (new), `app/web_app.py`

**Implementation:**

```python
# Create app/validation.py

import re
from typing import Tuple

class ValidationError(Exception):
    """Validation error exception"""
    pass


def validate_domain(domain: str) -> Tuple[bool, str]:
    """
    Validate domain name format

    Args:
        domain: Domain name to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not domain:
        return False, "Domain cannot be empty"

    # Length check
    if len(domain) > 253:
        return False, "Domain name too long (max 253 characters)"

    # Valid domain regex
    # Allows letters, numbers, hyphens, and dots
    domain_pattern = r'^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)*[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$'

    if not re.match(domain_pattern, domain.lower()):
        return False, "Invalid domain format"

    # Check for malicious patterns
    if '..' in domain or domain.startswith('.') or domain.endswith('.'):
        return False, "Invalid domain format"

    return True, ""


def validate_ip_address(ip: str) -> Tuple[bool, str]:
    """
    Validate IP address format

    Args:
        ip: IP address to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not ip:
        return False, "IP address cannot be empty"

    # IPv4 pattern
    ipv4_pattern = r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'

    if not re.match(ipv4_pattern, ip):
        return False, "Invalid IP address format"

    return True, ""


def validate_config_value(key: str, value: str) -> Tuple[bool, str]:
    """
    Validate configuration values

    Args:
        key: Configuration key
        value: Configuration value

    Returns:
        Tuple of (is_valid, error_message)
    """
    validators = {
        'upstream_dns': validate_ip_address,
        'block_response': validate_ip_address,
        'log_retention_days': lambda v: (v.isdigit() and 1 <= int(v) <= 365,
                                        "Must be between 1 and 365 days"),
    }

    if key in validators:
        validator = validators[key]
        if callable(validator):
            result = validator(value)
            if isinstance(result, tuple):
                return result
            return result, ""

    return True, ""


def sanitize_input(text: str, max_length: int = 1000) -> str:
    """
    Sanitize user input by removing potentially dangerous characters

    Args:
        text: Input text to sanitize
        max_length: Maximum allowed length

    Returns:
        Sanitized text
    """
    if not text:
        return ""

    # Limit length
    text = text[:max_length]

    # Remove control characters except newline and tab
    text = ''.join(char for char in text if char.isprintable() or char in '\n\t')

    return text.strip()
```

**Update web_app.py to use validation:**

```python
# Add import
from app.validation import validate_domain, validate_config_value, sanitize_input, ValidationError

# Update add_domain route
@app.route('/whitelist/add', methods=['POST'])
@login_required
@limiter.limit("30 per minute")
def add_domain():
    """Add domain to whitelist"""
    domain = request.form.get('domain', '').strip().lower()
    description = sanitize_input(request.form.get('description', '').strip())

    # SECURITY: Validate domain format
    is_valid, error = validate_domain(domain)
    if not is_valid:
        flash(f'Invalid domain: {error}', 'error')
        return redirect(url_for('whitelist'))

    if add_to_whitelist(domain, description, current_user.username):
        flash(f'Domain "{domain}" added to whitelist', 'success')
        logger.info(f"Domain added: {domain} by {current_user.username}")
    else:
        flash(f'Domain "{domain}" already exists in whitelist', 'error')

    return redirect(url_for('whitelist'))


# Update update_settings route
@app.route('/settings/update', methods=['POST'])
@login_required
@limiter.limit("10 per minute")
def update_settings():
    """Update settings"""
    config_keys = ['upstream_dns', 'block_response', 'log_retention_days']

    for key in config_keys:
        value = request.form.get(key)
        if value:
            # SECURITY: Validate config values
            is_valid, error = validate_config_value(key, value)
            if not is_valid:
                flash(f'Invalid {key}: {error}', 'error')
                return redirect(url_for('settings'))

            set_config(key, value)
            logger.info(f"Config updated: {key}={value} by {current_user.username}")

    flash('Settings updated successfully', 'success')
    return redirect(url_for('settings'))
```

**Testing:**
```python
def test_domain_validation():
    assert validate_domain("example.com")[0] == True
    assert validate_domain("sub.example.com")[0] == True
    assert validate_domain("invalid..domain")[0] == False
    assert validate_domain("evil'; DROP TABLE--")[0] == False
    assert validate_domain("")[0] == False

def test_ip_validation():
    assert validate_ip_address("8.8.8.8")[0] == True
    assert validate_ip_address("192.168.1.1")[0] == True
    assert validate_ip_address("256.1.1.1")[0] == False
    assert validate_ip_address("not.an.ip")[0] == False
```

---

### Task 2.3: Add Security Headers

**Priority:** P1 - High
**Effort:** 3 hours
**Files:** `requirements.txt`, `app/web_app.py`

**Implementation:**

```bash
# Add to requirements.txt
flask-talisman==1.1.0
```

```python
# Add to app/web_app.py
from flask_talisman import Talisman

# After app initialization
# Configure security headers
Talisman(app,
    force_https=False,  # Set to True when behind HTTPS proxy
    strict_transport_security=True,
    strict_transport_security_max_age=31536000,  # 1 year
    content_security_policy={
        'default-src': "'self'",
        'script-src': "'self'",
        'style-src': "'self' 'unsafe-inline'",  # Allow inline styles for now
        'img-src': "'self' data:",
        'font-src': "'self'",
        'connect-src': "'self'",
        'frame-ancestors': "'none'",
    },
    content_security_policy_nonce_in=['script-src'],
    referrer_policy='strict-origin-when-cross-origin',
    feature_policy={
        'geolocation': "'none'",
        'microphone': "'none'",
        'camera': "'none'",
    }
)

# Add additional security headers
@app.after_request
def set_security_headers(response):
    """Add additional security headers to all responses"""
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'

    # Remove server header
    response.headers.pop('Server', None)

    return response
```

**Testing:**
```bash
# Test security headers
curl -I http://localhost:8080/
# Expected headers:
# X-Frame-Options: DENY
# X-Content-Type-Options: nosniff
# X-XSS-Protection: 1; mode=block
# Content-Security-Policy: default-src 'self'; ...
# Referrer-Policy: strict-origin-when-cross-origin
```

---

### Task 2.4: Harden Session Configuration

**Priority:** P1 - High
**Effort:** 1 hour
**Files:** `app/web_app.py`

**Implementation:**

```python
# Add to app/web_app.py after app initialization

# Session security configuration
app.config.update(
    # Session cookie security
    SESSION_COOKIE_SECURE=False,  # Set to True when using HTTPS
    SESSION_COOKIE_HTTPONLY=True,  # Prevent JavaScript access
    SESSION_COOKIE_SAMESITE='Lax',  # CSRF protection
    SESSION_COOKIE_NAME='firefly_session',  # Custom name

    # Session timeout (30 minutes)
    PERMANENT_SESSION_LIFETIME=1800,

    # Remember me cookie security
    REMEMBER_COOKIE_SECURE=False,  # Set to True when using HTTPS
    REMEMBER_COOKIE_HTTPONLY=True,
    REMEMBER_COOKIE_DURATION=86400,  # 24 hours
)

# Flask-Login configuration
login_manager.session_protection = "strong"  # Detect session tampering
login_manager.login_message_category = "info"
```

---

### Phase 2 Completion Checklist

- [ ] SQL LIKE injection fixed
- [ ] Input validation framework implemented
- [ ] Security headers configured
- [ ] Session configuration hardened
- [ ] All routes protected with rate limiting
- [ ] Comprehensive logging added

---

## Phase 3: Medium Priority & Performance (Week 4-5)

**Goal:** Improve performance and address medium-severity issues
**Duration:** 10 days
**Effort:** 10-12 developer days

### Task 3.1: Implement Whitelist Caching

**Priority:** P2 - Medium (High Performance Impact)
**Effort:** 8 hours
**Files:** `app/dns_server.py`, `requirements.txt`

**Implementation:**

```python
# Update app/dns_server.py

import time
from threading import Lock, Thread
from typing import Dict, Tuple, Set

class CachedWhitelistResolver(BaseResolver):
    """
    DNS resolver with cached whitelist lookups
    """

    def __init__(self, upstream_dns='8.8.8.8', block_ip='0.0.0.0', cache_ttl=60):
        """
        Initialize resolver with caching

        Args:
            upstream_dns: DNS server to forward queries to
            block_ip: IP to return for blocked domains
            cache_ttl: Cache time-to-live in seconds
        """
        self.upstream_dns = upstream_dns
        self.block_ip = block_ip
        self.cache_ttl = cache_ttl

        # Cache structure: {domain: (is_allowed, timestamp)}
        self.cache: Dict[str, Tuple[bool, float]] = {}
        self.cache_lock = Lock()

        # Full whitelist cache: Set of all whitelisted domains
        self.whitelist_cache: Set[str] = set()
        self.whitelist_timestamp = 0
        self.whitelist_lock = Lock()

        # Start cache refresh thread
        self.running = True
        self.refresh_thread = Thread(target=self._refresh_whitelist_cache, daemon=True)
        self.refresh_thread.start()

        logger.info(f"CachedWhitelistResolver initialized: cache_ttl={cache_ttl}s")

    def _refresh_whitelist_cache(self):
        """Background thread to refresh full whitelist cache"""
        while self.running:
            try:
                # Reload whitelist from database
                from app.database import get_whitelist
                domains = get_whitelist(enabled_only=True)

                with self.whitelist_lock:
                    self.whitelist_cache = {d['domain'].lower() for d in domains}
                    self.whitelist_timestamp = time.time()

                logger.debug(f"Whitelist cache refreshed: {len(self.whitelist_cache)} domains")

            except Exception as e:
                logger.error(f"Failed to refresh whitelist cache: {e}")

            # Refresh every 30 seconds
            time.sleep(30)

    def is_allowed(self, domain: str) -> bool:
        """
        Check if domain is allowed (with caching)

        Args:
            domain: Domain to check

        Returns:
            True if allowed, False otherwise
        """
        domain = domain.lower().rstrip('.')
        current_time = time.time()

        # Check per-domain cache first
        with self.cache_lock:
            if domain in self.cache:
                cached_result, cached_time = self.cache[domain]
                if current_time - cached_time < self.cache_ttl:
                    return cached_result

        # Cache miss - check whitelist
        result = self._check_whitelist(domain)

        # Update cache
        with self.cache_lock:
            self.cache[domain] = (result, current_time)

            # Limit cache size to prevent memory exhaustion
            if len(self.cache) > 10000:
                # Remove oldest 50% of entries
                sorted_items = sorted(
                    self.cache.items(),
                    key=lambda x: x[1][1]
                )
                self.cache = dict(sorted_items[-5000:])

        return result

    def _check_whitelist(self, domain: str) -> bool:
        """
        Check if domain is in whitelist (using cached whitelist)

        Args:
            domain: Domain to check

        Returns:
            True if whitelisted, False otherwise
        """
        with self.whitelist_lock:
            # Check exact match
            if domain in self.whitelist_cache:
                return True

            # Check parent domains
            parts = domain.split('.')
            for i in range(len(parts)):
                parent_domain = '.'.join(parts[i:])
                if parent_domain in self.whitelist_cache:
                    return True

        return False

    def clear_cache(self):
        """Clear all caches (call when whitelist is updated)"""
        with self.cache_lock:
            self.cache.clear()

        with self.whitelist_lock:
            self.whitelist_cache.clear()

        logger.info("Whitelist cache cleared")

    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        with self.cache_lock:
            cache_size = len(self.cache)

        with self.whitelist_lock:
            whitelist_size = len(self.whitelist_cache)
            cache_age = time.time() - self.whitelist_timestamp

        return {
            'query_cache_size': cache_size,
            'whitelist_cache_size': whitelist_size,
            'whitelist_cache_age': cache_age
        }

    # Keep existing resolve() and forward_to_upstream() methods
    def resolve(self, request, handler):
        """Resolve DNS query (unchanged)"""
        # ... existing implementation ...
        pass
```

**Update web_app.py to clear cache on whitelist changes:**

```python
# Add cache clearing to whitelist operations

@app.route('/whitelist/add', methods=['POST'])
@login_required
@limiter.limit("30 per minute")
def add_domain():
    """Add domain to whitelist"""
    # ... existing code ...

    if add_to_whitelist(domain, description, current_user.username):
        # Clear DNS server cache
        from app.dns_server import get_dns_server
        dns_server = get_dns_server()
        if dns_server and hasattr(dns_server.resolver, 'clear_cache'):
            dns_server.resolver.clear_cache()

        flash(f'Domain "{domain}" added to whitelist', 'success')
        logger.info(f"Domain added: {domain} by {current_user.username}")

    return redirect(url_for('whitelist'))


# Similarly for remove and toggle operations
```

**Testing:**
```python
def test_cache_performance():
    import time
    from app.dns_server import CachedWhitelistResolver

    resolver = CachedWhitelistResolver()

    # First query (cache miss)
    start = time.time()
    result1 = resolver.is_allowed('example.com')
    time1 = time.time() - start

    # Second query (cache hit)
    start = time.time()
    result2 = resolver.is_allowed('example.com')
    time2 = time.time() - start

    assert result1 == result2
    assert time2 < time1 / 10  # Should be >10x faster
```

---

### Task 3.2: Implement Async DNS Queries

**Priority:** P2 - Medium
**Effort:** 6 hours
**Files:** `app/dns_server.py`

**Implementation:**

```python
# Add to dns_server.py
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError

class AsyncWhitelistResolver(CachedWhitelistResolver):
    """
    DNS resolver with async upstream queries
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Thread pool for upstream queries
        self.executor = ThreadPoolExecutor(
            max_workers=20,
            thread_name_prefix='dns_upstream'
        )

        logger.info("Async DNS resolver initialized with 20 workers")

    def forward_to_upstream(self, request):
        """
        Forward DNS query to upstream asynchronously

        Args:
            request: DNS request object

        Returns:
            IP address or None
        """
        # Submit query to thread pool
        future = self.executor.submit(self._upstream_query, request)

        try:
            # Wait for result with timeout
            return future.result(timeout=0.5)  # 500ms timeout
        except FutureTimeoutError:
            logger.warning(f"Upstream DNS timeout for {request.q.qname}")
            return None
        except Exception as e:
            logger.error(f"Upstream DNS error: {e}")
            return None

    def _upstream_query(self, request):
        """
        Actual upstream query (runs in thread pool)

        Args:
            request: DNS request

        Returns:
            IP address or None
        """
        try:
            upstream_request = request.send(self.upstream_dns, 53, timeout=0.5)
            upstream_reply = DNSRecord.parse(upstream_request)

            for rr in upstream_reply.rr:
                if rr.rtype == QTYPE.A:
                    return str(rr.rdata)

            return None

        except socket.timeout:
            logger.debug(f"Upstream timeout: {request.q.qname}")
            return None
        except Exception as e:
            logger.error(f"Upstream query error: {e}")
            return None
```

---

### Task 3.3: Schedule Automated Log Cleanup

**Priority:** P2 - Medium
**Effort:** 3 hours
**Files:** `requirements.txt`, `run.py`

**Implementation:**

```bash
# Add to requirements.txt
schedule==1.2.0
```

```python
# Update run.py

import schedule
import threading

def cleanup_task():
    """Background task for scheduled maintenance"""
    from app.database import cleanup_old_logs, get_config

    while True:
        try:
            schedule.run_pending()
            time.sleep(3600)  # Check every hour
        except Exception as e:
            logger.error(f"Cleanup task error: {e}")


def schedule_maintenance():
    """Schedule periodic maintenance tasks"""
    from app.database import cleanup_old_logs, get_config

    # Schedule daily log cleanup at 3 AM
    def cleanup_logs():
        try:
            retention_days = int(get_config('log_retention_days') or '30')
            deleted = cleanup_old_logs(days=retention_days)
            logger.info(f"Scheduled cleanup removed {deleted} old log entries")
        except Exception as e:
            logger.error(f"Log cleanup failed: {e}")

    schedule.every().day.at("03:00").do(cleanup_logs)

    # Start cleanup thread
    cleanup_thread = threading.Thread(target=cleanup_task, daemon=True)
    cleanup_thread.start()

    logger.info("✓ Maintenance tasks scheduled")


# Update main() function
def main():
    """Main application entry point"""

    # ... existing initialization code ...

    # Schedule maintenance tasks
    schedule_maintenance()

    # ... rest of existing code ...
```

---

### Task 3.4: Add Password Complexity Requirements

**Priority:** P2 - Medium
**Effort:** 4 hours
**Files:** `app/validation.py`, `app/web_app.py`

**Implementation:**

```python
# Add to app/validation.py

import re
from typing import Tuple, List

def validate_password_strength(password: str) -> Tuple[bool, List[str]]:
    """
    Validate password strength

    Args:
        password: Password to validate

    Returns:
        Tuple of (is_valid, list of error messages)
    """
    errors = []

    # Length check
    if len(password) < 12:
        errors.append("Password must be at least 12 characters")

    # Uppercase check
    if not re.search(r'[A-Z]', password):
        errors.append("Password must contain at least one uppercase letter")

    # Lowercase check
    if not re.search(r'[a-z]', password):
        errors.append("Password must contain at least one lowercase letter")

    # Number check
    if not re.search(r'[0-9]', password):
        errors.append("Password must contain at least one number")

    # Special character check
    if not re.search(r'[^A-Za-z0-9]', password):
        errors.append("Password must contain at least one special character")

    # Common password check
    common_passwords = ['password', 'admin123', '12345678', 'qwerty', 'letmein']
    if password.lower() in common_passwords:
        errors.append("Password is too common")

    return len(errors) == 0, errors


def get_password_strength_indicator(password: str) -> str:
    """
    Get password strength indicator

    Args:
        password: Password to evaluate

    Returns:
        Strength level: weak, medium, strong, very strong
    """
    score = 0

    # Length scoring
    if len(password) >= 12:
        score += 1
    if len(password) >= 16:
        score += 1
    if len(password) >= 20:
        score += 1

    # Character variety
    if re.search(r'[a-z]', password):
        score += 1
    if re.search(r'[A-Z]', password):
        score += 1
    if re.search(r'[0-9]', password):
        score += 1
    if re.search(r'[^A-Za-z0-9]', password):
        score += 1

    # Multiple special chars
    if len(re.findall(r'[^A-Za-z0-9]', password)) >= 3:
        score += 1

    if score <= 3:
        return 'weak'
    elif score <= 5:
        return 'medium'
    elif score <= 6:
        return 'strong'
    else:
        return 'very_strong'
```

```python
# Update app/web_app.py change_password route

from app.validation import validate_password_strength

@app.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password_route():
    """Change password page"""
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        # Validate current password
        user = User.authenticate(current_user.username, current_password)
        if not user:
            flash('Current password is incorrect', 'error')
            return redirect(url_for('change_password_route'))

        # Validate password strength
        is_valid, errors = validate_password_strength(new_password)
        if not is_valid:
            for error in errors:
                flash(error, 'error')
            return redirect(url_for('change_password_route'))

        # Confirm passwords match
        if new_password != confirm_password:
            flash('New passwords do not match', 'error')
            return redirect(url_for('change_password_route'))

        # Change password
        if change_password(current_user.username, new_password):
            flash('Password changed successfully!', 'success')
            logger.info(f"Password changed for user: {current_user.username}")
            return redirect(url_for('dashboard'))
        else:
            flash('Failed to change password', 'error')

    force_change = is_default_password(current_user.username)
    return render_template('change_password.html', force_change=force_change)
```

---

### Phase 3 Completion Checklist

- [ ] Whitelist caching implemented (50x speedup)
- [ ] Async DNS queries implemented
- [ ] Log cleanup scheduled
- [ ] Password complexity enforced
- [ ] Performance benchmarks completed
- [ ] Load testing passed

---

## Phase 4: Final Hardening (Week 6)

**Goal:** Complete remaining improvements and prepare for production
**Duration:** 5 days
**Effort:** 4-5 developer days

### Task 4.1: Fix Multi-User Support

**Priority:** P3 - Low
**Effort:** 3 hours

**Implementation:**

```python
# Add to app/database.py

def get_user_by_id(user_id: int) -> Optional[Dict]:
    """
    Get user by ID

    Args:
        user_id: User ID

    Returns:
        User data dict or None
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


# Update app/auth.py

@staticmethod
def get(user_id):
    """Get user by ID"""
    from app.database import get_user_by_id

    user_data = get_user_by_id(int(user_id))
    if user_data:
        return User(user_data)
    return None
```

---

### Task 4.2: Add Audit Logging

**Priority:** P3 - Low
**Effort:** 4 hours

**Implementation:**

```python
# Create app/audit.py

import logging
from datetime import datetime
from functools import wraps
from flask import request
from flask_login import current_user

audit_logger = logging.getLogger('firefly.audit')
audit_handler = logging.FileHandler('/app/logs/audit.log')
audit_handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s'
))
audit_logger.addHandler(audit_handler)
audit_logger.setLevel(logging.INFO)


def audit_log(action: str, details: dict = None):
    """
    Log security-relevant action

    Args:
        action: Action performed
        details: Additional details
    """
    user = current_user.username if current_user.is_authenticated else 'anonymous'
    ip = request.remote_addr if request else 'N/A'

    log_entry = {
        'timestamp': datetime.utcnow().isoformat(),
        'user': user,
        'ip': ip,
        'action': action,
        'details': details or {}
    }

    audit_logger.info(f"{action} | user={user} | ip={ip} | {details or ''}")


def audit_required(action: str):
    """
    Decorator to automatically audit route access

    Args:
        action: Action description
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            audit_log(action, {'endpoint': request.endpoint})
            return f(*args, **kwargs)
        return decorated_function
    return decorator
```

**Add audit logging to sensitive operations:**

```python
# Update app/web_app.py

from app.audit import audit_log, audit_required

@app.route('/login', methods=['GET', 'POST'])
def login():
    # ... existing code ...
    if user:
        audit_log('LOGIN_SUCCESS', {'username': username})
        # ... rest of code ...
    else:
        audit_log('LOGIN_FAILED', {'username': username})
        # ... rest of code ...


@app.route('/whitelist/add', methods=['POST'])
@login_required
@audit_required('WHITELIST_ADD')
def add_domain():
    # ... existing code ...


@app.route('/settings/update', methods=['POST'])
@login_required
@audit_required('SETTINGS_UPDATE')
def update_settings():
    # ... existing code ...
```

---

### Task 4.3: Enable Database WAL Mode

**Priority:** P3 - Low
**Effort:** 1 hour

**Implementation:**

```python
# Update app/database.py

def init_database():
    """Initialize database schema"""
    with get_db() as conn:
        cursor = conn.cursor()

        # Enable WAL mode for better concurrency
        cursor.execute('PRAGMA journal_mode=WAL')
        cursor.execute('PRAGMA synchronous=NORMAL')
        cursor.execute('PRAGMA cache_size=-64000')  # 64MB cache
        cursor.execute('PRAGMA temp_store=MEMORY')

        logger.info("✓ SQLite WAL mode enabled")

        # ... rest of initialization ...
```

---

### Task 4.4: Add Health Check Endpoint

**Priority:** P3 - Low
**Effort:** 2 hours

**Implementation:**

```python
# Add to app/web_app.py

@app.route('/health')
def health_check():
    """
    Health check endpoint for monitoring
    Does not require authentication
    """
    try:
        # Check database
        from app.database import get_config
        _ = get_config('upstream_dns')
        db_status = 'ok'
    except:
        db_status = 'error'

    # Check DNS server
    from app.dns_server import get_dns_server
    dns_server = get_dns_server()
    dns_status = 'ok' if dns_server and dns_server.is_running() else 'error'

    # Overall status
    status = 'healthy' if db_status == 'ok' and dns_status == 'ok' else 'unhealthy'
    status_code = 200 if status == 'healthy' else 503

    return jsonify({
        'status': status,
        'database': db_status,
        'dns_server': dns_status,
        'timestamp': datetime.utcnow().isoformat()
    }), status_code
```

---

## Dependencies & Packages

### Updated requirements.txt

```txt
# Core dependencies
flask==3.0.0
flask-login==0.6.3
dnslib==0.9.24
werkzeug==3.0.1
gunicorn==21.2.0

# Phase 1: Security
flask-wtf==1.2.1
flask-limiter==3.5.0

# Phase 2: Security headers
flask-talisman==1.1.0

# Phase 3: Maintenance
schedule==1.2.0

# Optional: Production enhancements
# redis==5.0.1  # For distributed rate limiting
# prometheus-flask-exporter==0.22.4  # For metrics
```

### Docker Rebuild

```bash
# After updating requirements.txt
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

---

## Testing Strategy

### Unit Tests

```python
# Create tests/test_security.py

import pytest
from app.web_app import create_app
from app.validation import validate_domain, validate_password_strength

class TestSecurity:
    def test_open_redirect_blocked(self):
        """Test that external redirects are blocked"""
        # Test implementation
        pass

    def test_csrf_protection(self):
        """Test CSRF token validation"""
        pass

    def test_rate_limiting(self):
        """Test rate limiting on login"""
        pass

    def test_password_validation(self):
        """Test password strength requirements"""
        assert validate_password_strength("weak")[0] == False
        assert validate_password_strength("StrongP@ssw0rd123")[0] == True
```

### Security Testing

```bash
# Run security scans
bandit -r app/
safety check
semgrep --config=auto .

# OWASP ZAP scan
docker run -t owasp/zap2docker-stable zap-baseline.py \
  -t http://localhost:8080
```

### Performance Testing

```python
# Create tests/test_performance.py

def test_cache_performance():
    """Test whitelist cache improves performance"""
    # Benchmark implementation
    pass

def test_dns_throughput():
    """Test DNS queries per second"""
    # Use dnsperf for benchmarking
    pass
```

---

## Rollout Plan

### Pre-Deployment Checklist

- [ ] All code changes committed and reviewed
- [ ] Unit tests passing
- [ ] Security scans passing
- [ ] Performance benchmarks acceptable
- [ ] Documentation updated
- [ ] Backup of current database
- [ ] Rollback plan prepared

### Deployment Steps

1. **Backup Current System**
   ```bash
   docker-compose exec firefly tar -czf /app/data/backup-$(date +%Y%m%d).tar.gz /app/data/
   ```

2. **Update Code**
   ```bash
   git pull origin main
   ```

3. **Generate SECRET_KEY**
   ```bash
   ./scripts/generate-secrets.sh
   ```

4. **Rebuild Container**
   ```bash
   docker-compose down
   docker-compose build --no-cache
   ```

5. **Start Services**
   ```bash
   docker-compose up -d
   ```

6. **Verify Health**
   ```bash
   curl http://localhost:8080/health
   docker-compose logs -f
   ```

7. **Change Admin Password**
   - Login with generated password
   - Immediately change password
   - Verify initial_password.txt deleted

### Rollback Plan

```bash
# If issues occur:
docker-compose down
git checkout <previous-commit>
docker-compose up -d
# Restore database backup if needed
```

---

## Success Metrics

### Security Metrics

- [ ] 0 critical vulnerabilities remaining
- [ ] 0 high-severity vulnerabilities remaining
- [ ] All security scans passing
- [ ] CSRF protection on all forms
- [ ] Rate limiting on all sensitive endpoints
- [ ] Audit logs capturing security events

### Performance Metrics

- [ ] DNS queries: >1000 q/s (target: 5000 q/s)
- [ ] Whitelist lookup: <1ms average
- [ ] Web interface response: <200ms average
- [ ] Memory usage: <256MB
- [ ] No memory leaks over 24h test

### Code Quality Metrics

- [ ] Unit test coverage: >80%
- [ ] All linters passing (flake8, pylint)
- [ ] Type hints on all functions
- [ ] Comprehensive documentation
- [ ] No hardcoded credentials

---

## Timeline Summary

| Phase | Duration | Key Deliverables |
|-------|----------|------------------|
| Phase 1 | Week 1 (5 days) | Critical security fixes |
| Phase 2 | Week 2-3 (10 days) | High-priority security |
| Phase 3 | Week 4-5 (10 days) | Performance & medium priority |
| Phase 4 | Week 6 (5 days) | Final hardening |
| **Total** | **30 days** | **Production-ready system** |

---

## Risk Management

### High-Risk Items

1. **Database Migration** - Backup critical
2. **SECRET_KEY Change** - Will invalidate sessions
3. **Rate Limiting** - May block legitimate users
4. **Password Requirements** - May frustrate users

### Mitigation Strategies

- Comprehensive testing before deployment
- Staged rollout (dev → staging → production)
- Monitoring and alerting
- Clear communication with users
- Documented rollback procedures

---

## Post-Implementation

### Ongoing Maintenance

- Weekly security scans
- Monthly dependency updates
- Quarterly security audits
- Regular backups (automated)
- Performance monitoring

### Future Enhancements

- Multi-factor authentication (2FA)
- API key authentication
- WebSocket real-time updates
- Prometheus metrics
- Grafana dashboards
- High availability setup

---

**Document Version:** 1.0
**Last Updated:** 2025-11-12
**Next Review:** After Phase 1 completion
