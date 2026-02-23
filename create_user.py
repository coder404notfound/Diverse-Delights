from app import app
from extensions import db
from models.user import User
from werkzeug.security import generate_password_hash


def create_user(
    email,
    password,
    first_name,
    last_name,
    contact_number,
    is_admin=False,
):
    with app.app_context():

        existing = User.query.filter_by(email=email).first()
        if existing:
            print("User already exists.")
            return

        hashed_password = generate_password_hash(password)

        user = User(
            email=email.lower(),
            contact_number=contact_number,
            first_name=first_name,
            last_name=last_name,
            password_hash=hashed_password,
            is_admin=is_admin,
        )

        db.session.add(user)
        db.session.commit()

        print("User created successfully.")
        if is_admin:
            print("Admin privileges granted.")


# ---- EDIT VALUES BELOW ----
if __name__ == "__main__":
    create_user(
        email="diverse.delights.2024@gmail.com",
        password="@JIAAS_sh0p!",
        first_name="Diverse",
        last_name="Delights",
        contact_number="8918612491",
        is_admin=True,  # Admin account
    )
