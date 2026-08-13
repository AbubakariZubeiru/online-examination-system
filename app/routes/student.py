from datetime import datetime
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
    all_published = Exam.query.filter_by(is_published=True).order_by(
        Exam.created_at.desc()
    ).all()

    # Filter exams assigned to current_user (or open to all)
    available_exams = [e for e in all_published if e.is_student_assigned(current_user)]

    # Calculate attempts taken per exam for this student
    all_submissions = Submission.query.filter_by(student_id=current_user.id).all()
    exam_attempt_counts = {}
    for sub in all_submissions:
        exam_attempt_counts[sub.exam_id] = exam_attempt_counts.get(sub.exam_id, 0) + 1

    return render_template(
        "student/dashboard.html",
        available_exams=available_exams,
        exam_attempt_counts=exam_attempt_counts,
    )


@student_bp.route("/exams/link/<token>")
def exam_link(token):
    exam = Exam.query.filter_by(access_token=token).first_or_404()
    if not current_user.is_authenticated:
        flash("Please log in as a student to take this exam.", "info")
        return redirect(url_for("auth.login", next=request.url))

    if current_user.is_teacher() or current_user.is_admin():
        flash(f"Logged in as {current_user.role}. Share this link with students to take '{exam.title}'.", "info")
        if current_user.is_teacher() and exam.teacher_id == current_user.id:
            return redirect(url_for("teacher.publish_settings", exam_id=exam.id))
        return redirect(url_for("index"))

    return redirect(url_for("student.take_exam", exam_id=exam.id))


@student_bp.route("/exams/<int:exam_id>/take", methods=["GET", "POST"])
@login_required
@role_required("student")
def take_exam(exam_id):
    exam = Exam.query.get_or_404(exam_id)

    if not exam.is_published:
        abort(404)

    if not exam.is_student_assigned(current_user):
        flash("You are not assigned to take this exam.", "danger")
        return redirect(url_for("student.dashboard"))

    now = datetime.utcnow()
    if exam.start_time and now < exam.start_time:
        flash(f"This exam is scheduled to open on {exam.start_time.strftime('%Y-%m-%d %H:%M UTC')}.", "warning")
        return redirect(url_for("student.dashboard"))

    if exam.end_time and now > exam.end_time:
        flash(f"This exam closed on {exam.end_time.strftime('%Y-%m-%d %H:%M UTC')}.", "danger")
        return redirect(url_for("student.dashboard"))

    existing_submissions = Submission.query.filter_by(
        exam_id=exam.id, student_id=current_user.id
    ).order_by(Submission.submitted_at.desc()).all()

    attempts_taken = len(existing_submissions)
    if attempts_taken >= exam.max_attempts:
        flash(f"You have reached the maximum allowed attempt limit ({exam.max_attempts}) for this exam.", "info")
        return redirect(url_for("student.view_result", submission_id=existing_submissions[0].id))

    attempt_number = attempts_taken + 1

    if request.method == "POST":
        answers_dict = {}
        for question in exam.questions:
            choice_id = request.form.get(f"question_{question.id}")
            answers_dict[question.id] = int(choice_id) if choice_id else None

        submission = grade_submission(exam, current_user, answers_dict, attempt_number=attempt_number)
        flash(f"Exam submitted successfully! (Attempt {attempt_number} of {exam.max_attempts})", "success")
        return redirect(url_for("student.view_result", submission_id=submission.id))

    return render_template(
        "student/take_exam.html",
        exam=exam,
        attempt_number=attempt_number,
        max_attempts=exam.max_attempts,
    )


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

