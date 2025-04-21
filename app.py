
import os
import secrets
from flask import Flask, render_template, request, redirect, url_for
from src.mais.url_crypto import encode_url, decode_url

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
    
    encoded_id = encode_url(url)
    if not encoded_id:
        return render_template('error.html', message='URLの暗号化に失敗しました')
    
    tiny_url = request.host_url + encoded_id
    return render_template('result.html', tiny_url=tiny_url, original_url=url)

@app.route('/<encoded_id>')
def redirect_to_url(encoded_id):
    original_url = decode_url(encoded_id)
    if not original_url:
        return render_template('error.html', message='無効なURLです')
    return redirect(original_url)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
