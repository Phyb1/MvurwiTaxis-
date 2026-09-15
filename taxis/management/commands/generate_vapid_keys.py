import base64

from cryptography.hazmat.primitives.asymmetric import ec
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = (
        "Generate a fresh VAPID keypair for Web Push and print the .env "
        "lines to add. Run this once per deployment — never share or reuse "
        "a keypair across unrelated projects."
    )

    def handle(self, *args, **options):
        private_key = ec.generate_private_key(ec.SECP256R1())
        public_key = private_key.public_key()

        numbers = public_key.public_numbers()
        x = numbers.x.to_bytes(32, "big")
        y = numbers.y.to_bytes(32, "big")
        public_raw = b"\x04" + x + y
        public_b64 = base64.urlsafe_b64encode(public_raw).rstrip(b"=").decode()

        private_value = private_key.private_numbers().private_value
        private_raw = private_value.to_bytes(32, "big")
        private_b64 = base64.urlsafe_b64encode(private_raw).rstrip(b"=").decode()

        self.stdout.write(self.style.SUCCESS("Add these to your .env:\n"))
        self.stdout.write(f"VAPID_PUBLIC_KEY={public_b64}")
        self.stdout.write(f"VAPID_PRIVATE_KEY={private_b64}")
        self.stdout.write(
            self.style.WARNING(
                "\nKeep VAPID_PRIVATE_KEY secret — it authenticates your server "
                "to push services on every notification sent."
            )
        )
