
from flask import Flask, render_template, request, redirect, url_for
import os
import secrets

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET") or secrets.token_hex(16)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/create_short_url', methods=['POST'])
def create_short_url():
    url = request.form.get('url')
    if not url:
        return render_template('error.html', message='URLを入力してください')
    
    # URLにスキームがない場合は追加
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
        
    from src.mais.url_crypto import encode_url
    encoded_id = encode_url(url)
    if not encoded_id:
        return render_template('error.html', message='URLの暗号化に失敗しました')
    
    proxy_url = request.host_url + encoded_id
    return render_template('result.html', tiny_url=proxy_url, original_url=url)

@app.route('/<encoded_id>')
def redirect_to_url(encoded_id):
    from src.mais.url_crypto import decode_url
    from src.mais.proxy_utils import fetch_content
    from src.mais.content_processor import process_content
    
    original_url = decode_url(encoded_id)
    if not original_url:
        return render_template('error.html', message='無効なURLです')
        
    # 元のコンテンツを取得
    content, status_code, content_type = fetch_content(original_url)
    if status_code != 200:
        return render_template('error.html', message='コンテンツの取得に失敗しました')
        
    # コンテンツを処理してプロキシ化
    processed_content = process_content(content, original_url, request.host_url)
    
    response = app.make_response(processed_content)
    response.headers['Content-Type'] = content_type
    return response

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
