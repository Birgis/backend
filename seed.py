from app.database import SessionLocal, engine
from app.models import User, Base
from app.auth import get_password_hash

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)


def seed_database():
    db = SessionLocal()

    # Create regular user
    user = User(
        user_name="user",
        email="user@example.com",
        password_hash=get_password_hash("user"),
        is_admin=False,
    )

    # Create admin user
    admin = User(
        user_name="admin",
        email="admin@example.com",
        password_hash=get_password_hash("admin"),
        is_admin=True,
    )

    try:
        db.add(user)
        db.add(admin)
        db.commit()
        print("Database seeded successfully!")
    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":  # pragma: no cover
    seed_database()
