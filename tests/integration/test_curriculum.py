"""Интеграционные тесты раздела «Учебный план» маршруты /curriculum."""
from urllib.parse import urlparse

import pytest

from app.models import Curriculum, JournalEntry


def curriculum_form(**overrides):
    """Корректные данные формы учебного плана; отдельные поля можно заменить."""
    data = {
        "speciality": "Программная инженерия",
        "discipline": "Базы данных",
        "semester": "5",
        "hours": "108",
        "report_form": "экзамен",
        "teacher_id": "",
    }
    data.update(overrides)
    return data


def test_curriculum_list_shows_items_for_teacher(teacher_client, add_curriculum):
    add_curriculum(discipline="Операционные системы")
    response = teacher_client.get("/curriculum")
    assert response.status_code == 200
    assert "Операционные системы" in response.get_data(as_text=True)


def test_curriculum_list_shows_assigned_teacher(methodist_client, add_curriculum, teacher):
    add_curriculum(teacher_id=teacher)
    assert "Тестовый Препод" in methodist_client.get("/curriculum").get_data(as_text=True)


def test_curriculum_list_is_sorted_by_speciality_then_semester(methodist_client, add_curriculum):
    add_curriculum(speciality="Бета", discipline="Дисц-В", semester=1)
    add_curriculum(speciality="Альфа", discipline="Дисц-Б", semester=6)
    add_curriculum(speciality="Альфа", discipline="Дисц-А", semester=2)
    text = methodist_client.get("/curriculum").get_data(as_text=True)
    assert text.index("Дисц-А") < text.index("Дисц-Б") < text.index("Дисц-В")


def test_add_button_is_visible_only_for_methodist(methodist_client, teacher_client):
    assert "Добавить запись" in methodist_client.get("/curriculum").get_data(as_text=True)
    assert "Добавить запись" not in teacher_client.get("/curriculum").get_data(as_text=True)


def test_new_form_offers_only_teachers_for_assignment(methodist_client, teacher, other_teacher):
    """В списке «Преподаватель» есть преподаватели, но нет методиста."""
    text = methodist_client.get("/curriculum/new").get_data(as_text=True)
    assert "Тестовый Препод" in text
    assert "Другой Препод" in text
    # имя методиста встречается один раз - в шапке сайта, в выпадающем списке его нет.
    assert text.count("Тестовый Методист") == 1


def test_methodist_creates_curriculum_item(methodist_client, teacher, count_rows, get_row):
    """Методист добавляет запись: редирект и запись в БД с закреплённым преподавателем."""
    response = methodist_client.post("/curriculum/new",
                                     data=curriculum_form(teacher_id=str(teacher)))
    assert response.status_code == 302
    assert urlparse(response.headers["Location"]).path == "/curriculum"
    assert count_rows(Curriculum) == 1
    item = get_row(Curriculum, 1)
    assert item.speciality == "Программная инженерия"
    assert item.discipline == "Базы данных"
    assert (item.semester, item.hours) == (5, 108)
    assert item.report_form == "экзамен"
    assert item.teacher_id == teacher


def test_create_curriculum_without_teacher_stores_null(methodist_client, get_row):
    methodist_client.post("/curriculum/new", data=curriculum_form(teacher_id=""))
    assert get_row(Curriculum, 1).teacher_id is None


def test_create_curriculum_strips_text_fields(methodist_client, get_row):
    methodist_client.post("/curriculum/new", data=curriculum_form(
        speciality="  Информатика ", discipline=" Сети  "))
    item = get_row(Curriculum, 1)
    assert (item.speciality, item.discipline) == ("Информатика", "Сети")


@pytest.mark.parametrize("field, value, message", [
    pytest.param("semester", "0", "не меньше 1", id="semester_below_minimum"),
    pytest.param("semester", "13", "не больше 12", id="semester_above_maximum"),
    pytest.param("semester", "abc", "должно быть целым числом", id="semester_not_a_number"),
    pytest.param("hours", "0", "не меньше 1", id="hours_zero"),
    pytest.param("hours", "-5", "не меньше 1", id="hours_negative"),
    pytest.param("hours", "много", "должно быть целым числом", id="hours_not_a_number"),
    pytest.param("teacher_id", "abc", "должно быть целым числом", id="teacher_not_a_number"),
])
def test_create_curriculum_with_invalid_number_is_rejected(methodist_client, count_rows,
                                                           field, value, message):
    # страница формы с ошибкой, запись не создаётся.
    response = methodist_client.post("/curriculum/new", data=curriculum_form(**{field: value}))
    assert response.status_code == 200
    assert message in response.get_data(as_text=True)
    assert count_rows(Curriculum) == 0


@pytest.mark.parametrize("semester", [
    pytest.param("1", id="first_semester"),
    pytest.param("12", id="last_semester"),
])
def test_create_curriculum_accepts_boundary_semesters(methodist_client, count_rows, semester):
    response = methodist_client.post("/curriculum/new", data=curriculum_form(semester=semester))
    assert response.status_code == 302
    assert count_rows(Curriculum) == 1


def test_teacher_cannot_create_curriculum_item(teacher_client, count_rows):
    assert teacher_client.get("/curriculum/new").status_code == 403
    assert teacher_client.post("/curriculum/new", data=curriculum_form()).status_code == 403
    assert count_rows(Curriculum) == 0


def test_methodist_updates_curriculum_item(methodist_client, add_curriculum, teacher, get_row):
    item_id = add_curriculum()
    response = methodist_client.post(f"/curriculum/{item_id}/edit", data=curriculum_form(
        discipline="Сети ЭВМ", semester="6", hours="72", report_form="зачет",
        teacher_id=str(teacher)))
    assert response.status_code == 302
    item = get_row(Curriculum, item_id)
    assert item.discipline == "Сети ЭВМ"
    assert (item.semester, item.hours) == (6, 72)
    assert item.report_form == "зачет"
    assert item.teacher_id == teacher


def test_edit_can_remove_assigned_teacher(methodist_client, add_curriculum, teacher, get_row):
    item_id = add_curriculum(teacher_id=teacher)
    methodist_client.post(f"/curriculum/{item_id}/edit", data=curriculum_form(teacher_id=""))
    assert get_row(Curriculum, item_id).teacher_id is None


def test_edit_with_invalid_hours_keeps_old_values(methodist_client, add_curriculum, get_row):
    item_id = add_curriculum(discipline="Старая", hours=108)
    response = methodist_client.post(f"/curriculum/{item_id}/edit",
                                     data=curriculum_form(discipline="Новая", hours="0"))
    assert response.status_code == 200
    item = get_row(Curriculum, item_id)
    assert (item.discipline, item.hours) == ("Старая", 108)


def test_edit_unknown_curriculum_item_returns_404(methodist_client):
    assert methodist_client.get("/curriculum/999/edit").status_code == 404


def test_teacher_cannot_edit_curriculum_item(teacher_client, add_curriculum, get_row):
    item_id = add_curriculum(discipline="Старая")
    assert teacher_client.get(f"/curriculum/{item_id}/edit").status_code == 403
    assert teacher_client.post(f"/curriculum/{item_id}/edit",
                               data=curriculum_form(discipline="Новая")).status_code == 403
    assert get_row(Curriculum, item_id).discipline == "Старая"



def test_methodist_deletes_curriculum_item(methodist_client, add_curriculum, count_rows):
    item_id = add_curriculum()
    response = methodist_client.post(f"/curriculum/{item_id}/delete")
    assert response.status_code == 302
    assert urlparse(response.headers["Location"]).path == "/curriculum"
    assert count_rows(Curriculum) == 0


def test_deleting_curriculum_item_deletes_its_journal_entries(methodist_client, add_student,
                                                              add_curriculum, add_entry, count_rows):
    # каскадом вместе с дисциплиной удаляются оценки по ней.
    student_id = add_student()
    item_id = add_curriculum()
    add_entry(student_id, item_id)
    methodist_client.post(f"/curriculum/{item_id}/delete")
    assert count_rows(JournalEntry) == 0


def test_delete_curriculum_requires_post(methodist_client, add_curriculum, count_rows):
    item_id = add_curriculum()
    assert methodist_client.get(f"/curriculum/{item_id}/delete").status_code == 405
    assert count_rows(Curriculum) == 1


def test_teacher_cannot_delete_curriculum_item(teacher_client, add_curriculum, count_rows):
    item_id = add_curriculum()
    assert teacher_client.post(f"/curriculum/{item_id}/delete").status_code == 403
    assert count_rows(Curriculum) == 1
