# Quick Start: Security Fixes for Project Firefly

**⚠️ IMMEDIATE ACTION REQUIRED**

This guide provides the fastest path to securing Project Firefly for production deployment.

---

## Priority Level: CRITICAL (Week 1)

Complete these 5 tasks **before** any production deployment:

### ✅ Task 1: Fix Open Redirect (30 minutes)

**File:** `app/web_app.py`

Add this function after imports:
```python
from urllib.parse import urlparse, urljoin

def is_safe_url(target):
    if not target:
        return False
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc
```

Update login route (line 59-60):
```python
next_page = request.args.get('next')
if next_page and not is_safe_url(next_page):
    logger.warning(f"Blocked unsafe redirect to: {next_page}")
    next_page = None
return redirect(next_page if next_page else url_for('dashboard'))
```

### ✅ Task 2: Add CSRF Protection (1 hour)

**Add to requirements.txt:**
```
flask-wtf==1.2.1
```

**In app/web_app.py:**
```python
from flask_wtf.csrf import CSRFProtect, CSRFError

csrf = CSRFProtect(app)

@app.errorhandler(CSRFError)
def handle_csrf_error(e):
    flash('Security validation failed. Please try again.', 'error')
    return redirect(url_for('login')), 400
```

**Update ALL form templates** - Add before form inputs:
```html
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
```

### ✅ Task 3: Add Rate Limiting (30 minutes)

**Add to requirements.txt:**
```
flask-limiter==3.5.0
```

**In app/web_app.py:**
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    # existing code
```

### ✅ Task 4: Enforce SECRET_KEY (30 minutes)

**Generate secure key:**
```bash
openssl rand -hex 32
```

**Update docker-compose.yml** - Replace line 32:
```yaml
# OLD: - SECRET_KEY=change-this-secret-key-in-production
# NEW: - SECRET_KEY=${SECRET_KEY}
```

**Create .env file:**
```bash
echo "SECRET_KEY=$(openssl rand -hex 32)" > .env
```

**Update config/config.py:**
```python
import sys
SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY and os.getenv('FLASK_ENV') == 'production':
    print("ERROR: SECRET_KEY must be set in production!")
    sys.exit(1)
```

### ✅ Task 5: Remove Default Password (1 hour)

**See SECURITY_FIX_PLAN.md Task 1.5** for complete implementation.

Key changes:
- Generate random password on first install
- Save to file (not in code)
- Force password change on first login
- Remove default from login.html

---

## Quick Deployment (After Week 1 Fixes)

```bash
# 1. Update requirements
pip install -r requirements.txt

# 2. Rebuild Docker
docker-compose down
docker-compose build --no-cache

# 3. Generate secrets
echo "SECRET_KEY=$(openssl rand -hex 32)" > .env

# 4. Start services
docker-compose up -d

# 5. Check health
curl http://localhost:8080/health
docker-compose logs -f

# 6. Get initial password
docker-compose exec firefly cat /app/data/initial_password.txt

# 7. Login and change password immediately
```

---

## Testing Checklist

After implementing fixes:

- [ ] Login works with CSRF token
- [ ] External redirects blocked (test: `/login?next=https://evil.com`)
- [ ] Rate limiting active (try 6 login attempts in 1 minute)
- [ ] Application starts without hardcoded SECRET_KEY
- [ ] Random password generated on fresh install
- [ ] All forms have CSRF tokens
- [ ] Security headers present (`curl -I http://localhost:8080/`)

---

## Performance Quick Wins (Week 2-3)

### Add Whitelist Caching (Massive Performance Boost)

**Impact:** 50-100x faster DNS queries

See **SECURITY_FIX_PLAN.md Task 3.1** for implementation.

Expected improvement:
- Before: 50-100 queries/second
- After: 5,000-10,000 queries/second

---

## Common Issues & Solutions

### Issue: CSRF token missing
**Solution:** Ensure all POST forms have `{{ csrf_token() }}` input

### Issue: Rate limit blocking legitimate users
**Solution:** Adjust limits in limiter.limit() decorators

### Issue: Container won't start (SECRET_KEY error)
**Solution:** Create .env file with `SECRET_KEY=$(openssl rand -hex 32)`

### Issue: Can't login after rebuild
**Solution:** Sessions invalidated by SECRET_KEY change - normal behavior

---

## Security Scan Commands

```bash
# Install security tools
pip install bandit safety

# Run scans
bandit -r app/
safety check
```

---

## Resources

- **Full Details:** See `SECURITY_REVIEW.md`
- **Implementation Plan:** See `SECURITY_FIX_PLAN.md`
- **Flask-WTF Docs:** https://flask-wtf.readthedocs.io/
- **Flask-Limiter Docs:** https://flask-limiter.readthedocs.io/

---

## Emergency Rollback

```bash
# If critical issues occur:
git log --oneline -5  # Find previous commit
git checkout <commit-hash>
docker-compose down
docker-compose up -d --build
```

---

**Priority:** 🔴 CRITICAL - Complete Week 1 tasks before production use
**Estimated Time:** 3-4 hours for critical fixes
**Next Steps:** Follow full SECURITY_FIX_PLAN.md for comprehensive hardening
