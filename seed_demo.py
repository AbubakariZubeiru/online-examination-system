"""
Seed the database with demo accounts and a sample published exam, so you can
immediately test the Teacher and Student interfaces without registering
accounts by hand.

Usage:
    python seed_demo.py

Creates (if they don't already exist):
    - Teacher   username: teacher_demo   password: Teacher@123
    - Student   username: student_demo   password: Student@123
    - A published exam "General Knowledge Quiz" with 3 questions,
      owned by teacher_demo.

Safe to re-run: it skips creation of anything that already exists.
"""

from app import create_app, db
from app.models.models import User, Exam, Question, Choice

app = create_app()


def get_or_create_user(username, email, password, role):
    user = User.query.filter_by(username=username).first()
    if user:
        print(f"[skip] User '{username}' already exists.")
        return user
    user = User(username=username, email=email, role=role)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    print(f"[created] {role} account -> username: {username} / password: {password}")
    return user


def seed_exam(teacher):
    existing = Exam.query.filter_by(title="General Knowledge Quiz", teacher_id=teacher.id).first()
    if existing:
        print("[skip] Demo exam already exists.")
        return existing

    exam = Exam(
        title="General Knowledge Quiz",
        description="A short demo quiz to test the exam-taking flow.",
        duration_minutes=5,
        teacher_id=teacher.id,
        is_published=True,
    )
    exam.generate_token()
    db.session.add(exam)
    db.session.flush()

    questions_data = [
        {
            "text": "What is the capital of France?",
            "marks": 2,
            "choices": ["Berlin", "Paris", "Madrid", "Rome"],
            "correct": 1,
        },
        {
            "text": "What is 7 x 6?",
            "marks": 2,
            "choices": ["36", "42", "48", "40"],
            "correct": 1,
        },
        {
            "text": "Which planet is known as the Red Planet?",
            "marks": 1,
            "choices": ["Venus", "Jupiter", "Mars", "Saturn"],
            "correct": 2,
        },
    ]

    for q_data in questions_data:
        question = Question(exam_id=exam.id, question_text=q_data["text"], marks=q_data["marks"])
        db.session.add(question)
        db.session.flush()
        for i, choice_text in enumerate(q_data["choices"]):
            db.session.add(Choice(
                question_id=question.id,
                choice_text=choice_text,
                is_correct=(i == q_data["correct"]),
            ))

    db.session.commit()
    print(f"[created] Exam '{exam.title}' with {len(questions_data)} questions (published).")
    return exam


if __name__ == "__main__":
    with app.app_context():
        teacher = get_or_create_user("teacher_demo", "teacher_demo@example.com", "Teacher@123", "teacher")
        get_or_create_user("student_demo", "student_demo@example.com", "Student@123", "student")
        seed_exam(teacher)

        print("\nDone. Log in at /auth/login with either:")
        print("  teacher_demo / Teacher@123  (manage the demo exam)")
        print("  student_demo / Student@123  (take the demo exam)")
