#!/usr/bin/env python3
"""Security Quotas - prevents resource exhaustion and SSRF attacks."""
import socket
import ipaddress
from urllib.parse import urlparse

# Block private/internal IPs (SSRF protection)
BLOCKED_NETWORKS = [
    ipaddress.ip_network('127.0.0.0/8'),      # Loopback
    ipaddress.ip_network('10.0.0.0/8'),        # Private Class A
    ipaddress.ip_network('172.16.0.0/12'),     # Private Class B
    ipaddress.ip_network('192.168.0.0/16'),    # Private Class C
    ipaddress.ip_network('169.254.0.0/16'),    # Link-local (AWS metadata)
    ipaddress.ip_network('0.0.0.0/8'),         # Current network
    ipaddress.ip_network('::1/128'),           # IPv6 loopback
    ipaddress.ip_network('fc00::/7'),          # IPv6 unique local
    ipaddress.ip_network('fe80::/10'),         # IPv6 link-local
]

# Resource limits
MAX_DOWNLOAD_SIZE_MB = 5
MAX_REQUEST_TIMEOUT_SEC = 10
MAX_REDIRECTS = 3

def validate_url(url):
    """Validate URL is safe to scrape (no SSRF, no private IPs)."""
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ['http', 'https']:
            return False, f"Invalid scheme: {parsed.scheme}. Only http/https allowed."
        
        hostname = parsed.hostname
        if not hostname:
            return False, "No hostname in URL"
        
        # Resolve hostname to IP
        try:
            ip_str = socket.gethostbyname(hostname)
            ip = ipaddress.ip_address(ip_str)
        except socket.gaierror:
            return False, f"Cannot resolve hostname: {hostname}"
        
        # Check if IP is in blocked networks
        for network in BLOCKED_NETWORKS:
            if ip in network:
                return False, f"Blocked: {hostname} resolves to private/internal IP {ip_str}. Cannot scrape internal networks."
        
        return True, "URL is safe"
    except Exception as e:
        return False, f"URL validation error: {str(e)}"

def get_limits():
    """Get resource limits."""
    return {
        "max_download_size_mb": MAX_DOWNLOAD_SIZE_MB,
        "max_request_timeout_sec": MAX_REQUEST_TIMEOUT_SEC,
        "max_redirects": MAX_REDIRECTS,
        "blocked_networks": ["127.0.0.0/8", "10.0.0.0/8", "192.168.0.0/16", "169.254.0.0/16"]
    }
