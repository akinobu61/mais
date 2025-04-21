import os
import logging
from flask import Flask, request, Response
from proxy_utils import resolve_tinyurl, fetch_content
from content_processor import process_content

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET")

@app.route('/<path:tiny_url_id>', methods=['GET'])
def proxy_tinyurl(tiny_url_id):
    """
    Main route handler for proxying TinyURL content
    Accepts tiny_url_id and fetches content through the proxy
    """
    logger.debug(f"Received request for tiny URL ID: {tiny_url_id}")
    
    # If the URL contains query parameters, extract and keep them
    query_string = request.query_string.decode() if request.query_string else ""
    query_appendix = f"?{query_string}" if query_string else ""
    
    try:
        # Resolve the TinyURL to get the original URL
        original_url = resolve_tinyurl(tiny_url_id)
        if not original_url:
            logger.error(f"Failed to resolve TinyURL for ID: {tiny_url_id}")
            return "Failed to resolve the TinyURL. The link might be invalid or no longer available.", 404
        
        logger.debug(f"Resolved to original URL: {original_url}")
        
        # Add query parameters if they exist
        if query_appendix:
            original_url = f"{original_url}{query_appendix}"
            
        # Fetch the content from the original URL
        content, status_code, content_type = fetch_content(original_url)
        
        if status_code >= 400:
            logger.error(f"Error fetching content: {status_code}")
            return f"Error fetching content: HTTP {status_code}", status_code
            
        # Process content if it's HTML
        if content_type and 'text/html' in content_type:
            content = process_content(content, original_url, request.host_url)
        
        # Create response with appropriate headers
        response = Response(content)
        
        # Set content type if available
        if content_type:
            response.headers['Content-Type'] = content_type
            
        return response
        
    except Exception as e:
        logger.exception(f"Error processing request: {str(e)}")
        return f"An error occurred while processing your request: {str(e)}", 500

@app.route('/', methods=['GET'])
def root():
    """Root route - returns a simple message since we need a TinyURL ID"""
    return "Please provide a TinyURL ID in the URL (domain/TinyURLID)", 400

@app.route('/favicon.ico')
def favicon():
    """Handle favicon requests"""
    return "", 204  # No content response

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return "Page not found.", 404

@app.errorhandler(500)
def server_error(e):
    return "Internal server error.", 500
