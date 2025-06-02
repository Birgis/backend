import pytest
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from app.database import get_db, SessionLocal


def test_get_db_session():
    # Test that get_db yields a session and closes it properly
    db_gen = get_db()
    db = next(db_gen)
    assert db is not None
    assert isinstance(db, Session)

    # Test that the session is closed after use
    try:
        next(db_gen)
    except StopIteration:
        pass

    # Verify session is closed
    with pytest.raises(SQLAlchemyError):
        db.execute("SELECT 1")


def test_get_db_session_error_handling():
    # Test that get_db properly closes the session even if an error occurs
    db_gen = get_db()
    db = next(db_gen)

    # Simulate an error
    try:
        raise Exception("Test error")
    except Exception:
        try:
            next(db_gen)
        except StopIteration:
            pass

    # Verify session is closed
    with pytest.raises(SQLAlchemyError):
        db.execute("SELECT 1")
