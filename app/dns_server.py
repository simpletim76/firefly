"""
DNS Server module for Project Firefly
Intercepts all DNS queries and enforces whitelist-only policy
"""

import socket
import threading
from dnslib import DNSRecord, DNSHeader, RR, A, QTYPE
from dnslib.server import DNSServer, DNSHandler, BaseResolver
import logging
from app.database import (
    is_domain_whitelisted,
    is_domain_whitelisted_for_profile,
    log_dns_query,
    get_config
)
from app.device_manager import get_device_manager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class WhitelistResolver(BaseResolver):
    """
    Custom DNS resolver that enforces whitelist-only policy
    """

    def __init__(self, upstream_dns='8.8.8.8', block_ip='0.0.0.0'):
        """
        Initialize the whitelist resolver

        Args:
            upstream_dns: DNS server to forward whitelisted queries to
            block_ip: IP address to return for blocked domains
        """
        self.upstream_dns = upstream_dns
        self.block_ip = block_ip
        logger.info(f"WhitelistResolver initialized: upstream={upstream_dns}, block_ip={block_ip}")

    def resolve(self, request, handler):
        """
        Resolve DNS query by checking whitelist

        Args:
            request: DNS request object
            handler: DNS handler object

        Returns:
            DNS reply object
        """
        reply = request.reply()
        qname = str(request.q.qname).rstrip('.')
        qtype = QTYPE[request.q.qtype]
        client_ip = handler.client_address[0]

        logger.debug(f"Query from {client_ip}: {qname} ({qtype})")

        # Get device and profile information
        device_manager = get_device_manager()
        device_id, profile_id = device_manager.get_profile_for_ip(client_ip)

        # Check if domain is whitelisted for this profile
        if self.is_allowed(qname, profile_id):
            logger.info(f"✓ ALLOWED: {qname} from {client_ip} (profile: {profile_id})")

            # Forward to upstream DNS
            try:
                response_ip = self.forward_to_upstream(request)
                log_dns_query(client_ip, qname, qtype, True, response_ip,
                            profile_id=profile_id, device_id=device_id)

                # If we got a valid response from upstream, use it
                if response_ip:
                    reply.add_answer(RR(qname, QTYPE.A, rdata=A(response_ip), ttl=300))
                else:
                    # If upstream failed, return the block IP
                    reply.add_answer(RR(qname, QTYPE.A, rdata=A(self.block_ip), ttl=60))

            except Exception as e:
                logger.error(f"Error forwarding query for {qname}: {e}")
                reply.add_answer(RR(qname, QTYPE.A, rdata=A(self.block_ip), ttl=60))

        else:
            logger.warning(f"✗ BLOCKED: {qname} from {client_ip} (profile: {profile_id})")
            log_dns_query(client_ip, qname, qtype, False, self.block_ip,
                        profile_id=profile_id, device_id=device_id)

            # Return block IP for denied domains
            reply.add_answer(RR(qname, QTYPE.A, rdata=A(self.block_ip), ttl=60))

        return reply

    def is_allowed(self, domain, profile_id=None):
        """
        Check if domain is whitelisted (including subdomains)

        Args:
            domain: Domain name to check
            profile_id: Profile ID to check against (None = check global whitelist only)

        Returns:
            True if allowed, False otherwise
        """
        domain = domain.lower().rstrip('.')

        # If profile_id is provided, check profile-specific whitelist
        if profile_id is not None:
            # Check exact match for profile
            if is_domain_whitelisted_for_profile(domain, profile_id):
                return True

            # Check parent domains (for subdomains) for profile
            parts = domain.split('.')
            for i in range(len(parts)):
                parent_domain = '.'.join(parts[i:])
                if is_domain_whitelisted_for_profile(parent_domain, profile_id):
                    return True
        else:
            # No profile - check global whitelist for backwards compatibility
            # Check exact match
            if is_domain_whitelisted(domain):
                return True

            # Check parent domains (for subdomains)
            parts = domain.split('.')
            for i in range(len(parts)):
                parent_domain = '.'.join(parts[i:])
                if is_domain_whitelisted(parent_domain):
                    return True

        return False

    def forward_to_upstream(self, request):
        """
        Forward DNS query to upstream DNS server

        Args:
            request: DNS request object

        Returns:
            IP address from upstream response, or None if failed
        """
        try:
            # Send request to upstream DNS
            upstream_request = request.send(self.upstream_dns, 53, timeout=2)
            upstream_reply = DNSRecord.parse(upstream_request)

            # Extract first A record from response
            for rr in upstream_reply.rr:
                if rr.rtype == QTYPE.A:
                    return str(rr.rdata)

            return None

        except socket.timeout:
            logger.warning(f"Upstream DNS timeout for {request.q.qname}")
            return None
        except Exception as e:
            logger.error(f"Upstream DNS error: {e}")
            return None


class FireflyDNSServer:
    """
    Main DNS server class for Project Firefly
    """

    def __init__(self, host='0.0.0.0', port=53):
        """
        Initialize Firefly DNS server

        Args:
            host: Host address to bind to
            port: Port to listen on (default 53)
        """
        self.host = host
        self.port = port
        self.server = None
        self.thread = None

        # Load configuration from database
        upstream_dns = get_config('upstream_dns') or '8.8.8.8'
        block_ip = get_config('block_response') or '0.0.0.0'

        # Initialize resolver
        self.resolver = WhitelistResolver(upstream_dns=upstream_dns, block_ip=block_ip)

        logger.info(f"FireflyDNSServer initialized on {host}:{port}")

    def start(self):
        """Start the DNS server in a separate thread"""
        if self.server is not None:
            logger.warning("DNS server already running")
            return

        try:
            # Create DNS server
            self.server = DNSServer(
                self.resolver,
                port=self.port,
                address=self.host,
                tcp=False  # UDP only for lightweight performance
            )

            # Start in separate thread to not block main application
            self.thread = threading.Thread(target=self._run_server, daemon=True)
            self.thread.start()

            logger.info(f"✓ DNS server started on {self.host}:{self.port}")

        except Exception as e:
            logger.error(f"Failed to start DNS server: {e}")
            raise

    def _run_server(self):
        """Internal method to run the DNS server"""
        try:
            self.server.start()
        except Exception as e:
            logger.error(f"DNS server error: {e}")

    def stop(self):
        """Stop the DNS server"""
        if self.server:
            self.server.stop()
            self.server = None
            logger.info("DNS server stopped")

    def is_running(self):
        """Check if DNS server is running"""
        return self.server is not None and self.thread and self.thread.is_alive()


# Global DNS server instance
_dns_server = None


def start_dns_server(host='0.0.0.0', port=53):
    """
    Start the global DNS server instance

    Args:
        host: Host address to bind to
        port: Port to listen on
    """
    global _dns_server

    if _dns_server and _dns_server.is_running():
        logger.warning("DNS server already running")
        return _dns_server

    _dns_server = FireflyDNSServer(host=host, port=port)
    _dns_server.start()

    return _dns_server


def stop_dns_server():
    """Stop the global DNS server instance"""
    global _dns_server

    if _dns_server:
        _dns_server.stop()
        _dns_server = None


def get_dns_server():
    """Get the global DNS server instance"""
    return _dns_server
