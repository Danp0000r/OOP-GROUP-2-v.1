from database.db import db


class Component(db.Model):
    """PC component model with specs and pricing."""

    __bind_key__ = "components"
    __tablename__ = "components"

    component_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    brand = db.Column(db.String(100), nullable=False)
    external_id = db.Column(db.String(100), unique=True, nullable=False)
    specs = db.Column(db.JSON, nullable=False)
    compatibility = db.Column(db.JSON, nullable=False, default={})
    price = db.Column(db.Float, default=0, nullable=False)
    performance_score = db.Column(db.Integer, default=50, nullable=False)
    image_url = db.Column(db.String(500), default="")
    description = db.Column(db.Text, default="")
    links = db.relationship(
        "Link", backref="component", lazy=True, cascade="all, delete-orphan"
    )

    @property
    def id(self):
        return self.component_id

    def to_dict(self):
        """Serialize component to dictionary."""
        return {
            "id": self.id,
            "external_id": self.external_id,
            "name": self.name,
            "brand": self.brand,
            "category": self.category,
            "specs": self.specs,
            "compatibility": self.compatibility,
            "price": self.price,
            "performance_score": self.performance_score,
            "image_url": self.image_url,
            "description": self.description,
            "links": [l.to_dict() for l in self.links] if self.links else [],
        }

    def get_details(self):
        """Get component details."""
        return {
            "id": self.component_id,
            "name": self.name,
            "brand": self.brand,
            "category": self.category,
            "specs": self.specs,
            "price": self.price,
            "performance_score": self.performance_score,
            "image_url": self.image_url,
            "description": self.description,
        }
