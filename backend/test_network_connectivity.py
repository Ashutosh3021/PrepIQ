import socket
import ssl
import requests
from urllib.parse import urlparse
import os

def test_dns_resolution(hostname):
    """Test DNS resolution for a hostname"""
    try:
        ip = socket.gethostbyname(hostname)
        print(f"✅ DNS resolution: {hostname} -> {ip}")
        return True
    except Exception as e:
        print(f"❌ DNS resolution failed: {e}")
        return False

def test_https_connection(url):
    """Test direct HTTPS connection"""
    try:
        parsed = urlparse(url)
        hostname = parsed.hostname
        port = parsed.port or (443 if parsed.scheme == 'https' else 80)
        
        print(f"Testing HTTPS connection to {hostname}:{port}")
        
        context = ssl.create_default_context()
        with socket.create_connection((hostname, port), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                print(f"✅ HTTPS connection to {hostname}:{port}")
                return True
    except Exception as e:
        print(f"❌ HTTPS connection failed: {e}")
        return False

def test_http_connection(url):
    """Test HTTP connection with requests"""
    try:
        print(f"Testing HTTP connection to {url}")
        response = requests.get(url, timeout=10)
        print(f"✅ HTTP connection successful - Status: {response.status_code}")
        return True
    except Exception as e:
        print(f"❌ HTTP connection failed: {e}")
        return False

def test_supabase_api():
    """Test Supabase API directly"""
    url = "https://cvkvciywqxsktlkigyth.supabase.co"
    service_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImN2a3ZjaXl3cXhza3Rsa2lneXRoIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2NzY5Mjc0OCwiZXhwIjoyMDgzMjY4NzQ4fQ.fvdB7635gvZ6V10LxY8M9MgNX5gUGQjtTf4DAaX84QE"
    
    try:
        print("Testing Supabase REST API...")
        response = requests.get(
            f"{url}/rest/v1/",
            headers={
                "apikey": service_key,
                "Authorization": f"Bearer {service_key}"
            },
            timeout=10
        )
        print(f"✅ Supabase API accessible - Status: {response.status_code}")
        return True
    except Exception as e:
        print(f"❌ Supabase API test failed: {e}")
        return False

def test_google_dns():
    """Test if DNS resolution works for other domains"""
    try:
        ip = socket.gethostbyname("google.com")
        print(f"✅ Google DNS resolution works: google.com -> {ip}")
        return True
    except Exception as e:
        print(f"❌ Google DNS resolution failed: {e}")
        return False

def test_local_network():
    """Test local network connectivity"""
    try:
        # Test connecting to a well-known IP
        with socket.create_connection(("8.8.8.8", 53), timeout=5) as sock:
            print("✅ Local network connectivity OK")
            return True
    except Exception as e:
        print(f"❌ Local network connectivity issue: {e}")
        return False

if __name__ == "__main__":
    print("=== Network Connectivity Diagnostics ===")
    print()
    
    # Test basic network
    local_net_ok = test_local_network()
    google_dns_ok = test_google_dns()
    
    print()
    print("=== Supabase Specific Tests ===")
    
    supabase_host = "cvkvciywqxsktlkigyth.supabase.co"
    
    # Test DNS resolution
    dns_ok = test_dns_resolution(supabase_host)
    
    # Test HTTPS connection
    https_ok = test_https_connection(f"https://{supabase_host}")
    
    # Test HTTP API
    api_ok = test_supabase_api()
    
    print()
    print("=== SUMMARY ===")
    print(f"Local network: {'✅ OK' if local_net_ok else '❌ FAILED'}")
    print(f"Google DNS: {'✅ OK' if google_dns_ok else '❌ FAILED'}")
    print(f"Supabase DNS: {'✅ OK' if dns_ok else '❌ FAILED'}")
    print(f"Supabase HTTPS: {'✅ OK' if https_ok else '❌ FAILED'}")
    print(f"Supabase API: {'✅ OK' if api_ok else '❌ FAILED'}")
    
    print()
    if dns_ok and https_ok and api_ok:
        print("✅ All Supabase connectivity tests passed")
        print("The issue might be in the Supabase client library or authentication")
    elif not dns_ok:
        print("❌ DNS resolution failing - possible DNS configuration issue")
        print("Try: nslookup cvkvciywqxsktlkigyth.supabase.co")
    elif dns_ok and not https_ok:
        print("❌ HTTPS connection failing - possible firewall/proxy issue")
        print("Check if your network blocks connections to Supabase")
    elif dns_ok and https_ok and not api_ok:
        print("❌ API access failing - possible authentication or rate limiting")
        print("Verify your service key is correct")
    else:
        print("❌ Multiple connectivity issues detected")
        print("Check your internet connection and network configuration")