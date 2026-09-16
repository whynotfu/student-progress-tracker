# -*- coding: utf-8 -*-
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

STUDY_FORMS = ["дневная", "вечерняя", "заочная"]
REPORT_FORMS = ["экзамен", "зачет"]
EXAM_GRADES = ["2", "3", "4", "5"]
CREDIT_GRADES = ["зачет", "незачет"]

ROLE_METHODIST = "methodist"
ROLE_TEACHER = "teacher"
ROLE_LABELS = {ROLE_METHODIST: "Сотрудник учебного отдела", ROLE_TEACHER: "Преподаватель"}


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(20), nullable=False, default=ROLE_TEACHER)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_methodist(self):
        return self.role == ROLE_METHODIST

    @property
    def role_label(self):
        return ROLE_LABELS.get(self.role, self.role)


class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    last_name = db.Column(db.String(100), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    patronymic = db.Column(db.String(100))
    admission_year = db.Column(db.Integer, nullable=False)
    study_form = db.Column(db.String(20), nullable=False)
    group_name = db.Column(db.String(50), nullable=False)

    journal_entries = db.relationship(
        "JournalEntry", backref="student", cascade="all, delete-orphan"
    )

    @property
    def full_name(self):
        parts = [self.last_name, self.first_name, self.patronymic or ""]
        return " ".join(part for part in parts if part)


class Curriculum(db.Model):
    """Запись учебного плана: специальность, дисциплина, семестр, часы, форма отчётности."""

    id = db.Column(db.Integer, primary_key=True)
    speciality = db.Column(db.String(200), nullable=False)
    discipline = db.Column(db.String(150), nullable=False)
    semester = db.Column(db.Integer, nullable=False)
    hours = db.Column(db.Integer, nullable=False)
    report_form = db.Column(db.String(20), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey("user.id"))

    teacher = db.relationship("User")
    journal_entries = db.relationship(
        "JournalEntry", backref="curriculum", cascade="all, delete-orphan"
    )

    @property
    def allowed_grades(self):
        return EXAM_GRADES if self.report_form == "экзамен" else CREDIT_GRADES


class JournalEntry(db.Model):
    """Запись журнала успеваемости: год/семестр (через учебный план), студент, дисциплина, оценка."""

    id = db.Column(db.Integer, primary_key=True)
    academic_year = db.Column(db.String(20), nullable=False)  # например "2025/2026"
    student_id = db.Column(db.Integer, db.ForeignKey("student.id"), nullable=False)
    curriculum_id = db.Column(db.Integer, db.ForeignKey("curriculum.id"), nullable=False)
    grade = db.Column(db.String(20), nullable=False)
