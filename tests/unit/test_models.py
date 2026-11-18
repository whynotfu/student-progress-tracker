"""Юнит-тесты моделей app/models.py)"""
import pytest

from app.models import (
    CREDIT_GRADES,
    ROLE_METHODIST,
    ROLE_TEACHER,
    Curriculum,
    Student,
    User,
)

# USER
def test_user_set_password_as_hash():
    new_user = User()
    new_user.set_password("ILoveEchpochmac")
    assert new_user.password_hash != "ILoveEchpochmac"
    assert "ILoveEchpochmac" not in new_user.password_hash
    assert len(new_user.password_hash) > 20


def test_same_password_gives_different_hashes_because_of_salt():
    first, second = User(), User()
    first.set_password("secret123")
    second.set_password("secret123")
    assert first.password_hash != second.password_hash


def test_user_check_password_valid():
    new_user = User()
    new_user.set_password("ILoveEchpochmac")
    assert new_user.check_password("ILoveEchpochmac") is True


@pytest.mark.parametrize("wrong", [
    "secret124", "SECRET123", "", " secret123", "secret123 "
    ])
def test_check_password_rejects_wrong_password(wrong):
    new_user = User()
    new_user.set_password("secret123")
    assert new_user.check_password(wrong) is False


def test_is_methodist_true_for_methodist_role():
    assert User(role=ROLE_METHODIST).is_methodist is True


def test_is_methodist_false_for_teacher_role():
    assert User(role=ROLE_TEACHER).is_methodist is False


@pytest.mark.parametrize("role, label", [
    (ROLE_METHODIST, "Сотрудник учебного отдела"),
    (ROLE_TEACHER, "Преподаватель")
    ])
def test_role_label_for_known_roles(role, label):
    assert User(role=role).role_label == label


def test_role_label_for_unknown_role_returns_role_itself():
    assert User(role="guest").role_label == "guest"


# STUDENT
def test_student_full_name_with_patronymic():
    student = Student(last_name="Удзумаки", first_name="Наруто", patronymic="Минатович")
    assert student.full_name == "Удзумаки Наруто Минатович"


@pytest.mark.parametrize("patronymic", [
    None, 
    ""
    ])
def test_student_full_name_without_patronymic(patronymic):
    student = Student(last_name="Удзумаки", first_name="Наруто", patronymic=patronymic)
    assert student.full_name == "Удзумаки Наруто"


# CURRICULUM 
def test_allowed_grades_for_exam():
    assert Curriculum(report_form="экзамен").allowed_grades == ["2", "3", "4", "5"]


def test_allowed_grades_for_credit():
    assert Curriculum(report_form="зачет").allowed_grades == ["зачет", "незачет"]