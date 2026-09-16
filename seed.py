# -*- coding: utf-8 -*-
"""Наполняет базу тестовыми данными: пользователей, студентов, учебный план и журнал.

Запуск:  python seed.py
"""
from app import create_app
from app.models import Curriculum, JournalEntry, ROLE_METHODIST, ROLE_TEACHER, Student, User, db

app = create_app()

with app.app_context():
    if not User.query.filter_by(username="admin").first():
        admin = User(username="admin", full_name="Смирнова Ольга Петровна", role=ROLE_METHODIST)
        admin.set_password("admin123")
        db.session.add(admin)

    teacher = User.query.filter_by(username="teacher").first()
    if not teacher:
        teacher = User(username="teacher", full_name="Кузнецов Пётр Сергеевич", role=ROLE_TEACHER)
        teacher.set_password("teacher123")
        db.session.add(teacher)
        db.session.flush()

    if Student.query.count() == 0:
        students = [
            Student(last_name="Минок", first_name="Алина", admission_year=2023, study_form="дневная", group_name="241-327"),
            Student(last_name="Конарев", first_name="Илья", admission_year=2023, study_form="дневная", group_name="241-327"),
            Student(last_name="Дубина", first_name="Анастасия", admission_year=2023, study_form="дневная", group_name="241-327"),
            Student(last_name="Егоров", first_name="Максим", admission_year=2022, study_form="заочная", group_name="241-330з"),
            Student(last_name="Сорокина", first_name="Дарья", admission_year=2024, study_form="вечерняя", group_name="241-335в"),
        ]
        db.session.add_all(students)

    if Curriculum.query.count() == 0:
        c1 = Curriculum(
            speciality="Программная инженерия",
            discipline="Автоматизация процессов жизненного цикла программных средств",
            semester=7,
            hours=72,
            report_form="зачет",
            teacher=teacher,
        )
        c2 = Curriculum(
            speciality="Программная инженерия",
            discipline="Базы данных",
            semester=5,
            hours=108,
            report_form="экзамен",
            teacher=teacher,
        )
        db.session.add_all([c1, c2])
        db.session.flush()

        first_student = Student.query.first()
        if first_student:
            db.session.add(
                JournalEntry(
                    academic_year="2025/2026",
                    student_id=first_student.id,
                    curriculum_id=c1.id,
                    grade="зачет",
                )
            )

    db.session.commit()
    print("Тестовые данные загружены.")
    print("Логины: admin/admin123 (сотрудник учебного отдела), teacher/teacher123 (преподаватель)")
