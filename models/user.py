import datetime

from database.db import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


class User(UserMixin, db.Model):

    __tablename__ = "users"

    user_id = db.Column(
        db.Integer,
        primary_key=True
    )

    def get_id(self):
        return str(self.user_id)

    @property
    def id(self):
        return self.user_id

    username = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    password = db.Column(
        db.String(255),
        nullable=False
    )

    email = db.Column(
        db.String(255)
    )

    profile_picture = db.Column(
        db.String(500),
        default=None
    )

    is_admin = db.Column(
        db.Boolean,
        default=False
    )

    country = db.Column(
        db.String(100),
        default="Philippines"
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.datetime.utcnow,
        nullable=False
    )

    is_active = db.Column(
        db.Boolean,
        default=False
    )

    last_active = db.Column(
        db.DateTime,
        nullable=True
    )

    def set_password(self, raw):
        self.password = generate_password_hash(raw)

    def check_password(self, raw):
        try:
            return check_password_hash(self.password, raw)
        except Exception:
            return False