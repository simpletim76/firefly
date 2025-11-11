# 🚀 Project Firefly - Deployment Guide

## Quick Start (One Command)

```bash
./start.sh
```

This script will:
1. ✅ Check for Docker and Docker Compose
2. ✅ Create directories with correct permissions
3. ✅ Build the Docker image
4. ✅ Start the container
5. ✅ Display access information

## Manual Deployment

### Step 1: Prepare Directories

**IMPORTANT**: Always create directories with proper permissions before starting the container.

```bash
mkdir -p data logs
chmod 777 data logs
```

Or use the Makefile:
```bash
make prepare
```

### Step 2: Build Container

```bash
docker-compose build
```

Or:
```bash
make build
```

### Step 3: Start Container

```bash
docker-compose up -d
```

Or:
```bash
make up
```

### Step 4: Verify

```bash
# Check container status
docker-compose ps

# View logs
docker-compose logs -f

# Check health
docker-compose exec firefly wget -qO- http://localhost:8080/api/stats
```

## Common Issues & Solutions

### Issue 1: Permission Denied on Logs

**Error**: `PermissionError: [Errno 13] Permission denied: '/app/logs/firefly.log'`

**Solution**:
```bash
chmod 777 data logs
docker-compose restart
```

**Note**: The application will automatically fall back to stdout-only logging if it encounters permission errors, so Firefly will still run.

### Issue 2: DNS Server Permission Denied

**Error**: `Permission denied` when binding to port 53

**Cause**: Port 53 is a privileged port requiring root access.

**Solution**: The container is configured to run as root in `docker-compose.yml`:
```yaml
user: root  # Required for DNS port 53
```

This is already set by default. If you see this error, verify the line is present in your docker-compose.yml.

### Issue 3: Container Won't Start

**Check**:
```bash
docker-compose logs
```

**Common causes**:
- Port 53 already in use (another DNS server running - check with `sudo lsof -i :53`)
- Port 8080 already in use
- Docker daemon not running

### Issue 4: Can't Access Web Interface

**Verify container is running**:
```bash
docker-compose ps
```

**Check if port is accessible**:
```bash
curl http://localhost:8080
```

**If using Raspberry Pi remotely**:
```bash
curl http://YOUR_PI_IP:8080
```

## Network Configuration

### Option 1: Host Network Mode (Default)

The container uses host network mode for seamless DNS operation. No port mapping needed.

```yaml
network_mode: host
```

### Option 2: Bridge Mode with Port Mapping

If you need bridge mode, edit `docker-compose.yml`:

```yaml
# Comment out:
# network_mode: host

# Uncomment:
ports:
  - "53:53/udp"
  - "8080:8080"
```

## Configuring Devices to Use Firefly

### Method 1: Router DNS (Recommended)

Set your router's primary DNS to your Raspberry Pi's IP address. This applies filtering to all devices automatically.

### Method 2: Per-Device Configuration

Manually set DNS on each device:
- **Windows**: Network Settings → Change Adapter → DNS Server
- **macOS**: System Preferences → Network → Advanced → DNS
- **Linux**: `/etc/resolv.conf` or Network Manager
- **iOS/Android**: WiFi Settings → Configure DNS

### Method 3: Testing

Test DNS resolution before changing production settings:

```bash
# Test with dig
dig @YOUR_PI_IP google.com

# Test with nslookup
nslookup google.com YOUR_PI_IP
```

## Post-Deployment Checklist

- [ ] Container is running: `docker-compose ps`
- [ ] Web interface accessible: `http://YOUR_PI_IP:8080`
- [ ] Changed default password from `admin123`
- [ ] Added essential domains to whitelist (see below)
- [ ] Configured at least one test device to use Firefly DNS
- [ ] Verified DNS filtering is working
- [ ] Set up automatic container restart: `restart: unless-stopped` in docker-compose.yml
- [ ] Documented your network configuration
- [ ] Scheduled database backups

## Essential Domains for Whitelist

Start with these essential domains:

```
# DNS Resolution
dns.google
cloudflare-dns.com

# Basic connectivity
google.com
googleapis.com
gstatic.com

# Package managers (if using Linux)
archive.ubuntu.com
security.ubuntu.com
pypi.org
github.com

# Time sync
pool.ntp.org
time.google.com

# Add more based on your needs
```

Use the web interface to add these at `http://YOUR_PI_IP:8080/whitelist`

## Monitoring & Maintenance

### View Real-Time Logs

```bash
docker-compose logs -f
```

### Check Statistics

```bash
curl http://localhost:8080/api/stats | jq
```

### Backup Database

```bash
# Manual backup
cp data/firefly.db data/firefly_backup_$(date +%Y%m%d).db

# Or from inside container
docker-compose exec firefly cp /app/data/firefly.db /app/data/backup.db
```

### Update Firefly

```bash
git pull
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## Performance Tuning

### For Raspberry Pi 3 or Lower

Reduce memory limit in `docker-compose.yml`:

```yaml
deploy:
  resources:
    limits:
      memory: 128M
```

### For High-Traffic Networks

Increase memory and adjust log retention:

```yaml
deploy:
  resources:
    limits:
      memory: 512M

environment:
  - LOG_RETENTION_DAYS=7  # Keep fewer logs
```

## Security Hardening

1. **Change default password immediately**
2. **Use strong SECRET_KEY** in production
3. **Restrict web interface access**:
   ```bash
   # Only allow from local network
   iptables -A INPUT -p tcp --dport 8080 -s 192.168.1.0/24 -j ACCEPT
   iptables -A INPUT -p tcp --dport 8080 -j DROP
   ```
4. **Enable HTTPS** with reverse proxy (nginx/caddy)
5. **Regular updates**: Keep Docker and host OS updated
6. **Monitor logs**: Set up log monitoring for suspicious activity

## Support

- **Documentation**: See README.md
- **Issues**: GitHub Issues
- **Logs**: `docker-compose logs -f`

---

**Built with 🔥 by Project Firefly**
