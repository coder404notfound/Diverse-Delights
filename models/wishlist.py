from extensions import db

wishlist_products = db.Table(
    "wishlist_products",
    db.Column("wishlist_id", db.Integer, db.ForeignKey("wishlist.id")),
    db.Column("product_id", db.Integer, db.ForeignKey("product.id"))
)

class Wishlist(db.Model):
    __tablename__ = "wishlist"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    user = db.relationship(
        "User",
        back_populates="wishlist"
    )

    products = db.relationship(
        "Product",
        secondary=wishlist_products,
        back_populates="wishlists"
    )
