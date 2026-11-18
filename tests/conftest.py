"""
фикстурки для тестов.
"""
import pytest

from app import create_app
from app.models import (db, ROLE_METHODIST, User,
                        ROLE_TEACHER, Student, Curriculum, JournalEntry)


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


@pytest.fixture
def methodist(flask_app):
    with flask_app.app_context():
        user = User(username="admin", role=ROLE_METHODIST, full_name="Тестовый Методист")
        user.set_password("admin123")
        db.session.add(user)
        db.session.commit()
        return user.id


@pytest.fixture
def teacher(flask_app):
    with flask_app.app_context():
        user = User(username="teacher", role=ROLE_TEACHER, full_name="Тестовый Препод")
        user.set_password("teacher123")
        db.session.add(user)
        db.session.commit()
        return user.id


@pytest.fixture
def other_teacher(flask_app):
    """Второй преподаватель: нужен, чтобы проверять доступ к «чужим» дисциплинам."""
    with flask_app.app_context():
        user = User(username="teacher2", role=ROLE_TEACHER, full_name="Другой Препод")
        user.set_password("teacher123")
        db.session.add(user)
        db.session.commit()
        return user.id


# ниже каждая фикстура создает совй клиент фласка, а не общий client
# чтобы куки разные были и тесты не падали.
def _login(app, username, password):
    c = app.test_client()
    c.post("/login", data={"username": username, "password": password})
    return c


@pytest.fixture
def methodist_client(flask_app, methodist):
    return _login(flask_app, "admin", "admin123")


@pytest.fixture
def teacher_client(flask_app, teacher):
    return _login(flask_app, "teacher", "teacher123")


@pytest.fixture
def other_teacher_client(flask_app, other_teacher):
    return _login(flask_app, "teacher2", "teacher123")



# Ниже фикстуры возвращают функцию, которой тест сам создаёт нужные записи.
# Каждая функция возвращает id созданной записи.
@pytest.fixture
def add_student(flask_app):
    def _add(last_name="Иванов", first_name="Иван", patronymic="Иванович",
             admission_year=2023, study_form="дневная", group_name="241-327"):
        with flask_app.app_context():
            student = Student(last_name=last_name, first_name=first_name,
                              patronymic=patronymic, admission_year=admission_year,
                              study_form=study_form, group_name=group_name)
            db.session.add(student)
            db.session.commit()
            return student.id
    return _add


@pytest.fixture
def add_curriculum(flask_app):
    def _add(speciality="Программная инженерия", discipline="Базы данных",
             semester=5, hours=108, report_form="экзамен", teacher_id=None):
        with flask_app.app_context():
            item = Curriculum(speciality=speciality, discipline=discipline,
                              semester=semester, hours=hours,
                              report_form=report_form, teacher_id=teacher_id)
            db.session.add(item)
            db.session.commit()
            return item.id
    return _add


@pytest.fixture
def add_entry(flask_app):
    def _add(student_id, curriculum_id, grade="5", academic_year="2025/2026"):
        with flask_app.app_context():
            entry = JournalEntry(academic_year=academic_year, student_id=student_id,
                                 curriculum_id=curriculum_id, grade=grade)
            db.session.add(entry)
            db.session.commit()
            return entry.id
    return _add


# чтобы проверять, что запрос реально изменил данные.
@pytest.fixture
def count_rows(flask_app):
    def _count(model):
        with flask_app.app_context():
            return model.query.count()
    return _count


@pytest.fixture
def get_row(flask_app):
    def _get(model, pk):
        with flask_app.app_context():
            return db.session.get(model, pk)
    return _get
