"""Интеграционные тесты моделей и БД"""
import pytest
from sqlalchemy.exc import IntegrityError

from app.models import ROLE_TEACHER, Curriculum, JournalEntry, Student, User, db


def test_user_role_defaults_to_teacher(flask_app):
    with flask_app.app_context():
        user = User(username="new", password_hash="x", full_name="Новый Пользователь")
        db.session.add(user)
        db.session.commit()
        assert user.role == ROLE_TEACHER


def test_username_must_be_unique(flask_app, teacher):
    with flask_app.app_context():
        db.session.add(User(username="teacher", password_hash="x", full_name="Дубликат"))
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()


def test_student_requires_last_name(flask_app):
    with flask_app.app_context():
        db.session.add(Student(first_name="Настя", admission_year=2023,
                               study_form="дневная", group_name="241-327"))
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()


def test_journal_entry_relations_resolve(flask_app, add_student, add_curriculum, add_entry, teacher):
    # запись журнала связана со студентом и дисциплиной, дисциплина с преподавателем.
    student_id = add_student(last_name="Конарев", first_name="Илья", patronymic=None)
    curriculum_id = add_curriculum(discipline="Базы данных", teacher_id=teacher)
    entry_id = add_entry(student_id, curriculum_id)
    with flask_app.app_context():
        entry = db.session.get(JournalEntry, entry_id)
        assert entry.student.full_name == "Конарев Илья"
        assert entry.curriculum.discipline == "Базы данных"
        assert entry.curriculum.teacher.username == "teacher"


def test_deleting_student_keeps_curriculum(flask_app, add_student, add_curriculum, add_entry):
    # удаление студента -> удаление его оценое, но не трогает учебный план.
    student_id = add_student()
    add_entry(student_id, add_curriculum())
    with flask_app.app_context():
        db.session.delete(db.session.get(Student, student_id))
        db.session.commit()
        assert JournalEntry.query.count() == 0
        assert Curriculum.query.count() == 1


def test_deleting_curriculum_keeps_student(flask_app, add_student, add_curriculum, add_entry):
    # удаление дисциплины убирает оценки по ней, но не трогает студентов.
    curriculum_id = add_curriculum()
    add_entry(add_student(), curriculum_id)
    with flask_app.app_context():
        db.session.delete(db.session.get(Curriculum, curriculum_id))
        db.session.commit()
        assert JournalEntry.query.count() == 0
        assert Student.query.count() == 1
