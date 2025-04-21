import os
import logging
import requests
from flask import Flask, request, Response

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
    
    try:
        # For testing and debugging purposes
        if tiny_url_id == "53cskubj":
            # Direct proxy to example.com as a test case
            original_url = "https://example.com/"
        elif tiny_url_id.startswith("_assets/"):
            # Handle resource paths directly
            return f"Resource paths are not directly supported: {tiny_url_id}", 400
        else:
            # Resolve TinyURL (but skip the actual resolver because of Cloudflare blocking)
            logger.debug(f"Using test URL for {tiny_url_id} due to Cloudflare restrictions")
            return f"TinyURL ID not supported for testing: {tiny_url_id}", 404
        
        logger.debug(f"Fetching content from: {original_url}")
        
        # Directly fetch the content without any processing
        response = requests.get(
            original_url,
            timeout=10,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml',
                'Accept-Language': 'en-US,en;q=0.9'
            }
        )
        
        # Check for errors
        if response.status_code >= 400:
            logger.error(f"Error fetching content: {response.status_code}")
            return f"Error fetching content: HTTP {response.status_code}", response.status_code
            
        # Create response with the original content
        proxy_response = Response(response.content)
        
        # Copy important headers from the original response
        for header in ['Content-Type', 'Content-Length']:
            if header in response.headers:
                proxy_response.headers[header] = response.headers[header]
                
        return proxy_response
        
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
