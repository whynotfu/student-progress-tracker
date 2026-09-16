# -*- coding: utf-8 -*-
import os

from flask import Flask, render_template
from flask_login import LoginManager
from flask_wtf import CSRFProtect

from .models import db, User

login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "Пожалуйста, войдите в систему."
login_manager.login_message_category = "warning"
csrf = CSRFProtect()


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
        "DATABASE_URL", "sqlite:///" + os.path.join(app.instance_path, "studgrade.db")
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    from .auth import auth_bp
    from .main import main_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)

    with app.app_context():
        db.create_all()

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    @app.errorhandler(403)
    def forbidden(_error):
        return render_template(
            "error.html", code=403, message="Недостаточно прав для выполнения действия."
        ), 403

    @app.errorhandler(404)
    def not_found(_error):
        return render_template("error.html", code=404, message="Страница не найдена."), 404

    @app.errorhandler(500)
    def server_error(_error):
        db.session.rollback()
        return render_template(
            "error.html", code=500, message="Внутренняя ошибка сервера. Проверьте введённые данные."
        ), 500

    return app
