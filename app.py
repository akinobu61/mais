import os
import logging
import json
from flask import Flask, request, Response, jsonify
from proxy_utils import decode_url, fetch_content, encode_url
from content_processor import process_content

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET")

@app.route('/<path:encoded_url>', methods=['GET'])
def proxy_url(encoded_url):
    """
    Main route handler for proxying content through encoded URLs
    Accepts encoded_url and fetches content through the proxy
    """
    logger.debug(f"Received request for encoded URL: {encoded_url}")
    
    # If the URL contains query parameters, extract and keep them
    query_string = request.query_string.decode() if request.query_string else ""
    query_appendix = f"?{query_string}" if query_string else ""
    
    try:
        # Decode the encoded URL to get the original URL
        original_url = decode_url(encoded_url)
        if not original_url:
            logger.error(f"Failed to decode URL ID: {encoded_url}")
            return "Failed to decode the URL. The link might be invalid or corrupted.", 404
        
        logger.debug(f"Decoded to original URL: {original_url}")
        
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
    """Root route - provides a form to encode a URL"""
    return """
    <html>
    <head>
        <title>URL Proxy</title>
        <link rel="stylesheet" href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css">
    </head>
    <body class="p-4">
        <div class="container">
            <h1 class="mb-4">URL Proxy Service</h1>
            <p class="mb-3">Enter a URL to encode and proxy:</p>
            <div class="row">
                <div class="col-md-8">
                    <div class="input-group mb-3">
                        <input type="text" id="urlInput" class="form-control" placeholder="https://example.com">
                        <button class="btn btn-primary" onclick="encodeUrl()">Encode & Proxy</button>
                    </div>
                </div>
            </div>
            <div id="result" class="mt-3 d-none">
                <h3>Proxied URL:</h3>
                <div class="input-group mb-3">
                    <input type="text" id="proxyUrl" class="form-control" readonly>
                    <button class="btn btn-secondary" onclick="copyUrl()">Copy</button>
                </div>
                <p><a id="visitLink" href="#" class="btn btn-success mt-2">Visit Proxied Site</a></p>
            </div>
        </div>
        
        <script>
        function encodeUrl() {
            const url = document.getElementById('urlInput').value.trim();
            if (!url) {
                alert('Please enter a valid URL');
                return;
            }
            
            fetch('/encode', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ url })
            })
            .then(response => response.json())
            .then(data => {
                if (data.encoded_url) {
                    const fullUrl = window.location.origin + '/' + data.encoded_url;
                    document.getElementById('proxyUrl').value = fullUrl;
                    document.getElementById('visitLink').href = fullUrl;
                    document.getElementById('result').classList.remove('d-none');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An error occurred while encoding the URL');
            });
        }
        
        function copyUrl() {
            const proxyUrl = document.getElementById('proxyUrl');
            proxyUrl.select();
            document.execCommand('copy');
            alert('URL copied to clipboard!');
        }
        </script>
    </body>
    </html>
    """

@app.route('/encode', methods=['POST'])
def encode_url_endpoint():
    """
    API endpoint to encode a URL
    Accepts a JSON POST with a 'url' parameter
    Returns a JSON response with the encoded URL
    """
    try:
        # Get the URL from the JSON body
        data = request.get_json()
        if not data or 'url' not in data:
            return jsonify({'error': 'URL parameter is required'}), 400
            
        url = data['url']
        
        # Make sure URL has a scheme
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            
        # Encode the URL
        encoded = encode_url(url)
        
        # Return the encoded URL
        return jsonify({'encoded_url': encoded})
        
    except Exception as e:
        logger.exception(f"Error encoding URL: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return "Page not found.", 404

@app.errorhandler(500)
def server_error(e):
    return "Internal server error.", 500
