
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
    return render_template('result.html', tiny_url=url)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
