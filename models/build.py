import datetime
from sqlalchemy.orm import synonym

from database.db import db


class Build(db.Model):

    __tablename__ = "builds"

    build_id = db.Column(db.Integer, primary_key=True)

    id = synonym("build_id")

    user_id = db.Column(db.Integer)

    created_at = db.Column(
        db.DateTime, default=datetime.datetime.utcnow, nullable=False
    )

    name = db.Column(db.String(100))

    # store component ids as JSON string
    component_ids = db.Column(db.Text, default="[]")

    total_price = db.Column(db.Float, default=0)

    compatibility_status = db.Column(db.String(50))
