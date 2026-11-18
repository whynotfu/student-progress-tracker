"""Интеграционные тесты раздела «Контингент студентов» маршруты /students."""
from datetime import date
from urllib.parse import urlparse

import pytest

from app.models import JournalEntry, Student

CURRENT_YEAR = date.today().year


def student_form(**overrides):
    """Корректные данные формы студента; отдельные поля можно заменить."""
    data = {
        "last_name": "Дубина",
        "first_name": "Анастасия",
        "patronymic": "Александровна",
        "admission_year": "2023",
        "study_form": "дневная",
        "group_name": "241-327",
    }
    data.update(overrides)
    return data


def test_students_list_shows_students_for_teacher(teacher_client, add_student):
    add_student(last_name="Петров")
    response = teacher_client.get("/students")
    assert response.status_code == 200
    assert "Петров" in response.get_data(as_text=True)


def test_students_list_empty_shows_placeholder(methodist_client):
    assert "Нет данных" in methodist_client.get("/students").get_data(as_text=True)


def test_students_list_is_sorted_by_last_name(methodist_client, add_student):
    add_student(last_name="Минок")
    add_student(last_name="Конарев")
    add_student(last_name="Дубина")
    text = methodist_client.get("/students").get_data(as_text=True)
    assert text.index("Дубина") < text.index("Конарев") < text.index("Минок")


def test_add_button_is_visible_only_for_methodist(methodist_client, teacher_client):
    assert "Добавить студента" in methodist_client.get("/students").get_data(as_text=True)
    assert "Добавить студента" not in teacher_client.get("/students").get_data(as_text=True)


def test_new_student_form_opens_for_methodist(methodist_client):
    assert methodist_client.get("/students/new").status_code == 200


def test_methodist_creates_student(methodist_client, count_rows, get_row):
    response = methodist_client.post("/students/new", data=student_form())
    assert response.status_code == 302
    assert urlparse(response.headers["Location"]).path == "/students"
    assert count_rows(Student) == 1
    student = get_row(Student, 1)
    assert (student.last_name, student.first_name, student.patronymic) == ("Дубина", "Анастасия", "Александровна")
    assert student.admission_year == 2023
    assert student.study_form == "дневная"
    assert student.group_name == "241-327"


def test_create_student_shows_success_message(methodist_client):
    response = methodist_client.post("/students/new", data=student_form(), follow_redirects=True)
    assert "Студент добавлен" in response.get_data(as_text=True)


def test_create_student_strips_whitespace(methodist_client, get_row):
    methodist_client.post("/students/new", data=student_form(
        last_name="  Конарев ", first_name=" Илья  ", group_name=" 241-327 "))
    student = get_row(Student, 1)
    assert (student.last_name, student.first_name, student.group_name) == ("Конарев", "Илья", "241-327")


def test_create_student_without_patronymic(methodist_client, get_row):
    methodist_client.post("/students/new", data=student_form(patronymic=""))
    assert get_row(Student, 1).full_name == "Дубина Анастасия"


@pytest.mark.parametrize("year, message", [
    ("abc", "должно быть целым числом"),  # not a number
    ("", "должно быть целым числом"),  # empty
    ("1999", "не меньше 2000"),  # below minimum year
    (str(CURRENT_YEAR + 1), f"не больше {CURRENT_YEAR}"),  # year in future
])
def test_create_student_with_invalid_year_is_rejected(methodist_client, count_rows, year, message):
    response = methodist_client.post("/students/new", data=student_form(admission_year=year))
    assert response.status_code == 200
    assert message in response.get_data(as_text=True)
    assert count_rows(Student) == 0


@pytest.mark.parametrize("year", [
    "2000",  # minimum year
    str(CURRENT_YEAR),  # current year
])
def test_create_student_accepts_boundary_years(methodist_client, count_rows, year):
    response = methodist_client.post("/students/new", data=student_form(admission_year=year))
    assert response.status_code == 302
    assert count_rows(Student) == 1


def test_teacher_cannot_open_new_student_form(teacher_client):
    response = teacher_client.get("/students/new")
    assert response.status_code == 403
    assert "Недостаточно прав" in response.get_data(as_text=True)


def test_teacher_cannot_create_student(teacher_client, count_rows):
    assert teacher_client.post("/students/new", data=student_form()).status_code == 403
    assert count_rows(Student) == 0


def test_anonymous_cannot_create_student(client, count_rows):
    response = client.post("/students/new", data=student_form())
    assert response.status_code == 302
    assert urlparse(response.headers["Location"]).path == "/login"
    assert count_rows(Student) == 0


def test_edit_form_shows_current_student(methodist_client, add_student):
    student_id = add_student(last_name="Сидоров")
    response = methodist_client.get(f"/students/{student_id}/edit")
    assert response.status_code == 200
    assert "Сидоров" in response.get_data(as_text=True)


def test_methodist_updates_student(methodist_client, add_student, get_row):
    student_id = add_student()
    response = methodist_client.post(f"/students/{student_id}/edit", data=student_form(
        last_name="Новиков", admission_year="2022", study_form="заочная", group_name="241-330"))
    assert response.status_code == 302
    student = get_row(Student, student_id)
    assert student.last_name == "Новиков"
    assert student.admission_year == 2022
    assert student.study_form == "заочная"
    assert student.group_name == "241-330"


def test_edit_with_invalid_year_keeps_old_values(methodist_client, add_student, get_row):
    student_id = add_student(last_name="Старая", admission_year=2023)
    response = methodist_client.post(f"/students/{student_id}/edit",
                                     data=student_form(last_name="Новая", admission_year="abc"))
    assert response.status_code == 200
    student = get_row(Student, student_id)
    assert (student.last_name, student.admission_year) == ("Старая", 2023)


def test_edit_unknown_student_returns_404(methodist_client):
    response = methodist_client.get("/students/999/edit")
    assert response.status_code == 404
    assert "Страница не найдена" in response.get_data(as_text=True)


def test_teacher_cannot_edit_student(teacher_client, add_student, get_row):
    student_id = add_student(last_name="Старая")
    assert teacher_client.get(f"/students/{student_id}/edit").status_code == 403
    assert teacher_client.post(f"/students/{student_id}/edit",
                               data=student_form(last_name="Новая")).status_code == 403
    assert get_row(Student, student_id).last_name == "Старая"


def test_methodist_deletes_student(methodist_client, add_student, count_rows):
    student_id = add_student()
    response = methodist_client.post(f"/students/{student_id}/delete")
    assert response.status_code == 302
    assert count_rows(Student) == 0


def test_delete_unknown_student_returns_404(methodist_client):
    assert methodist_client.post("/students/999/delete").status_code == 404


def test_teacher_cannot_delete_student(teacher_client, add_student, count_rows):
    student_id = add_student()
    assert teacher_client.post(f"/students/{student_id}/delete").status_code == 403
    assert count_rows(Student) == 1
