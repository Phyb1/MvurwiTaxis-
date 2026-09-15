"""Resize + re-encode uploaded images before they hit disk. Keeps driver
car photos and EcoCash proof screenshots from eating storage/bandwidth on
shared hosting — a phone camera photo can easily be 4-8MB uncompressed."""
from io import BytesIO

from django.core.files.uploadedfile import InMemoryUploadedFile
from PIL import Image

MAX_DIMENSION = 1280
JPEG_QUALITY = 80


def compress_image(uploaded_file, max_dimension=MAX_DIMENSION, quality=JPEG_QUALITY):
    """Take a Django UploadedFile/FieldFile, return a new InMemoryUploadedFile
    that's been downscaled to max_dimension on its longest side and
    re-encoded as JPEG. Returns the input unchanged if it can't be opened
    as an image (corrupt upload) — validation elsewhere should catch that;
    this function's job is compression, not validation."""
    if not uploaded_file:
        return uploaded_file

    try:
        uploaded_file.seek(0)
        img = Image.open(uploaded_file)
        img.load()
    except Exception:
        uploaded_file.seek(0)
        return uploaded_file

    # Flatten to RGB so PNG transparency/CMYK photos don't break JPEG output.
    if img.mode not in ("RGB",):
        img = img.convert("RGB")

    img.thumbnail((max_dimension, max_dimension), Image.LANCZOS)

    buffer = BytesIO()
    img.save(buffer, format="JPEG", quality=quality, optimize=True)
    buffer.seek(0)

    original_name = getattr(uploaded_file, "name", "upload.jpg")
    new_name = original_name.rsplit(".", 1)[0] + ".jpg"

    return InMemoryUploadedFile(
        buffer, None, new_name, "image/jpeg", buffer.getbuffer().nbytes, None
    )
