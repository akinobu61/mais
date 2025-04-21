import logging
import re
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from proxy_utils import get_proxy_url

logger = logging.getLogger(__name__)

def process_content(content, original_url, base_domain):
    """
    Process HTML content to rewrite URLs and maintain proxy context.
    
    Args:
        content (bytes): The HTML content to process
        original_url (str): The original URL that we're proxying
        base_domain (str): The base domain of our proxy server
        
    Returns:
        bytes: The processed HTML content
    """
    try:
        # Ensure base_domain uses HTTPS only in production environments
        if base_domain.startswith('http:') and not base_domain.startswith('http://localhost') and not base_domain.startswith('http://127.0.0.1'):
            base_domain = base_domain.replace('http:', 'https:', 1)
            
        # Parse the content with BeautifulSoup
        soup = BeautifulSoup(content, 'html.parser')
        
        # Process links (a tags)
        for a_tag in soup.find_all('a', href=True):
            a_tag['href'] = get_proxy_url(original_url, base_domain, a_tag['href'])
            
        # Process CSS links
        for link_tag in soup.find_all('link', href=True):
            link_tag['href'] = get_proxy_url(original_url, base_domain, link_tag['href'])
            
        # Process images (data: URLはそのまま保持)
        for img_tag in soup.find_all('img', src=True):
            if not img_tag['src'].startswith('data:'):
                img_tag['src'] = get_proxy_url(original_url, base_domain, img_tag['src'])
            
        # Process scripts
        for script_tag in soup.find_all('script', src=True):
            script_tag['src'] = get_proxy_url(original_url, base_domain, script_tag['src'])
            
        # Process form actions
        for form_tag in soup.find_all('form', action=True):
            form_tag['action'] = get_proxy_url(original_url, base_domain, form_tag['action'])
            
        # Add Content-Security-Policy meta tag to help prevent mixed content
        meta_csp = soup.new_tag('meta')
        meta_csp.attrs['http-equiv'] = 'Content-Security-Policy'
        meta_csp.attrs['content'] = "upgrade-insecure-requests"
        
        # Find head tag and insert meta tag
        head_tag = soup.find('head')
        if head_tag:
            head_tag.insert(0, meta_csp)
        else:
            # If no head tag, create one and add it to the beginning of the document
            head_tag = soup.new_tag('head')
            head_tag.append(meta_csp)
            if soup.html:
                soup.html.insert(0, head_tag)
                
        # Return the modified content
        return str(soup).encode()
    
    except Exception as e:
        logger.exception(f"Error processing content: {str(e)}")
        return content  # Return original content on error