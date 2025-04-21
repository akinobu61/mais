
import os
from flask import Flask, render_template, request, redirect, url_for
import secrets

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET") or secrets.token_hex(16)

# ... rest of your route handlers ...

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
