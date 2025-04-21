import logging
import requests
from urllib.parse import urljoin, urlparse

logger = logging.getLogger(__name__)

# Timeout for HTTP requests (in seconds)
REQUEST_TIMEOUT = 10

def fetch_content(url):
    """
    Fetches content from the specified URL.
    
    Args:
        url (str): The URL to fetch content from
        
    Returns:
        tuple: (content, status_code, content_type)
    """
    try:
        # Try to upgrade HTTP to HTTPS if needed
        if url.startswith('http:'):
            https_url = url.replace('http:', 'https:', 1)
            logger.debug(f"Trying to upgrade HTTP URL to HTTPS: {https_url}")
            
            try:
                # First try with HTTPS
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3',
                }
                
                response = requests.get(https_url, headers=headers, timeout=REQUEST_TIMEOUT, allow_redirects=True)
                
                # If successful, use the HTTPS URL
                url = https_url
                
            except requests.RequestException:
                # If HTTPS failed, continue with the original HTTP URL
                logger.debug(f"HTTPS upgrade failed, falling back to original URL: {url}")
                
        # Set up headers to mimic a browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3',
        }
        
        # Make the request
        response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT, allow_redirects=True)
        
        # Get content type from headers
        content_type = response.headers.get('Content-Type', 'text/html')
        
        return response.content, response.status_code, content_type
    
    except Exception as e:
        logger.exception(f"Error fetching content from {url}: {str(e)}")
        return f"Error fetching content: {str(e)}".encode(), 500, 'text/plain'

def get_proxy_url(original_url, base_domain, target_url):
    """
    Converts a URL from the original site to a proxied URL using our custom encoding.
    
    Args:
        original_url (str): The original URL that we're proxying
        base_domain (str): The base domain of our proxy (e.g., 'http://example.com/')
        target_url (str): The URL to convert to a proxied URL
        
    Returns:
        str: The proxied URL
    """
    from url_crypto import encode_url
    
    # If it's a relative URL, make it absolute first
    if not target_url.startswith(('http://', 'https://')):
        target_url = urljoin(original_url, target_url)
    
    # Use our custom encoding to convert the URL to an encoded form
    encoded_id = encode_url(target_url)
    
    # Ensure base_domain uses HTTPS only in production environments
    if base_domain.startswith('http:') and not base_domain.startswith('http://localhost') and not base_domain.startswith('http://127.0.0.1'):
        base_domain = base_domain.replace('http:', 'https:', 1)
    
    # Create the proxy URL by joining the base domain with the encoded ID
    proxy_url = urljoin(base_domain, encoded_id)
    
    logger.debug(f"Converted '{target_url}' to proxy URL '{proxy_url}'")
    return proxy_url