import uuid
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app import db, login_manager

exam_students = db.Table(
    "exam_students",
    db.Column("exam_id", db.Integer, db.ForeignKey("exams.id", ondelete="CASCADE"), primary_key=True),
    db.Column("user_id", db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
)

class_students = db.Table(
    "class_students",
    db.Column("class_id", db.Integer, db.ForeignKey("classes.id", ondelete="CASCADE"), primary_key=True),
    db.Column("user_id", db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
)

exam_classes = db.Table(
    "exam_classes",
    db.Column("exam_id", db.Integer, db.ForeignKey("exams.id", ondelete="CASCADE"), primary_key=True),
    db.Column("class_id", db.Integer, db.ForeignKey("classes.id", ondelete="CASCADE"), primary_key=True),
)


class Class(db.Model):
    __tablename__ = "classes"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    teacher_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    teacher = db.relationship("User", foreign_keys=[teacher_id], backref="classes_taught")
    students = db.relationship("User", secondary=class_students, backref="enrolled_classes")

    def __repr__(self):
        return f"<Class {self.name}>"


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="student")  # admin/teacher/student
    is_active_account = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    exams_created = db.relationship("Exam", backref="teacher", lazy=True,
                                     foreign_keys="Exam.teacher_id")
    submissions = db.relationship("Submission", backref="student", lazy=True,
                                   foreign_keys="Submission.student_id")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_active(self):
        # Overrides UserMixin.is_active to respect admin-disabled accounts
        return self.is_active_account

    def is_admin(self):
        return self.role == "admin"

    def is_teacher(self):
        return self.role == "teacher"

    def is_student(self):
        return self.role == "student"

    def __repr__(self):
        return f"<User {self.username} ({self.role})>"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class Exam(db.Model):
    __tablename__ = "exams"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    duration_minutes = db.Column(db.Integer, nullable=False, default=30)
    teacher_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    is_published = db.Column(db.Boolean, default=False)
    start_time = db.Column(db.DateTime, nullable=True)
    end_time = db.Column(db.DateTime, nullable=True)
    max_attempts = db.Column(db.Integer, nullable=False, default=1)
    access_token = db.Column(db.String(64), unique=True, index=True, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    assigned_students = db.relationship("User", secondary=exam_students, backref="assigned_exams")
    assigned_classes = db.relationship("Class", secondary=exam_classes, backref="assigned_exams")
    questions = db.relationship("Question", backref="exam", lazy=True,
                                 cascade="all, delete-orphan")
    submissions = db.relationship("Submission", backref="exam", lazy=True,
                                   cascade="all, delete-orphan")

    def total_marks(self):
        return sum(q.marks for q in self.questions)

    def generate_token(self):
        if not self.access_token:
            self.access_token = uuid.uuid4().hex
        return self.access_token

    def is_student_assigned(self, user):
        if not self.assigned_students and not self.assigned_classes:
            return True
        if user in self.assigned_students:
            return True
        for c in self.assigned_classes:
            if user in c.students:
                return True
        return False

    def is_available_now(self):
        now = datetime.utcnow()
        if self.start_time and now < self.start_time:
            return False
        if self.end_time and now > self.end_time:
            return False
        return True

    def __repr__(self):
        return f"<Exam {self.title}>"


class Question(db.Model):
    __tablename__ = "questions"

    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey("exams.id"), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    marks = db.Column(db.Integer, nullable=False, default=1)

    choices = db.relationship("Choice", backref="question", lazy=True,
                               cascade="all, delete-orphan")
    answers = db.relationship("Answer", backref="question", lazy=True,
                               cascade="all, delete-orphan")

    def correct_choice(self):
        for c in self.choices:
            if c.is_correct:
                return c
        return None


class Choice(db.Model):
    __tablename__ = "choices"

    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey("questions.id"), nullable=False)
    choice_text = db.Column(db.String(255), nullable=False)
    is_correct = db.Column(db.Boolean, default=False)


class Submission(db.Model):
    __tablename__ = "submissions"

    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey("exams.id"), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    score = db.Column(db.Float, default=0)
    total_marks = db.Column(db.Float, default=0)
    attempt_number = db.Column(db.Integer, default=1)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)

    answers = db.relationship("Answer", backref="submission", lazy=True,
                               cascade="all, delete-orphan")

    def percentage(self):
        if self.total_marks == 0:
            return 0
        return round((self.score / self.total_marks) * 100, 2)


class Answer(db.Model):
    __tablename__ = "answers"

    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(db.Integer, db.ForeignKey("submissions.id"), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey("questions.id"), nullable=False)
    choice_id = db.Column(db.Integer, db.ForeignKey("choices.id"), nullable=True)

    selected_choice = db.relationship("Choice", foreign_keys=[choice_id])

