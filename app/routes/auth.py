from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user

from app import db
from app.models.models import User

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


def _redirect_for_role(user):
    if user.is_admin():
        return redirect(url_for("admin.dashboard"))
    if user.is_teacher():
        return redirect(url_for("teacher.dashboard"))
    return redirect(url_for("student.dashboard"))


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return _redirect_for_role(current_user)

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        role = request.form.get("role", "student")

        if role not in ("student", "teacher"):
            role = "student"  # admins cannot self-register

        errors = []
        if not username or not email or not password:
            errors.append("All fields are required.")
        if password != confirm_password:
            errors.append("Passwords do not match.")
        if len(password) < 6:
            errors.append("Password must be at least 6 characters.")
        if User.query.filter_by(username=username).first():
            errors.append("Username already taken.")
        if User.query.filter_by(email=email).first():
            errors.append("Email already registered.")

        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template("auth/register.html", form_data=request.form)

        user = User(username=username, email=email, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash("Registration successful. Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html", form_data={})


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return _redirect_for_role(current_user)

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = User.query.filter_by(username=username).first()

        if user is None or not user.check_password(password):
            flash("Invalid username or password.", "danger")
            return render_template("auth/login.html")

        if not user.is_active_account:
            flash("This account has been disabled. Contact an administrator.", "danger")
            return render_template("auth/login.html")

        login_user(user)
        flash(f"Welcome back, {user.username}!", "success")
        return _redirect_for_role(user)

    return render_template("auth/login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))
