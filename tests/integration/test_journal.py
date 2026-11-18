"""Интеграционные тесты журнала успеваемости маршруты /journal*."""
from types import SimpleNamespace
from urllib.parse import urlparse

import pytest

from app.models import JournalEntry

INVALID_GRADE_TEXT = "Недопустимое значение оценки"


def entry_form(student_id, curriculum_id, grade="5", academic_year="2025/2026"):
    """Данные формы оценки."""
    return {
        "academic_year": academic_year,
        "student_id": str(student_id),
        "curriculum_id": str(curriculum_id),
        "grade": grade,
    }


@pytest.fixture
def data(add_student, add_curriculum, teacher, other_teacher):
    """Студент и три дисциплины: экзамен и зачёт у teacher, экзамен у other_teacher."""
    return SimpleNamespace(
        student=add_student(),
        exam=add_curriculum(discipline="Базы данных", report_form="экзамен", teacher_id=teacher),
        credit=add_curriculum(discipline="Физкультура", report_form="зачет", teacher_id=teacher),
        foreign=add_curriculum(discipline="Чужая дисциплина", report_form="экзамен",
                               teacher_id=other_teacher),
    )


def test_methodist_sees_all_journal_entries(methodist_client, add_entry, data):
    add_entry(data.student, data.exam)
    add_entry(data.student, data.foreign)
    text = methodist_client.get("/journal").get_data(as_text=True)
    assert "Базы данных" in text
    assert "Чужая дисциплина" in text
    assert "Показаны только оценки по дисциплинам, которые вы ведёте." not in text


def test_teacher_sees_only_entries_of_own_disciplines(teacher_client, add_entry, data):
    add_entry(data.student, data.exam)
    add_entry(data.student, data.foreign)
    text = teacher_client.get("/journal").get_data(as_text=True)
    assert "Базы данных" in text
    assert "Чужая дисциплина" not in text
    assert "Показаны только оценки по дисциплинам, которые вы ведёте." in text


def test_journal_list_is_sorted_by_academic_year_descending(methodist_client, add_entry, data):
    add_entry(data.student, data.exam, academic_year="2023/2024")
    add_entry(data.student, data.exam, academic_year="2025/2026")
    text = methodist_client.get("/journal").get_data(as_text=True)
    assert text.index("2025/2026") < text.index("2023/2024")


def test_teacher_adds_grade_for_own_discipline(teacher_client, data, count_rows, get_row):
    response = teacher_client.post("/journal/new", data=entry_form(
        data.student, data.exam, grade="5", academic_year=" 2025/2026 "))
    assert response.status_code == 302
    assert urlparse(response.headers["Location"]).path == "/journal"
    assert count_rows(JournalEntry) == 1
    entry = get_row(JournalEntry, 1)
    assert entry.student_id == data.student
    assert entry.curriculum_id == data.exam
    assert entry.grade == "5"
    assert entry.academic_year == "2025/2026"  # пробелы обрезаны


@pytest.mark.parametrize("grade", ["2", "3", "4", "5"])
def test_exam_accepts_numeric_grades(teacher_client, data, get_row, grade):
    teacher_client.post("/journal/new", data=entry_form(data.student, data.exam, grade=grade))
    assert get_row(JournalEntry, 1).grade == grade


@pytest.mark.parametrize("grade", ["зачет", "незачет"])
def test_credit_accepts_pass_fail_grades(teacher_client, data, get_row, grade):
    teacher_client.post("/journal/new", data=entry_form(data.student, data.credit, grade=grade))
    assert get_row(JournalEntry, 1).grade == grade


@pytest.mark.parametrize("grade", [
    "зачет",  # credit grade for exam
    "1",  # below range
    "6",  # above range
    "отлично",  # word instead of number
    "",  # empty
])
def test_exam_rejects_invalid_grades(teacher_client, data, count_rows, grade):
    response = teacher_client.post("/journal/new", data=entry_form(data.student, data.exam, grade=grade))
    assert response.status_code == 200
    assert INVALID_GRADE_TEXT in response.get_data(as_text=True)
    assert count_rows(JournalEntry) == 0


@pytest.mark.parametrize("grade", [
    "2",  # numeric two
    "5",  # numeric five
    "хорошо",  # word
    "",  # empty
])
def test_credit_rejects_invalid_grades(teacher_client, data, count_rows, grade):
    response = teacher_client.post("/journal/new", data=entry_form(data.student, data.credit, grade=grade))
    assert response.status_code == 200
    assert INVALID_GRADE_TEXT in response.get_data(as_text=True)
    assert count_rows(JournalEntry) == 0


def test_teacher_cannot_add_grade_for_foreign_discipline(teacher_client, data, count_rows):
    response = teacher_client.post("/journal/new", data=entry_form(data.student, data.foreign))
    assert response.status_code == 403
    assert count_rows(JournalEntry) == 0


def test_methodist_can_add_grade_for_any_discipline(methodist_client, data, count_rows):
    response = methodist_client.post("/journal/new", data=entry_form(data.student, data.foreign))
    assert response.status_code == 302
    assert count_rows(JournalEntry) == 1


def test_add_entry_for_unknown_discipline_returns_404(teacher_client, data):
    assert teacher_client.post("/journal/new", data=entry_form(data.student, 9999)).status_code == 404


def test_teacher_without_disciplines_is_redirected_with_warning(teacher_client):
    response = teacher_client.get("/journal/new", follow_redirects=True)
    assert response.request.path == "/journal"
    assert "Нет доступных дисциплин" in response.get_data(as_text=True)


def test_teacher_edits_grade_of_own_entry(teacher_client, data, add_entry, get_row):
    entry_id = add_entry(data.student, data.exam, grade="3")
    response = teacher_client.post(f"/journal/{entry_id}/edit",
                                   data=entry_form(data.student, data.exam, grade="4"))
    assert response.status_code == 302
    assert get_row(JournalEntry, entry_id).grade == "4"


def test_edit_form_opens_for_own_entry(teacher_client, data, add_entry):
    entry_id = add_entry(data.student, data.exam)
    assert teacher_client.get(f"/journal/{entry_id}/edit").status_code == 200


def test_teacher_cannot_open_or_edit_foreign_entry(teacher_client, data, add_entry, get_row):
    entry_id = add_entry(data.student, data.foreign, grade="3")
    assert teacher_client.get(f"/journal/{entry_id}/edit").status_code == 403
    response = teacher_client.post(f"/journal/{entry_id}/edit",
                                   data=entry_form(data.student, data.foreign, grade="5"))
    assert response.status_code == 403
    assert get_row(JournalEntry, entry_id).grade == "3"


def test_methodist_can_edit_any_entry(methodist_client, data, add_entry, get_row):
    entry_id = add_entry(data.student, data.foreign, grade="3")
    methodist_client.post(f"/journal/{entry_id}/edit",
                          data=entry_form(data.student, data.foreign, grade="5"))
    assert get_row(JournalEntry, entry_id).grade == "5"


def test_edit_unknown_entry_returns_404(methodist_client):
    assert methodist_client.get("/journal/999/edit").status_code == 404


def test_teacher_deletes_own_entry(teacher_client, data, add_entry, count_rows):
    entry_id = add_entry(data.student, data.exam)
    response = teacher_client.post(f"/journal/{entry_id}/delete")
    assert response.status_code == 302
    assert count_rows(JournalEntry) == 0


def test_teacher_cannot_delete_foreign_entry(teacher_client, data, add_entry, count_rows):
    entry_id = add_entry(data.student, data.foreign)
    assert teacher_client.post(f"/journal/{entry_id}/delete").status_code == 403
    assert count_rows(JournalEntry) == 1


def test_methodist_can_delete_any_entry(methodist_client, data, add_entry, count_rows):
    entry_id = add_entry(data.student, data.foreign)
    methodist_client.post(f"/journal/{entry_id}/delete")
    assert count_rows(JournalEntry) == 0


def test_delete_entry_requires_post(methodist_client, data, add_entry, count_rows):
    entry_id = add_entry(data.student, data.exam)
    assert methodist_client.get(f"/journal/{entry_id}/delete").status_code == 405
    assert count_rows(JournalEntry) == 1


def test_delete_unknown_entry_returns_404(methodist_client):
    assert methodist_client.post("/journal/999/delete").status_code == 404
