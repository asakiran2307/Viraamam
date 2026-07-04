"""AmbiencePhoto model — admin-uploaded gallery images for the Ambience page."""
from datetime import datetime
from ..extensions import db


class AmbiencePhoto(db.Model):
    __tablename__ = "ambience_photos"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    caption = db.Column(db.String(500), nullable=True)
    image_data = db.Column(db.LargeBinary, nullable=False)
    image_mime_type = db.Column(db.String(50), nullable=False)
    display_order = db.Column(db.Integer, default=0, index=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<AmbiencePhoto {self.title}>"
