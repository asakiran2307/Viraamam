"""Image service — validate, re-encode, and serve images safely."""
import io
from PIL import Image, UnidentifiedImageError
from flask import current_app


ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_DIMENSION = 2000  # px


def process_uploaded_image(file_storage) -> tuple[bytes, str]:
    """
    Validate and re-encode an uploaded image.
    Returns (image_bytes, mime_type) or raises ValueError.
    """
    raw_bytes = file_storage.read()
    if not raw_bytes:
        raise ValueError("Empty file uploaded.")

    max_size = current_app.config.get("MAX_CONTENT_LENGTH", 5 * 1024 * 1024)
    if len(raw_bytes) > max_size:
        raise ValueError(f"File exceeds maximum size of {max_size // (1024*1024)} MB.")

    # Validate via Pillow magic bytes (not just extension)
    try:
        img = Image.open(io.BytesIO(raw_bytes))
        img.verify()  # raises on corrupt/malicious
    except (UnidentifiedImageError, Exception) as e:
        raise ValueError(f"Invalid image file: {e}")

    # Re-open after verify (verify exhausts the stream)
    img = Image.open(io.BytesIO(raw_bytes))

    # Reject SVG (Pillow won't open it, but belt-and-suspenders)
    fmt = img.format
    if fmt not in ("JPEG", "PNG", "WEBP"):
        raise ValueError("Only JPEG, PNG, and WebP images are allowed.")

    # Resize if too large
    if img.width > MAX_DIMENSION or img.height > MAX_DIMENSION:
        img.thumbnail((MAX_DIMENSION, MAX_DIMENSION), Image.LANCZOS)

    # Convert RGBA/P to RGB for JPEG output
    output_format = "JPEG"
    mime_type = "image/jpeg"
    if img.mode in ("RGBA", "P", "LA"):
        background = Image.new("RGB", img.size, (255, 255, 255))
        if img.mode == "P":
            img = img.convert("RGBA")
        if img.mode in ("RGBA", "LA"):
            background.paste(img, mask=img.split()[-1])
        img = background

    # Re-encode to strip any metadata/payloads
    buf = io.BytesIO()
    img.save(buf, format=output_format, quality=85, optimize=True)
    return buf.getvalue(), mime_type
