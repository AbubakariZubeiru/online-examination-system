from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from app import db
from app.models.models import User, Exam, Submission
from app.utils import role_required

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/dashboard")
@login_required
@role_required("admin")
def dashboard():
    users = User.query.order_by(User.created_at.desc()).all()
    exams = Exam.query.order_by(Exam.created_at.desc()).all()
    stats = {
        "total_users": len(users),
        "total_teachers": len([u for u in users if u.is_teacher()]),
        "total_students": len([u for u in users if u.is_student()]),
        "total_exams": len(exams),
        "total_submissions": Submission.query.count(),
    }
    return render_template("admin/dashboard.html", users=users, exams=exams, stats=stats)


@admin_bp.route("/users/<int:user_id>/toggle", methods=["POST"])
@login_required
@role_required("admin")
def toggle_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("You cannot disable your own account.", "warning")
        return redirect(url_for("admin.dashboard"))

    user.is_active_account = not user.is_active_account
    db.session.commit()
    state = "enabled" if user.is_active_account else "disabled"
    flash(f"User '{user.username}' has been {state}.", "success")
    return redirect(url_for("admin.dashboard"))


@admin_bp.route("/users/<int:user_id>/delete", methods=["POST"])
@login_required
@role_required("admin")
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("You cannot delete your own account.", "warning")
        return redirect(url_for("admin.dashboard"))

    db.session.delete(user)
    db.session.commit()
    flash(f"User '{user.username}' has been deleted.", "success")
    return redirect(url_for("admin.dashboard"))


@admin_bp.route("/exams/<int:exam_id>/delete", methods=["POST"])
@login_required
@role_required("admin")
def delete_exam(exam_id):
    exam = Exam.query.get_or_404(exam_id)
    db.session.delete(exam)
    db.session.commit()
    flash(f"Exam '{exam.title}' has been deleted.", "success")
    return redirect(url_for("admin.dashboard"))
