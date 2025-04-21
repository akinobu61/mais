import logging
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
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
            
        # Process other resources with srcset attribute
        for elem in soup.find_all(srcset=True):
            elem['srcset'] = get_proxy_url(original_url, base_domain, elem['srcset'])
            
        # Add jQuery if it doesn't exist (to fix "$ is not defined" errors)
        head = soup.find('head')
        if head:
            # Check if jQuery already exists
            jquery_exists = False
            for script in soup.find_all('script', src=True):
                if 'jquery' in script['src'].lower():
                    jquery_exists = True
                    break
                    
            if not jquery_exists:
                jquery_script = soup.new_tag('script')
                jquery_script['src'] = 'https://code.jquery.com/jquery-3.6.0.min.js'
                jquery_script['integrity'] = 'sha256-/xUj+3OJU5yExlq6GSYGSHk7tPXikynS7ogEvDej/m4='
                jquery_script['crossorigin'] = 'anonymous'
                head.insert(0, jquery_script)
            
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
            
        # Fix any direct reference to _assets in style attributes
        for elem in soup.find_all(lambda tag: tag.has_attr('style')):
            try:
                style = elem['style']
                if '_assets/' in style:
                    # Replace relative _assets paths with absolute paths
                    domain = urlparse(original_url).netloc
                    protocol = urlparse(original_url).scheme
                    new_style = style.replace('_assets/', f'{protocol}://{domain}/_assets/')
                    elem['style'] = new_style
            except (TypeError, AttributeError):
                # Skip elements that aren't Tag objects or don't have valid style attributes
                continue
        
        # Return the modified HTML
        return str(soup).encode('utf-8')
    
    except Exception as e:
        logger.exception(f"Error processing HTML content: {str(e)}")
        # Return the original content if processing fails
        return content
