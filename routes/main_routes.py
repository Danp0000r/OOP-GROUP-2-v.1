from flask import Blueprint, render_template, redirect, url_for, session, request, flash
from database.db import db
from models.build import Build
from models.user import User

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    return render_template("index.html")


@main_bp.route("/profile")
def profile():
    if not session.get("user_id"):
        return redirect(url_for("auth.login"))
    user = User.query.get(session["user_id"])
    if not user:
        session.pop("user_id", None)
        session.pop("username", None)
        session.pop("is_admin", None)
        flash("Your session is no longer valid. Please log in again.", "warning")
        return redirect(url_for("auth.login"))
    builds = Build.query.filter_by(user_id=session["user_id"]).order_by(Build.created_at.desc()).all()
    return render_template("profile.html", builds=builds)


@main_bp.route("/profile/update", methods=["POST"])
def update_profile():
    if not session.get("user_id"):
        return redirect(url_for("auth.login"))
    user = User.query.get(session["user_id"])
    if not user:
        return redirect(url_for("auth.login"))

    new_username = request.form.get("username", "").strip()
    new_email    = request.form.get("email", "").strip()
    new_password = request.form.get("password", "")

    if new_username:
        user.username = new_username
        session["username"] = new_username
    if new_email:
        user.email = new_email
        session["email"] = new_email
    if new_password:
        user.set_password(new_password)

    db.session.commit()
    flash("Profile updated successfully.", "success")
    return redirect(url_for("main.profile"))
