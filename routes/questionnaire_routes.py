"""
Questionnaire routes — AI PC Builder questionnaire flow.
Guides users through questions to find the perfect build.
"""

import json
from flask import (
    Blueprint,
    render_template,
    request,
    jsonify,
    redirect,
    url_for,
    session,
    flash,
)
from database.db import db
from models.build import Build
from models.component import Component
from services.build_finder.questionnaire_service import get_build_recommendation
from services.activity.activity_service import ActivityService

questionnaire_bp = Blueprint("questionnaire", __name__)


@questionnaire_bp.route("/questionnaire")
def questionnaire():
    """Render the questionnaire page."""
    return render_template("builder/questionnaire.html")


@questionnaire_bp.route("/questionnaire/recommend", methods=["POST"])
def recommend():
    """
    API endpoint: Takes questionnaire answers and returns a recommended build.

    Expected JSON:
    {
        "targetTier": "string",
        "budget": "string",
        "formFactor": "string",
        "style": "string",
        "platform": "string"
    }
    """
    try:
        answers = request.get_json()
        if not answers:
            return jsonify({"error": "No answers provided"}), 400

        # Get the recommendation
        recommendation = get_build_recommendation(answers)

        # Log activity if user is logged in
        if "user_id" in session:
            ActivityService.log_questionnaire_completed(session["user_id"])

        return jsonify(recommendation), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@questionnaire_bp.route("/questionnaire/create-build", methods=["POST"])
def create_build_from_questionnaire():
    """
    API endpoint: Creates a build from questionnaire recommendations.
    User must be logged in.

    Expected JSON:
    {
        "component_ids": [int, ...],
        "build_name": "string",
        "answers": {...}
    }
    """
    if not session.get("user_id"):
        return jsonify({"error": "Please log in to create builds"}), 401

    try:
        data = request.get_json()
        component_ids = data.get("component_ids", [])
        build_name = data.get("build_name", "AI Questionnaire Build")

        if not component_ids:
            return jsonify({"error": "No components in build"}), 400

        # Calculate total price
        total_price = 0
        for cid in component_ids:
            comp = Component.query.get(cid)
            if comp:
                total_price += comp.price

        # Create the build
        build = Build(
            user_id=session["user_id"],
            name=build_name,
            component_ids=json.dumps(component_ids),
            total_price=total_price,
            compatibility_status="pending",
        )

        db.session.add(build)
        db.session.commit()

        # Log activity
        ActivityService.log_build_created(session["user_id"], build_name)

        return (
            jsonify(
                {
                    "success": True,
                    "build_id": build.build_id,
                    "message": f"Build '{build_name}' created successfully!",
                }
            ),
            201,
        )

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
