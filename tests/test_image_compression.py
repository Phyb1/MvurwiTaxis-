from io import BytesIO

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from taxis.models import Payment


def _fake_photo(width=3000, height=2000, name="car.jpg"):
    img = Image.new("RGB", (width, height), color=(120, 180, 40))
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=95)
    return SimpleUploadedFile(name, buf.getvalue(), content_type="image/jpeg")


@pytest.mark.django_db
def test_driver_photo_is_downscaled_on_save(driver_user):
    driver_user.photo = _fake_photo(3000, 2000)
    driver_user.save()

    driver_user.refresh_from_db()
    with Image.open(driver_user.photo.path) as img:
        assert max(img.size) <= 1280


@pytest.mark.django_db
def test_driver_photo_under_max_dimension_is_left_alone_in_size(driver_user):
    # A small photo shouldn't be upscaled — thumbnail() only ever shrinks.
    driver_user.photo = _fake_photo(400, 300)
    driver_user.save()

    driver_user.refresh_from_db()
    with Image.open(driver_user.photo.path) as img:
        assert img.size == (400, 300)


@pytest.mark.django_db
def test_resaving_driver_without_new_photo_does_not_recompress(driver_user):
    driver_user.photo = _fake_photo(3000, 2000)
    driver_user.save()
    driver_user.refresh_from_db()
    first_size = driver_user.photo.size

    # Change an unrelated field and save again — the already-committed photo
    # file must not be re-processed (FieldFile._committed should be True now).
    driver_user.base_area = "Mvurwi Growth Point"
    driver_user.save()
    driver_user.refresh_from_db()

    assert driver_user.photo.size == first_size


@pytest.mark.django_db
def test_payment_proof_of_payment_is_downscaled_on_save(driver_user, hot_lead):
    payment = Payment(
        driver=driver_user, purpose=Payment.Purpose.HOT_LEAD, amount_usd="0.20",
        related_lead=hot_lead, proof_of_payment=_fake_photo(2500, 1800, name="proof.jpg"),
    )
    payment.save()

    payment.refresh_from_db()
    with Image.open(payment.proof_of_payment.path) as img:
        assert max(img.size) <= 1280
