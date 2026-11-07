"""Интеграционные тесты аутентификации app/auth.py."""
import pytest

PROTECTED_URLS = [
    "/",
    "/students",
    "/students/new",
    "/curriculum",
    "/curriculum/new",
    "/journal",
    "/journal/new",
    "/reports/by-form",
    "/reports/by-discipline",
    "/logout",
]


def test_login_page_opens_for_anonymous_user(client):
    response = client.get("/login")
    assert response.status_code == 200