"""
Core assessment logic: grading a student's exam submission.
Kept separate from routes so the grading rules can be tested/extended
independently of the web layer (e.g. adding partial credit, essay
questions with manual grading, etc.)
"""

from app import db
from app.models.models import Submission, Answer


def grade_submission(exam, student, answers_dict):
    """
    Grade and persist a submission.

    :param exam: Exam instance being taken
    :param student: User instance (the student submitting)
    :param answers_dict: dict of {question_id (int): choice_id (int or None)}
    :return: the created Submission instance
    """
    total_marks = exam.total_marks()
    score = 0

    submission = Submission(
        exam_id=exam.id,
        student_id=student.id,
        total_marks=total_marks,
    )
    db.session.add(submission)
    db.session.flush()  # get submission.id before committing

    for question in exam.questions:
        selected_choice_id = answers_dict.get(question.id)
        answer = Answer(
            submission_id=submission.id,
            question_id=question.id,
            choice_id=selected_choice_id,
        )
        db.session.add(answer)

        correct = question.correct_choice()
        if correct and selected_choice_id and int(selected_choice_id) == correct.id:
            score += question.marks

    submission.score = score
    db.session.commit()
    return submission
