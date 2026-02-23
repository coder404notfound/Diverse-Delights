from extensions import db
from datetime import datetime

class Category(db.Model):    
    __tablename__ = "category"

    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(100), unique=True, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    products = db.relationship(
        "Product",
        back_populates="category",
        cascade="all, delete-orphan"
    )