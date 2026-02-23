from extensions import db
from datetime import datetime

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    product_name = db.Column(db.String(200))
    price = db.Column(db.Float)
    quantity = db.Column(db.Integer)
    product_image = db.Column(db.String(255))
    product_id = db.Column(db.Integer)

    order_id = db.Column(
        db.Integer,
        db.ForeignKey("order.id"),
        nullable=False
    )

    order = db.relationship(
        "Order",
        back_populates="order_items"
    )
