from extensions import db
from datetime import datetime

class Order(db.Model):
    __tablename__ = "order"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    user = db.relationship(
        "User",
        back_populates="orders"
    )

    total_amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(50))
    payment_status = db.Column(db.String(50), default="Pending")
    order_status = db.Column(db.String(50), default="Placed")

    order_items = db.relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan"
    )


    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(100), nullable=False)
    pincode = db.Column(db.String(10), nullable=False)

    razorpay_order_id = db.Column(db.String(100))
    razorpay_payment_id = db.Column(db.String(100))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
