from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user

from app import db
from app.models.models import Exam, Submission
from app.services.assessment import grade_submission
from app.utils import role_required

student_bp = Blueprint("student", __name__, url_prefix="/student")


@student_bp.route("/dashboard")
@login_required
@role_required("student")
def dashboard():
    taken_exam_ids = {
        s.exam_id for s in Submission.query.filter_by(student_id=current_user.id).all()
    }
    available_exams = Exam.query.filter_by(is_published=True).order_by(
        Exam.created_at.desc()
    ).all()

    return render_template(
        "student/dashboard.html",
        available_exams=available_exams,
        taken_exam_ids=taken_exam_ids,
    )


@student_bp.route("/exams/<int:exam_id>/take", methods=["GET", "POST"])
@login_required
@role_required("student")
def take_exam(exam_id):
    exam = Exam.query.get_or_404(exam_id)

    if not exam.is_published:
        abort(404)

    existing = Submission.query.filter_by(
        exam_id=exam.id, student_id=current_user.id
    ).first()
    if existing:
        flash("You have already submitted this exam.", "info")
        return redirect(url_for("student.view_result", submission_id=existing.id))

    if request.method == "POST":
        answers_dict = {}
        for question in exam.questions:
            choice_id = request.form.get(f"question_{question.id}")
            answers_dict[question.id] = int(choice_id) if choice_id else None

        submission = grade_submission(exam, current_user, answers_dict)
        flash("Exam submitted successfully!", "success")
        return redirect(url_for("student.view_result", submission_id=submission.id))

    return render_template("student/take_exam.html", exam=exam)


@student_bp.route("/results/<int:submission_id>")
@login_required
@role_required("student")
def view_result(submission_id):
    submission = Submission.query.get_or_404(submission_id)
    if submission.student_id != current_user.id:
        abort(403)

    return render_template("student/view_result.html", submission=submission)


@student_bp.route("/history")
@login_required
@role_required("student")
def history():
    submissions = Submission.query.filter_by(student_id=current_user.id).order_by(
        Submission.submitted_at.desc()
    ).all()
    return render_template("student/history.html", submissions=submissions)
