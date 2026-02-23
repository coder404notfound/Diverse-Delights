from extensions import db
from datetime import datetime

class Review(db.Model):
    __tablename__ = "review"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    product_id = db.Column(
        db.Integer,
        db.ForeignKey("product.id"),
        nullable=False
    )

    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text, nullable=False)

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    __table_args__ = (
        db.UniqueConstraint(
            "user_id",
            "product_id",
            name="unique_user_product_review"
        ),
    )

    user = db.relationship(
        "User",
        back_populates="reviews"
    )

    product = db.relationship(
        "Product",
        back_populates="review"
    )

