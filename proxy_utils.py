import requests
import logging
from urllib.parse import urljoin, urlparse

logger = logging.getLogger(__name__)

# Timeout for HTTP requests (in seconds)
REQUEST_TIMEOUT = 10

def resolve_tinyurl(short_url_id):
    """
    Resolves a shortened URL ID to its original URL using direct HTTP requests.
    
    Args:
        short_url_id (str): The shortened URL identifier
        
    Returns:
        str: The resolved original URL or None if resolution fails
    """
    # Create a complete URL with the ID
    short_url = f"https://is.gd/{short_url_id}"
    logger.debug(f"Resolving URL: {short_url}")
    
    try:
        # Just do a HEAD request with allow_redirects=True to follow redirects
        # This is more reliable than using pyshorteners for expansion
        response = requests.head(
            short_url,
            allow_redirects=True,
            timeout=REQUEST_TIMEOUT,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
        )
        
        # If the status code is successful (2xx), return the final URL after redirects
        if 200 <= response.status_code < 300:
            logger.debug(f"Successfully expanded URL to: {response.url}")
            return response.url
        else:
            logger.error(f"Failed to resolve URL: {short_url}, status code: {response.status_code}")
            return None
            
    except requests.exceptions.RequestException as e:
        logger.exception(f"Error resolving URL: {str(e)}")
        return None

def fetch_content(url):
    """
    Fetches content from the specified URL.
    
    Args:
        url (str): The URL to fetch content from
        
    Returns:
        tuple: (content, status_code, content_type)
    """
    logger.debug(f"Fetching content from: {url}")
    
    try:
        response = requests.get(
            url, 
            timeout=REQUEST_TIMEOUT,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
        )
        
        # Return the response content, status code and content type
        return response.content, response.status_code, response.headers.get('Content-Type')
            
    except requests.exceptions.RequestException as e:
        logger.exception(f"Error fetching content: {str(e)}")
        return str(e).encode('utf-8'), 500, 'text/plain'

def get_proxy_url(original_url, base_domain, target_url):
    """
    Converts a URL from the original site to a proxied URL.
    
    Args:
        original_url (str): The original URL that we're proxying
        base_domain (str): The domain of our proxy (e.g., 'http://example.com/')
        target_url (str): The URL to convert to a proxied URL
        
    Returns:
        str: The proxied URL
    """
    # If it's an absolute URL with http/https
    if target_url.startswith(('http://', 'https://')):
        parsed_url = urlparse(target_url)
        
        # If it's a is.gd URL, extract the ID
        if 'is.gd' in parsed_url.netloc:
            short_id = parsed_url.path.strip('/')
            return urljoin(base_domain, short_id)
            
        # For other domains, convert to proxy format using path
        # Remove the leading slash if it exists
        path = parsed_url.path
        if path.startswith('/'):
            path = path[1:]
        
        return urljoin(base_domain, path)
        
    # For relative URLs, join with the original URL first, then convert
    absolute_url = urljoin(original_url, target_url)
    parsed = urlparse(absolute_url)
    
    # Get the path and remove leading slash
    path = parsed.path
    if path.startswith('/'):
        path = path[1:]
        
    return urljoin(base_domain, path)
