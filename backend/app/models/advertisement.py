"""Advertisement model for the carousel banner."""
from datetime import date
from ..extensions import db


class Advertisement(db.Model):
    __tablename__ = "advertisements"

    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey("items.id"), nullable=True)
    title = db.Column(db.String(200), nullable=False)
    image_data = db.Column(db.LargeBinary, nullable=True)
    image_mime_type = db.Column(db.String(50), nullable=True)
    display_order = db.Column(db.Integer, default=0, index=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    start_date = db.Column(db.Date, default=date.today, nullable=False)
    end_date = db.Column(db.Date, nullable=False)

    item = db.relationship("Item", foreign_keys=[item_id])

    def __repr__(self):
        return f"<Advertisement {self.title}>"

    @property
    def is_currently_active(self):
        today = date.today()
        return self.is_active and self.start_date <= today <= self.end_date
