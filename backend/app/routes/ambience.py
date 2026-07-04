"""Public ambience route — gallery page."""
import hashlib
from flask import Blueprint, render_template, Response, make_response, request, abort
from ..models.ambience import AmbiencePhoto

ambience_bp = Blueprint("ambience", __name__)


@ambience_bp.route("/")
def gallery():
    photos = (AmbiencePhoto.query
              .filter_by(is_active=True)
              .order_by(AmbiencePhoto.display_order, AmbiencePhoto.created_at.desc())
              .all())
    return render_template("ambience.html", photos=photos)


@ambience_bp.route("/<int:photo_id>/image")
def photo_image(photo_id: int):
    """Serve ambience photo from DB with HTTP caching headers."""
    photo = AmbiencePhoto.query.with_entities(
        AmbiencePhoto.id, AmbiencePhoto.image_data, AmbiencePhoto.image_mime_type
    ).filter_by(id=photo_id, is_active=True).first_or_404()

    if not photo.image_data:
        abort(404)

    etag = hashlib.md5(photo.image_data[:64]).hexdigest()
    if request.headers.get("If-None-Match") == etag:
        return Response(status=304)

    resp = make_response(photo.image_data)
    resp.headers["Content-Type"] = photo.image_mime_type or "image/jpeg"
    resp.headers["Cache-Control"] = "public, max-age=86400"
    resp.headers["ETag"] = etag
    return resp
