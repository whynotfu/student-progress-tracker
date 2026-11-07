"""
фикстурки для тестов.
"""
import pytest

from app import create_app
from app.models import db

@pytest.fixture
def flask_app(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite://") # подменим бд на оперативку, которая очиститья по завервшении теста
    app = create_app()
    app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
    yield app
    with app.app_context():
        db.session.remove()
        db.drop_all()

# на каждый тест свое приложение
@pytest.fixture
def client(flask_app):
    return flask_app.test_client()
                       

