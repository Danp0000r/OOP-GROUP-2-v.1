import re
from database.db import db


class Link(db.Model):

    __bind_key__ = 'components'

    __tablename__ = "links"

    link_id = db.Column(
        db.Integer,
        primary_key=True
    )

    component_id = db.Column(
        db.Integer,
        db.ForeignKey('components.component_id')
    )

    store = db.Column(
        db.String(100)
    )

    url = db.Column(
        db.String(500)
    )

    verified = db.Column(
        db.Boolean,
        default=False
    )

    price = db.Column(
        db.Float,
        default=0.0
    )

    @property
    def id(self):
        return self.link_id

    def normalized_url(self):
        raw_url = (getattr(self, 'url', None) or '').strip()
        if raw_url and not re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:', raw_url):
            return f"https://{raw_url}"
        return raw_url

    def to_dict(self):
        return {
            "id": self.id,
            "component_id": self.component_id,
            "store": getattr(self, 'store', None),
            # provide legacy/template-friendly alias
            "store_name": getattr(self, 'store', None),
            "url": self.normalized_url(),
            "price": float(self.price or 0),
            "verified": bool(self.verified)
        }