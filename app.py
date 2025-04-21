import os
import logging
from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
import pyshorteners
import secrets

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Setup database
class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET") or secrets.token_hex(16)

# Configure database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
db.init_app(app)

# Import URL encryption utilities
from url_crypto import encode_url, decode_url
# Import database models
with app.app_context():
    from models import URLMapping
    db.create_all()

# Create TinyURL shortener
shortener = pyshorteners.Shortener()

@app.route('/', methods=['GET'])
def index():
    """Homepage with URL form"""
    return render_template('index.html')

@app.route('/create', methods=['POST'])
def create_short_url():
    """Create a new encrypted and shortened URL"""
    try:
        original_url = request.form.get('url')
        
        if not original_url:
            return render_template('index.html', error='URLを入力してください')
        
        # Make sure URL has a scheme
        if not original_url.startswith(('http://', 'https://')):
            original_url = 'https://' + original_url
            
        # Check if this URL has already been encoded
        existing_mapping = URLMapping.query.filter_by(original_url=original_url).first()
        if existing_mapping:
            # Get the TinyURL shortened version
            tiny_url = shortener.tinyurl.short(request.host_url + existing_mapping.encoded_id)
            return render_template('result.html', 
                                   original_url=original_url,
                                   encoded_url=request.host_url + existing_mapping.encoded_id,
                                   tiny_url=tiny_url)
        
        # Encode the URL
        encoded_id = encode_url(original_url)
        
        # Save to database
        url_mapping = URLMapping(original_url=original_url, encoded_id=encoded_id)
        db.session.add(url_mapping)
        db.session.commit()
        
        # Get the TinyURL shortened version
        tiny_url = shortener.tinyurl.short(request.host_url + encoded_id)
        
        return render_template('result.html', 
                               original_url=original_url,
                               encoded_url=request.host_url + encoded_id,
                               tiny_url=tiny_url)
        
    except Exception as e:
        logger.exception(f"Error creating short URL: {str(e)}")
        return render_template('index.html', error=f'エラーが発生しました: {str(e)}')

@app.route('/<path:encoded_id>', methods=['GET'])
def redirect_to_original(encoded_id):
    """Redirect to the original URL from an encoded ID"""
    try:
        # Check if the encoded ID exists in our database
        url_mapping = URLMapping.query.filter_by(encoded_id=encoded_id).first()
        
        if url_mapping:
            # Increment access count
            url_mapping.access_count += 1
            db.session.commit()
            return redirect(url_mapping.original_url)
        
        # If not in database, try to decode it directly
        original_url = decode_url(encoded_id)
        if original_url:
            return redirect(original_url)
        
        return render_template('error.html', message='無効なURLまたはリンクが見つかりません'), 404
        
    except Exception as e:
        logger.exception(f"Error redirecting to original URL: {str(e)}")
        return render_template('error.html', message=f'エラーが発生しました: {str(e)}'), 500

@app.route('/api/encode', methods=['POST'])
def api_encode_url():
    """API endpoint to encode a URL"""
    try:
        data = request.get_json()
        if not data or 'url' not in data:
            return jsonify({'error': 'URL parameter is required'}), 400
            
        url = data['url']
        
        # Make sure URL has a scheme
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            
        # Check if this URL has already been encoded
        existing_mapping = URLMapping.query.filter_by(original_url=url).first()
        if existing_mapping:
            return jsonify({
                'original_url': url,
                'encoded_url': request.host_url + existing_mapping.encoded_id,
                'tiny_url': shortener.tinyurl.short(request.host_url + existing_mapping.encoded_id)
            })
        
        # Encode the URL
        encoded_id = encode_url(url)
        
        # Save to database
        url_mapping = URLMapping(original_url=url, encoded_id=encoded_id)
        db.session.add(url_mapping)
        db.session.commit()
        
        # Return the encoded URL
        return jsonify({
            'original_url': url,
            'encoded_url': request.host_url + encoded_id,
            'tiny_url': shortener.tinyurl.short(request.host_url + encoded_id)
        })
        
    except Exception as e:
        logger.exception(f"API error encoding URL: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', message='ページが見つかりません'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('error.html', message='サーバーエラーが発生しました'), 500