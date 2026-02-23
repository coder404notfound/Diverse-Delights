from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta

db = SQLAlchemy()

class ResetOTP(db.Model):    
    __tablename__ = "reset_otp"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True)
    otp = db.Column(db.String(6))
    expires_at = db.Column(db.DateTime)

    def is_valid(self):
        return datetime.utcnow() < self.expires_at
