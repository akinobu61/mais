import requests
import logging
import base64
import hashlib
from urllib.parse import urljoin, urlparse, quote, unquote

logger = logging.getLogger(__name__)

# Timeout for HTTP requests (in seconds)
REQUEST_TIMEOUT = 10

# Secret key for URL encoding/decoding (keep this secure in a production environment)
URL_ENCODING_KEY = "mySecretKey123"  # In production, this should be in environment variables

def encode_url(original_url):
    """
    Encodes a URL using a custom algorithm to create a shorter representation.
    
    Args:
        original_url (str): The original URL to encode
        
    Returns:
        str: The encoded URL string
    """
    # First, URL-quote the original URL to handle special characters
    safe_url = quote(original_url)
    
    # Create a simple encoding by using base64 
    encoded = base64.urlsafe_b64encode(safe_url.encode()).decode()
    
    # Remove padding characters (=) as they're not URL-safe
    encoded = encoded.rstrip("=")
    
    # Add a simple hash for validation (first 8 chars of the sha256 hash)
    hash_signature = hashlib.sha256((encoded + URL_ENCODING_KEY).encode()).hexdigest()[:8]
    
    # Combine the hash and encoded string
    result = f"{hash_signature}{encoded}"
    
    logger.debug(f"Encoded URL '{original_url}' to '{result}'")
    return result

def decode_url(encoded_id):
    """
    Decodes an encoded URL ID back to its original URL.
    
    Args:
        encoded_id (str): The encoded URL identifier
        
    Returns:
        str: The decoded original URL or None if decoding fails
    """
    try:
        if len(encoded_id) < 8:
            logger.error(f"Invalid encoded ID (too short): {encoded_id}")
            return None
            
        # Extract the hash and encoded parts
        hash_part = encoded_id[:8]
        encoded_part = encoded_id[8:]
        
        # Validate the hash
        calculated_hash = hashlib.sha256((encoded_part + URL_ENCODING_KEY).encode()).hexdigest()[:8]
        if calculated_hash != hash_part:
            logger.error(f"Hash validation failed for encoded ID: {encoded_id}")
            return None
        
        # Add padding back if needed
        padding_needed = len(encoded_part) % 4
        if padding_needed:
            encoded_part += "=" * (4 - padding_needed)
        
        # Decode the base64 part
        decoded_bytes = base64.urlsafe_b64decode(encoded_part)
        safe_url = decoded_bytes.decode()
        
        # URL-unquote to get the original URL
        original_url = unquote(safe_url)
        
        logger.debug(f"Decoded ID '{encoded_id}' to URL '{original_url}'")
        return original_url
        
    except Exception as e:
        logger.exception(f"Error decoding URL ID: {str(e)}")
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
    Converts a URL from the original site to a proxied URL using our custom encoding.
    
    Args:
        original_url (str): The original URL that we're proxying
        base_domain (str): The domain of our proxy (e.g., 'http://example.com/')
        target_url (str): The URL to convert to a proxied URL
        
    Returns:
        str: The proxied URL
    """
    # If it's a relative URL, make it absolute first
    if not target_url.startswith(('http://', 'https://')):
        target_url = urljoin(original_url, target_url)
    
    # Use our custom encoding to convert the URL to an encoded form
    encoded_id = encode_url(target_url)
    
    # Create the proxy URL by joining the base domain with the encoded ID
    proxy_url = urljoin(base_domain, encoded_id)
    
    logger.debug(f"Converted '{target_url}' to proxy URL '{proxy_url}'")
    return proxy_url
