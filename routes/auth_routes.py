from flask import Blueprint, render_template, redirect, url_for, flash, request, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from database.db import db
from models.user import User
from models.activity import Activity
from models.build import Build
from services.activity_service import ActivityService
import datetime

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email    = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            session["user_id"]  = user.id
            session["username"] = user.username
            session["email"]    = user.email
            session["is_admin"] = user.is_admin
            # Mark user as active and update last_active timestamp
            user.is_active = True
            user.last_active = datetime.datetime.utcnow()
            db.session.commit()
            flash("Welcome back, " + user.username + "!", "success")
            return redirect(url_for("main.index"))
        flash("Invalid email or password.", "danger")
    return render_template("auth/login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email    = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        if User.query.filter_by(email=email).first():
            flash("Email already registered.", "danger")
            return render_template("auth/register.html")
        user = User(username=username, email=email)
        user.set_password(password)
        # Auto-grant admin if email is admin@buildlab.ph
        if email == "admin@buildlab.ph":
            user.is_admin = True
        db.session.add(user)
        db.session.commit()
        flash("Account created! Please log in.", "success")
        return redirect(url_for("auth.login"))
    return render_template("auth/register.html")


@auth_bp.route("/logout")
def logout():
    # Mark user as inactive before clearing session
    if session.get("user_id"):
        user = User.query.get(session["user_id"])
        if user:
            user.is_active = False
            # Set last_active to past time to ensure they show as offline
            user.last_active = datetime.datetime.utcnow() - datetime.timedelta(seconds=180)
            db.session.commit()
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("main.index"))


@auth_bp.route("/profile", methods=["GET", "POST"])
def profile():
    """User profile page - view and manage profile."""
    if not session.get("user_id"):
        flash("Please log in to view your profile.", "warning")
        return redirect(url_for("auth.login"))
    
    user = User.query.get(session["user_id"])
    if not user:
        session.clear()
        return redirect(url_for("auth.login"))
    
    # Get user's builds
    builds = Build.query.filter_by(user_id=user.user_id).all()
    
    # Get recent activities (limit to 10) - handle if table doesn't exist
    try:
        activities = Activity.get_recent_activities(user.user_id, limit=10)
    except Exception:
        activities = []
    
    # Count stats
    compatibility_checks = len(activities)  # or implement actual counter
    comparisons_made = 0  # implement if needed
    components_used = sum(
        len([c for c in b.component_ids if c]) 
        for b in builds
    ) if builds else 0
    
    return render_template(
        "profile.html",
        user=user,
        builds=builds,
        activities=activities,
        compatibility_checks=compatibility_checks,
        comparisons_made=comparisons_made,
        components_used=components_used
    )


@auth_bp.route("/profile/edit-info", methods=["POST"])
def edit_profile_info():
    """Update account information (username, email, country, profile picture)."""
    if not session.get("user_id"):
        return jsonify({"success": False, "message": "Not logged in"}), 401
    
    user = User.query.get(session["user_id"])
    if not user:
        session.clear()
        return jsonify({"success": False, "message": "User not found"}), 404
    
    try:
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        country = request.form.get("country", "").strip()
        profile_picture = request.form.get("profile_picture", "").strip()

        original_username = user.username
        original_email = user.email
        original_country = user.country
        original_profile_picture = user.profile_picture
        
        # Validate username
        if username and username != original_username:
            if User.query.filter_by(username=username).first():
                return jsonify({"success": False, "message": "Username already taken."}), 400
            user.username = username
            session["username"] = username
        
        # Validate email
        if email and email != original_email:
            if User.query.filter_by(email=email).first():
                return jsonify({"success": False, "message": "Email already registered."}), 400
            user.email = email
            session["email"] = email
        
        # Update other fields
        if country and country != original_country:
            user.country = country
        
        if profile_picture and profile_picture != original_profile_picture:
            user.profile_picture = profile_picture
        
        db.session.commit()
        
        # Log activity
        changes = []
        if username and username != original_username:
            changes.append("username")
        if email and email != original_email:
            changes.append("email")
        if country and country != original_country:
            changes.append("country")
        if profile_picture and profile_picture != original_profile_picture:
            changes.append("profile picture")
        
        if changes:
            ActivityService.log_profile_update(user.user_id, changes)
        
        return jsonify({"success": True, "message": "Profile updated successfully!"}), 200
    
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@auth_bp.route("/profile/change-password", methods=["POST"])
def change_password():
    """Change user password with old password verification."""
    if not session.get("user_id"):
        return jsonify({"success": False, "message": "Not logged in"}), 401
    
    user = User.query.get(session["user_id"])
    if not user:
        session.clear()
        return jsonify({"success": False, "message": "User not found"}), 404
    
    try:
        old_password = request.form.get("old_password", "")
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")
        
        # Validate old password
        if not user.check_password(old_password):
            return jsonify({"success": False, "message": "Current password is incorrect."}), 400
        
        # Validate new password
        if not new_password or len(new_password) < 6:
            return jsonify({"success": False, "message": "New password must be at least 6 characters."}), 400
        
        # Confirm passwords match
        if new_password != confirm_password:
            return jsonify({"success": False, "message": "Passwords do not match."}), 400
        
        # Update password
        user.set_password(new_password)
        db.session.commit()
        
        # Log activity
        ActivityService.log_password_change(user.user_id)
        
        return jsonify({"success": True, "message": "Password changed successfully!"}), 200
    
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@auth_bp.route("/profile/activities", methods=["GET"])
def get_activities():
    """Get user's recent activities (JSON)."""
    if not session.get("user_id"):
        return jsonify({"success": False, "message": "Not logged in"}), 401
    
    user = User.query.get(session["user_id"])
    if not user:
        session.clear()
        return jsonify({"success": False, "message": "User not found"}), 404
    
    try:
        activities = Activity.get_recent_activities(user.user_id, limit=10)
        
        activities_data = [
            {
                "id": activity.activity_id,
                "action_type": activity.action_type,
                "description": activity.description,
                "timestamp": activity.timestamp.strftime("%B %d, %Y at %I:%M %p")
            }
            for activity in activities
        ]
        
        return jsonify({"success": True, "activities": activities_data}), 200
    
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@auth_bp.route("/heartbeat", methods=["POST"])
def heartbeat():
    """
    Heartbeat endpoint to track user online/offline status.
    Frontend sends periodic heartbeats while the browser window is active.
    """
    if not session.get("user_id"):
        return jsonify({"success": False, "message": "Not logged in"}), 401
    
    try:
        user = User.query.get(session["user_id"])
        if not user:
            session.clear()
            return jsonify({"success": False, "message": "User not found"}), 404
        
        # Update user's activity status
        user.is_active = True
        user.last_active = datetime.datetime.utcnow()
        db.session.commit()
        
        return jsonify({"success": True, "message": "Heartbeat received", "timestamp": user.last_active.isoformat()}), 200
    
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@auth_bp.route("/set-offline", methods=["POST"])
def set_offline():
    """
    Explicitly mark user as offline.
    Called when browser tab is hidden, unfocused, or being closed.
    """
    if not session.get("user_id"):
        return jsonify({"success": False, "message": "Not logged in"}), 401
    
    try:
        user = User.query.get(session["user_id"])
        if not user:
            session.clear()
            return jsonify({"success": False, "message": "User not found"}), 404
        
        # Immediately mark user as offline by setting last_active to a past time
        # This ensures they won't show as online in the next admin status check
        user.is_active = False
        user.last_active = datetime.datetime.utcnow() - datetime.timedelta(seconds=180)
        db.session.commit()
        
        return jsonify({"success": True, "message": "User marked offline"}), 200
    
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
