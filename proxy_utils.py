import requests
import logging
from urllib.parse import urljoin, urlparse

logger = logging.getLogger(__name__)

# Timeout for HTTP requests (in seconds)
REQUEST_TIMEOUT = 10

def resolve_tinyurl(tiny_url_id):
    """
    Resolves a TinyURL ID to its original URL.
    
    Args:
        tiny_url_id (str): The TinyURL identifier
        
    Returns:
        str: The resolved original URL or None if resolution fails
    """
    tinyurl = f"https://tinyurl.com/{tiny_url_id}"
    logger.debug(f"Resolving TinyURL: {tinyurl}")
    
    try:
        # We don't want to download the content yet, just resolve the URL
        response = requests.head(
            tinyurl, 
            allow_redirects=True,
            timeout=REQUEST_TIMEOUT
        )
        
        # If we got redirected, return the final URL
        if response.status_code == 200:
            return response.url
        else:
            logger.error(f"Failed to resolve TinyURL. Status code: {response.status_code}")
            return None
            
    except requests.exceptions.RequestException as e:
        logger.exception(f"Error resolving TinyURL: {str(e)}")
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
    # Special case for data URLs (e.g., data:image/png;base64,...)
    if target_url.startswith('data:'):
        return target_url
        
    # Special case for javascript URLs
    if target_url.startswith('javascript:'):
        return target_url
        
    # Special case for anchor links
    if target_url.startswith('#'):
        return target_url

    # Special case for resources starting with _assets/
    if target_url.startswith('_assets/'):
        # Use the original domain to create a direct path for these assets
        original_domain = urlparse(original_url).netloc
        original_scheme = urlparse(original_url).scheme
        # Create direct URL to the asset on the original domain
        direct_url = f"{original_scheme}://{original_domain}/{target_url}"
        
        # Extract path without _assets/ prefix
        path = target_url
        return urljoin(base_domain, path)
    
    # If it's an absolute URL with http/https
    if target_url.startswith(('http://', 'https://')):
        parsed_url = urlparse(target_url)
        
        # If it's a TinyURL, extract the ID
        if 'tinyurl.com' in parsed_url.netloc:
            tiny_id = parsed_url.path.strip('/')
            return urljoin(base_domain, tiny_id)
            
        # Check if the URL is on the same domain as the original URL
        original_domain = urlparse(original_url).netloc
        if parsed_url.netloc == original_domain:
            # For same domain, use path directly
            path = parsed_url.path
            if path.startswith('/'):
                path = path[1:]
            return urljoin(base_domain, path)
            
        # For other domains, convert to proxy format using path
        # Remove the leading slash if it exists
        path = parsed_url.path
        if path.startswith('/'):
            path = path[1:]
        
        # For external URLs, we could either proxy them or return them directly
        # Here we proxy them through our service
        return urljoin(base_domain, path)
        
    # For relative URLs, join with the original URL first, then convert
    absolute_url = urljoin(original_url, target_url)
    parsed = urlparse(absolute_url)
    
    # Get the path and remove leading slash
    path = parsed.path
    if path.startswith('/'):
        path = path[1:]
        
    return urljoin(base_domain, path)
