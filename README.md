# 🔥 Project Firefly

**Lightweight DNS Filtering Application for Raspberry Pi**

A whitelist-only DNS server with a web admin interface, designed to run efficiently in a Docker container on Raspberry Pi.

## Features

- **Whitelist-Only DNS Filtering**: Default deny for all domains except those explicitly whitelisted
- **Web Admin Interface**: Easy-to-use dashboard for managing whitelist and viewing logs
- **SQLite Database**: Lightweight storage for whitelist, DNS query logs, and configuration
- **Docker Container**: Single-container deployment with minimal resource footprint
- **Raspberry Pi Optimized**: Built on Alpine Linux for ARM architecture
- **Real-time Logging**: Track all DNS queries with detailed statistics
- **Subdomain Support**: Whitelist parent domains to allow all subdomains

## Technology Stack

- **Python 3.11** - Core application language
- **dnslib** - Lightweight DNS server library
- **Flask** - Web framework for admin interface
- **SQLite3** - Database for persistence
- **Alpine Linux** - Minimal container base image
- **Docker** - Containerization platform

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Raspberry Pi (or any ARM/AMD64 system)
- Port 53 (DNS) and 8080 (Web UI) available

### Installation

**Option 1: Quick Start (Recommended)**

Use the provided start script that handles everything:
```bash
cd /path/to/firefly
./start.sh
```

**Option 2: Manual Setup**

1. **Clone or create the project:**
   ```bash
   cd /path/to/firefly
   ```

2. **Prepare directories (important for permissions):**
   ```bash
   mkdir -p data logs
   chmod 777 data logs
   ```
   Or use: `make prepare`

3. **Configure environment (optional):**
   ```bash
   cp .env.example .env
   nano .env  # Customize settings
   ```

4. **Build and start the container:**
   ```bash
   docker-compose build
   docker-compose up -d
   ```
   Or use: `make build && make up`

5. **Verify it's running:**
   ```bash
   docker-compose ps
   docker-compose logs -f
   ```

6. **Access the web interface:**
   - URL: `http://your-raspberry-pi-ip:8080`
   - Default username: `admin`
   - Default password: `admin123`
   - **⚠️ IMPORTANT: Change default password after first login!**

## Configuration

### Environment Variables

Edit `.env` or set in `docker-compose.yml`:

| Variable | Default | Description |
|----------|---------|-------------|
| `DNS_HOST` | `0.0.0.0` | DNS server bind address |
| `DNS_PORT` | `53` | DNS server port |
| `WEB_HOST` | `0.0.0.0` | Web interface bind address |
| `WEB_PORT` | `8080` | Web interface port |
| `DB_PATH` | `/app/data/firefly.db` | SQLite database path |
| `SECRET_KEY` | (random) | Flask secret key (change in production!) |
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `TZ` | `UTC` | Timezone |

### Network Configuration

The container uses `host` network mode by default for DNS to work properly. If you need to use bridge mode, uncomment the `ports` section in `docker-compose.yml`.

## Usage

### Web Interface

#### Dashboard
- View DNS query statistics (total, allowed, blocked)
- See recently queried domains
- Quick-add frequently blocked domains to whitelist

#### Whitelist Management
- Add domains with optional descriptions
- Enable/disable domains without removing them
- Remove domains from whitelist
- Parent domains automatically allow subdomains

#### DNS Query Logs
- View all DNS queries with timestamps
- Search for specific domains
- Filter by allowed/blocked status
- Track client IP addresses

#### Settings
- Configure upstream DNS server (default: 8.8.8.8)
- Set block response IP (default: 0.0.0.0)
- Adjust log retention period

### DNS Server Usage

#### Configure Devices to Use Firefly

**Option 1: Per-Device Configuration**
Set DNS server on each device to your Raspberry Pi's IP address.

**Option 2: Router Configuration (Recommended)**
Set your router's DNS server to your Raspberry Pi's IP address. This applies filtering to all devices on your network.

**Option 3: Testing**
Test DNS resolution with:
```bash
dig @your-raspberry-pi-ip google.com
nslookup google.com your-raspberry-pi-ip
```

### API Endpoints

Firefly provides JSON API endpoints for automation:

```bash
# Get statistics
curl http://localhost:8080/api/stats

# Get whitelist
curl http://localhost:8080/api/whitelist

# Get recent logs
curl http://localhost:8080/api/logs?limit=50
```

## Database Schema

### Tables

**whitelist**
- `id`: Primary key
- `domain`: Domain name (unique)
- `description`: Optional description
- `added_date`: Timestamp when added
- `added_by`: Username who added it
- `enabled`: Boolean flag

**dns_logs**
- `id`: Primary key
- `timestamp`: Query timestamp
- `client_ip`: Client IP address
- `domain`: Queried domain
- `query_type`: DNS query type (A, AAAA, etc.)
- `allowed`: Boolean (allowed/blocked)
- `response_ip`: IP address returned

**config**
- `key`: Configuration key
- `value`: Configuration value
- `updated_at`: Last update timestamp

**users**
- `id`: Primary key
- `username`: Username (unique)
- `password_hash`: Hashed password
- `created_at`: Account creation timestamp
- `last_login`: Last login timestamp

## File Structure

```
firefly/
├── app/
│   ├── __init__.py
│   ├── auth.py              # Authentication logic
│   ├── database.py          # Database operations
│   ├── dns_server.py        # DNS server implementation
│   ├── web_app.py           # Flask web application
│   ├── static/
│   │   └── style.css        # Stylesheet
│   └── templates/           # HTML templates
│       ├── base.html
│       ├── dashboard.html
│       ├── login.html
│       ├── whitelist.html
│       ├── logs.html
│       ├── settings.html
│       └── error.html
├── config/
│   └── config.py            # Configuration management
├── data/                    # SQLite database (persistent volume)
├── logs/                    # Application logs (persistent volume)
├── Dockerfile               # Container build instructions
├── docker-compose.yml       # Container orchestration
├── requirements.txt         # Python dependencies
├── run.py                   # Application entry point
├── setup.py                 # Setup and verification script
├── .env.example             # Environment variables template
└── README.md                # This file
```

## Maintenance

### View Logs
```bash
docker-compose logs -f
```

### Restart Container
```bash
docker-compose restart
```

### Stop Container
```bash
docker-compose stop
```

### Update Application
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Backup Database
```bash
docker-compose exec firefly cp /app/data/firefly.db /app/data/firefly_backup.db
# Or from host:
cp data/firefly.db data/firefly_backup_$(date +%Y%m%d).db
```

### Clean Old Logs
Logs are automatically cleaned based on retention settings, but you can manually clean:
```bash
docker-compose exec firefly python -c "from app.database import cleanup_old_logs; cleanup_old_logs(30)"
```

## Troubleshooting

### DNS Server Won't Start

**Issue**: `Permission denied` on port 53

**Cause**: Binding to privileged ports (< 1024) requires root privileges, especially with host network mode.

**Solution**: The docker-compose.yml is configured to run as root by default:
```yaml
user: root  # Required for DNS on port 53
```

This is already set and necessary for DNS server functionality. If you removed it, re-add this line.

### Web Interface Not Accessible

**Check if container is running:**
```bash
docker-compose ps
```

**Check logs:**
```bash
docker-compose logs
```

**Verify port 8080 is not in use:**
```bash
sudo netstat -tulpn | grep 8080
```

### DNS Queries Not Being Filtered

**Verify DNS server is listening:**
```bash
docker-compose exec firefly netstat -ulnp
```

**Test DNS resolution:**
```bash
dig @localhost google.com
```

**Check device DNS settings:**
Ensure devices are configured to use Firefly's IP address.

### Database Locked Errors

**Issue**: SQLite database locked

**Solution**:
- Ensure only one Firefly instance is running
- Check for crashed processes: `docker-compose restart`

### Permission Errors (Logs/Database)

**Issue**: `PermissionError: [Errno 13] Permission denied: '/app/logs/firefly.log'`

**Cause**: Host directories mounted as volumes may not have correct permissions for the container user (UID 1000).

**Solution**:
```bash
# Fix permissions on host directories
chmod 777 data logs

# Or run the prepare command
make prepare

# Then restart the container
docker-compose restart
```

**Alternative**: The application will automatically fall back to stdout-only logging if it can't write to the log file, so this won't prevent Firefly from running.

### Container Crashes

**Check resource limits:**
```bash
docker stats firefly-dns
```

**Increase memory limit in docker-compose.yml:**
```yaml
deploy:
  resources:
    limits:
      memory: 512M
```

## Performance

### Resource Usage

Typical resource consumption on Raspberry Pi 4:
- **Memory**: 128-256 MB
- **CPU**: <5% during normal operation
- **Disk**: ~20 MB application + logs/database

### Optimization Tips

1. **Adjust log retention**: Reduce database size by lowering retention period
2. **Limit log verbosity**: Set `LOG_LEVEL=WARNING` in production
3. **Use cache**: DNS responses are cached by upstream DNS server
4. **Regular cleanup**: Clean old logs periodically

## Security Considerations

1. **Change default password**: Change `admin123` immediately after first login
2. **Secure SECRET_KEY**: Use a strong random key in production
3. **Root user note**: The container runs as root to bind to port 53 (DNS). This is standard for DNS servers and acceptable because:
   - The container is still isolated from the host system
   - DNS servers traditionally require elevated privileges
   - It's a dedicated appliance for a single purpose
   - Alternative: Use port 5353 and redirect with iptables if root access is a concern
4. **Network isolation**: Consider running Firefly on isolated network segment
5. **Regular updates**: Keep Docker image and dependencies updated
6. **HTTPS**: For production, consider adding HTTPS with reverse proxy (nginx)
7. **Firewall**: Restrict web interface access to trusted IPs

## Advanced Usage

### Custom Upstream DNS

Edit settings or set environment variable:
```bash
UPSTREAM_DNS=1.1.1.1  # Cloudflare
UPSTREAM_DNS=9.9.9.9  # Quad9
```

### Multiple Instances

Run multiple Firefly instances for redundancy:
```yaml
# docker-compose.yml
services:
  firefly-primary:
    # ... config ...
    ports:
      - "53:53/udp"
      - "8080:8080"

  firefly-secondary:
    # ... config ...
    ports:
      - "5353:53/udp"
      - "8081:8080"
```

### Integration with Pi-hole

Firefly can complement Pi-hole:
- Pi-hole: Blacklist approach (block ads)
- Firefly: Whitelist approach (explicit allow)

Chain them: Device → Firefly → Pi-hole → Internet

## Development

### Local Testing

1. **Install dependencies:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Run setup:**
   ```bash
   python setup.py
   ```

3. **Run application:**
   ```bash
   export DB_PATH=./data/firefly.db
   export DNS_PORT=5353  # Non-privileged port for testing
   export WEB_PORT=8080
   python run.py
   ```

### Testing DNS Server

```bash
# Test allowed domain (if in whitelist)
dig @localhost -p 5353 google.com

# Test blocked domain (if not in whitelist)
dig @localhost -p 5353 example.com
```

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

MIT License - See LICENSE file for details

## Support

For issues and questions:
- GitHub Issues: [Project repository]
- Documentation: This README
- Community: [Your community link]

## Changelog

### Version 1.0.0 (Initial Release)
- ✨ Whitelist-only DNS filtering
- ✨ Web admin interface with Flask
- ✨ SQLite database for persistence
- ✨ Docker container deployment
- ✨ Raspberry Pi ARM optimization
- ✨ Real-time DNS query logging
- ✨ Statistics dashboard
- ✨ Subdomain support

---

**Made with 🔥 by Project Firefly**
