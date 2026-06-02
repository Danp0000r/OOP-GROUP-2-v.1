import datetime
from database.db import db


class Activity(db.Model):
    """Track user activities for profile recent activity section."""

    __tablename__ = "activities"

    activity_id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        nullable=False
    )

    action_type = db.Column(
        db.String(100),
        nullable=False
    )

    description = db.Column(
        db.String(255),
        nullable=False
    )

    timestamp = db.Column(
        db.DateTime,
        default=datetime.datetime.utcnow,
        nullable=False
    )

    @classmethod
    def log_activity(cls, user_id, action_type, description):
        """Create and log a new activity."""
        activity = cls(
            user_id=user_id,
            action_type=action_type,
            description=description
        )
        db.session.add(activity)
        db.session.commit()
        return activity

    @classmethod
    def get_recent_activities(cls, user_id, limit=10):
        """Get recent activities for a user, limited to specified number."""
        return cls.query.filter_by(user_id=user_id).order_by(
            cls.timestamp.desc()
        ).limit(limit).all()
