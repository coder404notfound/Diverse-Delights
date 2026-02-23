from extensions import db
from datetime import datetime
from models.wishlist import wishlist_products

class Product(db.Model):    
    __tablename__ = "product"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    image_url = db.Column(db.String(500), nullable=False)

    category_id = db.Column(
        db.Integer,
        db.ForeignKey("category.id"),
        nullable=False
    )

    stock = db.Column(db.Integer, default=0)
    discount = db.Column(db.Integer, default=0)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    category = db.relationship(
        "Category",
        back_populates="products"
    )

    review = db.relationship(
        "Review",
        back_populates="product",
        cascade="all, delete-orphan"
    )

    wishlists = db.relationship(
        "Wishlist",
        secondary=wishlist_products,
        back_populates="products"
    )

    @property
    def average_rating(self):
        if not self.review:
            return 0
        return sum(r.rating for r in self.review) / len(self.review)
