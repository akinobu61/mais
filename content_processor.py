import logging
from bs4 import BeautifulSoup
from urllib.parse import urljoin
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
        # Parse the HTML content
        soup = BeautifulSoup(content, 'html.parser')
        
        # Process links (<a> tags)
        for a_tag in soup.find_all('a', href=True):
            a_tag['href'] = get_proxy_url(original_url, base_domain, a_tag['href'])
        
        # Process form actions
        for form in soup.find_all('form', action=True):
            form['action'] = get_proxy_url(original_url, base_domain, form['action'])
        
        # Process CSS links
        for link in soup.find_all('link', rel='stylesheet', href=True):
            link['href'] = get_proxy_url(original_url, base_domain, link['href'])
        
        # Process script sources
        for script in soup.find_all('script', src=True):
            script['src'] = get_proxy_url(original_url, base_domain, script['src'])
        
        # Process images
        for img in soup.find_all('img', src=True):
            img['src'] = get_proxy_url(original_url, base_domain, img['src'])
        
        # Process iframe sources
        for iframe in soup.find_all('iframe', src=True):
            iframe['src'] = get_proxy_url(original_url, base_domain, iframe['src'])
        
        # Add base tag to ensure all relative URLs are resolved correctly
        head = soup.find('head')
        if head:
            # Check if base tag already exists
            base_tag = head.find('base')
            if base_tag:
                base_tag['href'] = original_url
            else:
                new_base = soup.new_tag('base', href=original_url)
                head.insert(0, new_base)
        
        # Add proxy information in a hidden div (helpful for debugging)
        info_div = soup.new_tag('div', style='display:none;')
        info_div['id'] = 'proxy-info'
        info_div['data-original-url'] = original_url
        if soup.body:
            soup.body.append(info_div)
        
        # Return the modified HTML
        return str(soup).encode('utf-8')
    
    except Exception as e:
        logger.exception(f"Error processing HTML content: {str(e)}")
        # Return the original content if processing fails
        return content
