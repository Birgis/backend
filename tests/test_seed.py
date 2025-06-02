import pytest
from seed import seed_database
from app.database import SessionLocal
from app.models import User, Post, Comment
from sqlalchemy.orm import Session
from app.auth import get_password_hash
from sqlalchemy.exc import IntegrityError


def test_seed_database(db: Session):
    # Clear existing data
    db.query(Comment).delete()
    db.query(Post).delete()
    db.query(User).delete()
    db.commit()

    # Create test users
    test_users = [
        User(
            user_name="testuser1",
            email="test1@example.com",
            password_hash=get_password_hash("password123"),
        ),
        User(
            user_name="testuser2",
            email="test2@example.com",
            password_hash=get_password_hash("password123"),
        ),
    ]
    db.add_all(test_users)
    db.commit()

    # Create test posts
    test_posts = [
        Post(content="Test post 1", author_id=test_users[0].id),
        Post(content="Test post 2", author_id=test_users[1].id),
    ]
    db.add_all(test_posts)
    db.commit()

    # Create test comments
    test_comments = [
        Comment(
            content="Test comment 1",
            author_id=test_users[0].id,
            post_id=test_posts[0].id,
        ),
        Comment(
            content="Test comment 2",
            author_id=test_users[1].id,
            post_id=test_posts[1].id,
        ),
    ]
    db.add_all(test_comments)
    db.commit()

    # Verify users were created
    users = db.query(User).all()
    assert len(users) == 2

    # Verify posts were created
    posts = db.query(Post).all()
    assert len(posts) == 2

    # Verify comments were created
    comments = db.query(Comment).all()
    assert len(comments) == 2

    # Verify relationships
    for post in posts:
        assert post.author is not None
        assert len(post.comments) > 0

    for comment in comments:
        assert comment.author is not None
        assert comment.post is not None


def test_seed_database_error_handling(db: Session):
    # Create a user that will cause a duplicate key error
    user = User(
        user_name="user",
        email="user@example.com",
        password_hash=get_password_hash("user"),
    )
    db.add(user)
    db.commit()

    # Try to seed the database, which should fail due to duplicate user
    with pytest.raises(IntegrityError):
        # Create another user with the same username
        duplicate_user = User(
            user_name="user",  # Same username as above
            email="another@example.com",
            password_hash=get_password_hash("user"),
        )
        db.add(duplicate_user)
        db.commit()  # This should raise IntegrityError

    # Rollback the session after the IntegrityError
    db.rollback()

    # Verify the database was rolled back
    users = db.query(User).filter(User.user_name == "user").all()
    assert len(users) == 1  # Only our manually created user, not the duplicate one


def test_seed_database_normal(monkeypatch):
    from seed import seed_database
    from app.models import User
    from app.database import SessionLocal

    # Use a fresh DB for this test
    db = SessionLocal()
    db.query(User).delete()
    db.commit()
    db.close()

    # Patch print to avoid clutter
    monkeypatch.setattr("builtins.print", lambda *a, **k: None)

    seed_database()

    db = SessionLocal()
    users = db.query(User).all()
    user_names = {u.user_name for u in users}
    assert "user" in user_names
    assert "admin" in user_names
    db.close()


def test_seed_database_error(monkeypatch):
    from seed import seed_database
    from app.models import User
    from app.database import SessionLocal

    # Use a fresh DB for this test
    db = SessionLocal()
    db.query(User).delete()
    db.commit()
    db.close()

    # Patch print to capture output
    printed = {}

    def fake_print(*args, **kwargs):
        printed["msg"] = args[0] if args else ""

    monkeypatch.setattr("builtins.print", fake_print)

    # Patch db.add to raise an exception
    import seed as seed_module

    orig_add = seed_module.SessionLocal().add

    def raise_exc(*a, **k):
        raise Exception("fail add")

    monkeypatch.setattr(seed_module.SessionLocal().__class__, "add", raise_exc)

    seed_database()
    assert "Error seeding database" in printed["msg"]
