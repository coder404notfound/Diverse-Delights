from extensions import db
from datetime import datetime

class CartItem(db.Model):
    __tablename__ = "cart_item"

    id = db.Column(db.Integer, primary_key=True)

    cart_id = db.Column(
        db.Integer,
        db.ForeignKey("cart.id"),
        nullable=False
    )

    product_id = db.Column(
        db.Integer,
        db.ForeignKey("product.id"),
        nullable=False
    )

    quantity = db.Column(db.Integer, nullable=False, default=1)

    cart = db.relationship("Cart", back_populates="items")
    product = db.relationship("Product")

class Cart(db.Model):
    __tablename__ = "cart"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        unique=True
    )

    user = db.relationship(
        "User",
        back_populates="cart"
    )

    items = db.relationship(
        "CartItem",
        back_populates="cart",
        cascade="all, delete-orphan"
    )
