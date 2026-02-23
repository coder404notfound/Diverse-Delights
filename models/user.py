from extensions import db
from datetime import datetime


class User(db.Model):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)

    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    contact_number = db.Column(db.String(20), nullable=False)

    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)

    password_hash = db.Column(db.String(255), nullable=False)

    is_admin = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    reviews = db.relationship(
        "Review",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    wishlist = db.relationship(
        "Wishlist",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )

    cart = db.relationship(
        "Cart",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )

    orders = db.relationship(
        "Order",
        back_populates="user",
        lazy=True
    )