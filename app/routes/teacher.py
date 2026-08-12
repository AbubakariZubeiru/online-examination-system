from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user

from app import db
from app.models.models import Exam, Question, Choice, Submission
from app.utils import role_required

teacher_bp = Blueprint("teacher", __name__, url_prefix="/teacher")


def _get_owned_exam_or_404(exam_id):
    exam = Exam.query.get_or_404(exam_id)
    if exam.teacher_id != current_user.id:
        abort(403)
    return exam


@teacher_bp.route("/dashboard")
@login_required
@role_required("teacher")
def dashboard():
    exams = Exam.query.filter_by(teacher_id=current_user.id).order_by(
        Exam.created_at.desc()
    ).all()
    return render_template("teacher/dashboard.html", exams=exams)


@teacher_bp.route("/exams/create", methods=["GET", "POST"])
@login_required
@role_required("teacher")
def create_exam():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        duration = request.form.get("duration_minutes", "30")

        if not title:
            flash("Exam title is required.", "danger")
            return render_template("teacher/create_exam.html", form_data=request.form)

        try:
            duration = int(duration)
            if duration <= 0:
                raise ValueError
        except ValueError:
            flash("Duration must be a positive number of minutes.", "danger")
            return render_template("teacher/create_exam.html", form_data=request.form)

        exam = Exam(
            title=title,
            description=description,
            duration_minutes=duration,
            teacher_id=current_user.id,
        )
        db.session.add(exam)
        db.session.commit()
        flash("Exam created. Now add some questions to it.", "success")
        return redirect(url_for("teacher.manage_questions", exam_id=exam.id))

    return render_template("teacher/create_exam.html", form_data={})


@teacher_bp.route("/exams/<int:exam_id>/questions", methods=["GET", "POST"])
@login_required
@role_required("teacher")
def manage_questions(exam_id):
    exam = _get_owned_exam_or_404(exam_id)

    if request.method == "POST":
        question_text = request.form.get("question_text", "").strip()
        marks = request.form.get("marks", "1")
        choice_texts = request.form.getlist("choice_text")
        correct_index = request.form.get("correct_choice")

        errors = []
        if not question_text:
            errors.append("Question text is required.")

        choice_texts = [c.strip() for c in choice_texts if c.strip()]
        if len(choice_texts) < 2:
            errors.append("Provide at least 2 answer choices.")
        if correct_index is None or not correct_index.isdigit():
            errors.append("Select which choice is correct.")
        elif int(correct_index) >= len(choice_texts):
            errors.append("Correct choice selection is invalid.")

        try:
            marks = int(marks)
            if marks <= 0:
                raise ValueError
        except ValueError:
            errors.append("Marks must be a positive integer.")
            marks = 1

        if errors:
            for e in errors:
                flash(e, "danger")
            return redirect(url_for("teacher.manage_questions", exam_id=exam.id))

        question = Question(exam_id=exam.id, question_text=question_text, marks=marks)
        db.session.add(question)
        db.session.flush()

        for i, text in enumerate(choice_texts):
            choice = Choice(
                question_id=question.id,
                choice_text=text,
                is_correct=(i == int(correct_index)),
            )
            db.session.add(choice)

        db.session.commit()
        flash("Question added.", "success")
        return redirect(url_for("teacher.manage_questions", exam_id=exam.id))

    return render_template("teacher/manage_questions.html", exam=exam)


@teacher_bp.route("/exams/<int:exam_id>/questions/<int:question_id>/delete", methods=["POST"])
@login_required
@role_required("teacher")
def delete_question(exam_id, question_id):
    exam = _get_owned_exam_or_404(exam_id)
    question = Question.query.filter_by(id=question_id, exam_id=exam.id).first_or_404()
    db.session.delete(question)
    db.session.commit()
    flash("Question deleted.", "success")
    return redirect(url_for("teacher.manage_questions", exam_id=exam.id))


@teacher_bp.route("/exams/<int:exam_id>/publish", methods=["POST"])
@login_required
@role_required("teacher")
def publish_exam(exam_id):
    exam = _get_owned_exam_or_404(exam_id)
    if not exam.questions:
        flash("Add at least one question before publishing.", "warning")
        return redirect(url_for("teacher.manage_questions", exam_id=exam.id))

    exam.is_published = not exam.is_published
    db.session.commit()
    state = "published" if exam.is_published else "unpublished"
    flash(f"Exam '{exam.title}' has been {state}.", "success")
    return redirect(url_for("teacher.dashboard"))


@teacher_bp.route("/exams/<int:exam_id>/delete", methods=["POST"])
@login_required
@role_required("teacher")
def delete_exam(exam_id):
    exam = _get_owned_exam_or_404(exam_id)
    db.session.delete(exam)
    db.session.commit()
    flash(f"Exam '{exam.title}' deleted.", "success")
    return redirect(url_for("teacher.dashboard"))


@teacher_bp.route("/exams/<int:exam_id>/results")
@login_required
@role_required("teacher")
def exam_results(exam_id):
    exam = _get_owned_exam_or_404(exam_id)
    submissions = Submission.query.filter_by(exam_id=exam.id).order_by(
        Submission.submitted_at.desc()
    ).all()
    return render_template("teacher/exam_results.html", exam=exam, submissions=submissions)
