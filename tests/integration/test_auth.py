"""Интеграционные тесты аутентификации app/auth.py."""
import pytest
from urllib.parse import urlparse

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


@pytest.mark.usefixtures("methodist")
def test_successful_login_redirect_to_dashboard(client):
    response = client.post("/login", data={"username": "admin", "password": "admin123"})
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")


@pytest.mark.usefixtures("methodist")
@pytest.mark.parametrize("username, password", [
    pytest.param("admin", "WRONGpassword", id="wrong_password"),
    pytest.param("admin", "ADMIN123", id="password_case_differs"),  # пароль чувствителен к регистру
    pytest.param("admin", "", id="empty_password"),  # логин верный, пароль не введён
    pytest.param("UNKNOWN_USER", "admin123", id="unknown_user"),  # такого пользователя нет в базе
    pytest.param("", "", id="empty_form"),  # оба поля пустые
])
def test_login_is_rejected(client, username, password):
    response = client.post("/login", data={"username": username, "password": password})
    assert response.status_code == 200
    assert "Неверный логин или пароль" in response.get_data(as_text=True)
    assert client.get("/").status_code == 302  # сессия не создана, главная по-прежнему закрыта


@pytest.mark.usefixtures("methodist")
def test_login_strips_whitespace_around_username(client):
    response = client.post("/login", data={"username": "  admin  ", "password": "admin123"})
    assert response.status_code == 302


@pytest.mark.usefixtures("methodist")
def test_after_login_protected_pages_are_available(client):
    response = client.post("/login", data={"username": "admin", "password": "admin123"})
    for url in PROTECTED_URLS:
        if url in ["/journal/new", "/logout"]: # "/logout" в PROTECTED_URLS стоит последним, поэтому все остальные страницы проверяются норм, при логаут редирект на логин (302), журанал пока пустой (302)
            assert client.get(url).status_code == 302
        else:
            assert client.get(url).status_code == 200


@pytest.mark.usefixtures("methodist")
def test_logout_shows_confirmation_message(client):
    client.post("/login", data={"username": "admin", "password": "admin123"})
    response = client.get("/logout", follow_redirects=True)
    assert "Вы вышли из системы" in response.get_data(as_text=True)


@pytest.mark.parametrize("url", PROTECTED_URLS)
def test_protected_pages_redirect_anonymous_user_to_login(client, url):
    # без входа в систему доступ к любой странице, кроме /login, закрыт.
    response = client.get(url)
    assert response.status_code == 302
    assert urlparse(response.headers["Location"]).path == "/login"