# -*- coding: utf-8 -*-
from datetime import date
from functools import wraps

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from .models import (
    CREDIT_GRADES,
    Curriculum,
    EXAM_GRADES,
    JournalEntry,
    REPORT_FORMS,
    ROLE_METHODIST,
    ROLE_TEACHER,
    STUDY_FORMS,
    Student,
    User,
    db,
)

main_bp = Blueprint("main", __name__)

MIN_ADMISSION_YEAR = 2000


def parse_int(raw_value, field_label, min_value=None, max_value=None):
    """Преобразует строку формы в int с понятным сообщением об ошибке.

    Не даёт некорректному вводу (нечисловое значение, значение вне
    допустимого диапазона) уронить обработчик запроса — см. п. 4.2.8 ТЗ.
    """
    try:
        value = int(raw_value)
    except (TypeError, ValueError):
        raise ValueError(f'Поле "{field_label}" должно быть целым числом.')
    if min_value is not None and value < min_value:
        raise ValueError(f'Поле "{field_label}" должно быть не меньше {min_value}.')
    if max_value is not None and value > max_value:
        raise ValueError(f'Поле "{field_label}" должно быть не больше {max_value}.')
    return value


def methodist_required(view):
    @wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        if not current_user.is_methodist:
            abort(403)
        return view(*args, **kwargs)

    return wrapped


# ---------------------------------------------------------------- dashboard
@main_bp.route("/")
@login_required
def dashboard():
    stats = {form: Student.query.filter_by(study_form=form).count() for form in STUDY_FORMS}
    totals = {
        "students": Student.query.count(),
        "curriculum": Curriculum.query.count(),
        "journal": JournalEntry.query.count(),
    }
    return render_template("dashboard.html", stats=stats, totals=totals)


# ---------------------------------------------------------------- students
@main_bp.route("/students")
@login_required
def students_list():
    students = Student.query.order_by(Student.last_name, Student.first_name).all()
    return render_template("students/list.html", students=students)


@main_bp.route("/students/new", methods=["GET", "POST"])
@methodist_required
def student_new():
    if request.method == "POST":
        try:
            admission_year = parse_int(
                request.form["admission_year"], "Год поступления",
                min_value=MIN_ADMISSION_YEAR, max_value=date.today().year,
            )
        except ValueError as exc:
            flash(str(exc), "danger")
            return render_template("students/form.html", student=None, study_forms=STUDY_FORMS)
        student = Student(
            last_name=request.form["last_name"].strip(),
            first_name=request.form["first_name"].strip(),
            patronymic=request.form.get("patronymic", "").strip(),
            admission_year=admission_year,
            study_form=request.form["study_form"],
            group_name=request.form["group_name"].strip(),
        )
        db.session.add(student)
        db.session.commit()
        flash("Студент добавлен", "success")
        return redirect(url_for("main.students_list"))
    return render_template("students/form.html", student=None, study_forms=STUDY_FORMS)


@main_bp.route("/students/<int:student_id>/edit", methods=["GET", "POST"])
@methodist_required
def student_edit(student_id):
    student = Student.query.get_or_404(student_id)
    if request.method == "POST":
        try:
            admission_year = parse_int(
                request.form["admission_year"], "Год поступления",
                min_value=MIN_ADMISSION_YEAR, max_value=date.today().year,
            )
        except ValueError as exc:
            flash(str(exc), "danger")
            return render_template("students/form.html", student=student, study_forms=STUDY_FORMS)
        student.last_name = request.form["last_name"].strip()
        student.first_name = request.form["first_name"].strip()
        student.patronymic = request.form.get("patronymic", "").strip()
        student.admission_year = admission_year
        student.study_form = request.form["study_form"]
        student.group_name = request.form["group_name"].strip()
        db.session.commit()
        flash("Данные студента обновлены", "success")
        return redirect(url_for("main.students_list"))
    return render_template("students/form.html", student=student, study_forms=STUDY_FORMS)


@main_bp.route("/students/<int:student_id>/delete", methods=["POST"])
@methodist_required
def student_delete(student_id):
    student = Student.query.get_or_404(student_id)
    db.session.delete(student)
    db.session.commit()
    flash("Студент удалён", "success")
    return redirect(url_for("main.students_list"))


# ------------------------------------------------------------- curriculum
@main_bp.route("/curriculum")
@login_required
def curriculum_list():
    items = Curriculum.query.order_by(Curriculum.speciality, Curriculum.semester).all()
    return render_template("curriculum/list.html", items=items)


@main_bp.route("/curriculum/new", methods=["GET", "POST"])
@methodist_required
def curriculum_new():
    teachers = User.query.filter_by(role=ROLE_TEACHER).order_by(User.full_name).all()
    if request.method == "POST":
        try:
            semester = parse_int(request.form["semester"], "Семестр", min_value=1, max_value=12)
            hours = parse_int(request.form["hours"], "Количество часов", min_value=1)
            teacher_id_raw = request.form.get("teacher_id") or None
            teacher_id = parse_int(teacher_id_raw, "Преподаватель") if teacher_id_raw else None
        except ValueError as exc:
            flash(str(exc), "danger")
            return render_template(
                "curriculum/form.html", item=None, report_forms=REPORT_FORMS, teachers=teachers
            )
        item = Curriculum(
            speciality=request.form["speciality"].strip(),
            discipline=request.form["discipline"].strip(),
            semester=semester,
            hours=hours,
            report_form=request.form["report_form"],
            teacher_id=teacher_id,
        )
        db.session.add(item)
        db.session.commit()
        flash("Запись учебного плана добавлена", "success")
        return redirect(url_for("main.curriculum_list"))
    return render_template(
        "curriculum/form.html", item=None, report_forms=REPORT_FORMS, teachers=teachers
    )


@main_bp.route("/curriculum/<int:item_id>/edit", methods=["GET", "POST"])
@methodist_required
def curriculum_edit(item_id):
    item = Curriculum.query.get_or_404(item_id)
    teachers = User.query.filter_by(role=ROLE_TEACHER).order_by(User.full_name).all()
    if request.method == "POST":
        try:
            semester = parse_int(request.form["semester"], "Семестр", min_value=1, max_value=12)
            hours = parse_int(request.form["hours"], "Количество часов", min_value=1)
            teacher_id_raw = request.form.get("teacher_id") or None
            teacher_id = parse_int(teacher_id_raw, "Преподаватель") if teacher_id_raw else None
        except ValueError as exc:
            flash(str(exc), "danger")
            return render_template(
                "curriculum/form.html", item=item, report_forms=REPORT_FORMS, teachers=teachers
            )
        item.speciality = request.form["speciality"].strip()
        item.discipline = request.form["discipline"].strip()
        item.semester = semester
        item.hours = hours
        item.report_form = request.form["report_form"]
        item.teacher_id = teacher_id
        db.session.commit()
        flash("Запись учебного плана обновлена", "success")
        return redirect(url_for("main.curriculum_list"))
    return render_template(
        "curriculum/form.html", item=item, report_forms=REPORT_FORMS, teachers=teachers
    )


@main_bp.route("/curriculum/<int:item_id>/delete", methods=["POST"])
@methodist_required
def curriculum_delete(item_id):
    item = Curriculum.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    flash("Запись учебного плана удалена", "success")
    return redirect(url_for("main.curriculum_list"))


# ----------------------------------------------------------------- journal
def _journal_query():
    query = JournalEntry.query.join(Curriculum)
    if not current_user.is_methodist:
        query = query.filter(Curriculum.teacher_id == current_user.id)
    return query


@main_bp.route("/journal")
@login_required
def journal_list():
    entries = _journal_query().order_by(JournalEntry.academic_year.desc()).all()
    return render_template("journal/list.html", entries=entries)


@main_bp.route("/journal/new", methods=["GET", "POST"])
@login_required
def journal_new():
    if current_user.is_methodist:
        curricula = Curriculum.query.all()
    else:
        curricula = Curriculum.query.filter_by(teacher_id=current_user.id).all()
    students = Student.query.order_by(Student.last_name).all()

    if not curricula:
        flash("Нет доступных дисциплин учебного плана для внесения оценок", "warning")
        return redirect(url_for("main.journal_list"))

    if request.method == "POST":
        try:
            curriculum_id = parse_int(request.form["curriculum_id"], "Дисциплина")
            student_id = parse_int(request.form["student_id"], "Студент")
        except ValueError as exc:
            flash(str(exc), "danger")
            return render_template(
                "journal/form.html", entry=None, curricula=curricula, students=students
            )
        curriculum = Curriculum.query.get_or_404(curriculum_id)
        if not current_user.is_methodist and curriculum.teacher_id != current_user.id:
            abort(403)
        grade = request.form["grade"]
        if grade not in curriculum.allowed_grades:
            flash("Недопустимое значение оценки для выбранной формы отчётности", "danger")
            return render_template(
                "journal/form.html", entry=None, curricula=curricula, students=students
            )
        entry = JournalEntry(
            academic_year=request.form["academic_year"].strip(),
            student_id=student_id,
            curriculum_id=curriculum.id,
            grade=grade,
        )
        db.session.add(entry)
        db.session.commit()
        flash("Запись в журнал успеваемости добавлена", "success")
        return redirect(url_for("main.journal_list"))

    return render_template(
        "journal/form.html", entry=None, curricula=curricula, students=students
    )


@main_bp.route("/journal/<int:entry_id>/edit", methods=["GET", "POST"])
@login_required
def journal_edit(entry_id):
    entry = JournalEntry.query.get_or_404(entry_id)
    if not current_user.is_methodist and entry.curriculum.teacher_id != current_user.id:
        abort(403)

    if current_user.is_methodist:
        curricula = Curriculum.query.all()
    else:
        curricula = Curriculum.query.filter_by(teacher_id=current_user.id).all()
    students = Student.query.order_by(Student.last_name).all()

    if request.method == "POST":
        try:
            curriculum_id = parse_int(request.form["curriculum_id"], "Дисциплина")
            student_id = parse_int(request.form["student_id"], "Студент")
        except ValueError as exc:
            flash(str(exc), "danger")
            return render_template(
                "journal/form.html", entry=entry, curricula=curricula, students=students
            )
        curriculum = Curriculum.query.get_or_404(curriculum_id)
        if not current_user.is_methodist and curriculum.teacher_id != current_user.id:
            abort(403)
        grade = request.form["grade"]
        if grade not in curriculum.allowed_grades:
            flash("Недопустимое значение оценки для выбранной формы отчётности", "danger")
            return render_template(
                "journal/form.html", entry=entry, curricula=curricula, students=students
            )
        entry.academic_year = request.form["academic_year"].strip()
        entry.student_id = student_id
        entry.curriculum_id = curriculum.id
        entry.grade = grade
        db.session.commit()
        flash("Запись журнала обновлена", "success")
        return redirect(url_for("main.journal_list"))

    return render_template(
        "journal/form.html", entry=entry, curricula=curricula, students=students
    )


@main_bp.route("/journal/<int:entry_id>/delete", methods=["POST"])
@login_required
def journal_delete(entry_id):
    entry = JournalEntry.query.get_or_404(entry_id)
    if not current_user.is_methodist and entry.curriculum.teacher_id != current_user.id:
        abort(403)
    db.session.delete(entry)
    db.session.commit()
    flash("Запись журнала удалена", "success")
    return redirect(url_for("main.journal_list"))


# ----------------------------------------------------------------- reports
@main_bp.route("/reports/by-form", methods=["GET", "POST"])
@login_required
def report_by_form():
    count = None
    selected = None
    if request.method == "POST":
        selected = request.form["study_form"]
        count = Student.query.filter_by(study_form=selected).count()
    return render_template(
        "reports/by_form.html", study_forms=STUDY_FORMS, count=count, selected=selected
    )


@main_bp.route("/reports/by-discipline", methods=["GET", "POST"])
@login_required
def report_by_discipline():
    rows = None
    discipline = None
    disciplines = sorted({c.discipline for c in Curriculum.query.all()})
    if request.method == "POST":
        discipline = request.form["discipline"].strip()
        rows = (
            Curriculum.query.filter(Curriculum.discipline == discipline)
            .order_by(Curriculum.semester)
            .all()
        )
    return render_template(
        "reports/by_discipline.html",
        rows=rows,
        discipline=discipline,
        disciplines=disciplines,
    )
