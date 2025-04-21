from app import db
from datetime import datetime

class URLMapping(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    original_url = db.Column(db.String(2048), nullable=False)
    encoded_id = db.Column(db.String(128), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    access_count = db.Column(db.Integer, default=0)
    
    def __repr__(self):
        return f'<URLMapping {self.encoded_id}: {self.original_url}>'