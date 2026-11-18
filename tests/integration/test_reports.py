"""Интеграционные тесты отчётов"""
import pytest


@pytest.fixture
def students_of_all_forms(add_student):
    add_student(last_name="А", study_form="дневная")
    add_student(last_name="Б", study_form="дневная")
    add_student(last_name="В", study_form="вечерняя")


@pytest.mark.parametrize("study_form, expected", [
    ("дневная", 2),  # two full time
    ("вечерняя", 1),  # one evening
    ("заочная", 0),  # студентов этой формы нет
    ("несуществующая", 0),  # такой формы нет вообще
])
def test_count_students_by_study_form(teacher_client, students_of_all_forms, study_form, expected):
    #отчёт считает только студентов выбранной формы обучения.
    response = teacher_client.post("/reports/by-form", data={"study_form": study_form})
    assert response.status_code == 200
    assert f"<strong>{expected}</strong>" in response.get_data(as_text=True)


def test_count_in_empty_database_is_zero(methodist_client):
    response = methodist_client.post("/reports/by-form", data={"study_form": "дневная"})
    assert "<strong>0</strong>" in response.get_data(as_text=True)


def test_by_form_without_field_returns_bad_request(methodist_client):
    assert methodist_client.post("/reports/by-form", data={}).status_code == 400


def test_by_form_report_requires_login(client):
    assert client.post("/reports/by-form", data={"study_form": "дневная"}).status_code == 302


def test_by_discipline_page_lists_unique_disciplines(teacher_client, add_curriculum):
    # в подсказках страницы каждая дисциплина один раз, даже если есть в нескольких семестрах.
    add_curriculum(discipline="Сети", semester=3)
    add_curriculum(discipline="Сети", semester=4)
    text = teacher_client.get("/reports/by-discipline").get_data(as_text=True)
    assert text.count('<option value="Сети">') == 1


def test_by_discipline_returns_hours_and_report_form(teacher_client, add_curriculum):
    add_curriculum(discipline="Базы данных", semester=5, hours=108, report_form="экзамен")
    response = teacher_client.post("/reports/by-discipline", data={"discipline": "Базы данных"})
    text = response.get_data(as_text=True)
    assert "<td>108</td>" in text
    assert "<td>экзамен</td>" in text


def test_by_discipline_unknown_discipline_shows_not_found_message(teacher_client, add_curriculum):
    add_curriculum(discipline="Базы данных")
    response = teacher_client.post("/reports/by-discipline", data={"discipline": "Астрология"})
    assert "не найдена в учебном плане" in response.get_data(as_text=True)


def test_by_discipline_without_field_returns_bad_request(methodist_client):
    assert methodist_client.post("/reports/by-discipline", data={}).status_code == 400


def test_by_discipline_report_requires_login(client):
    assert client.post("/reports/by-discipline", data={"discipline": "x"}).status_code == 302
