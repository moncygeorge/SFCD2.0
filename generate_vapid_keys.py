"""
generate_vapid_keys.py
-----------------------
Run this once to create a VAPID key pair for Web Push notifications:

    python generate_vapid_keys.py

Then set the printed values as environment variables (locally in a .env
file, or as Heroku config vars):

    VAPID_PUBLIC_KEY=...
    VAPID_PRIVATE_KEY=...
    VAPID_CLAIM_EMAIL=mailto:admin@yourchurch.org

Keep VAPID_PRIVATE_KEY secret — it proves your server's identity to
push services. If it leaks, generate a new pair (existing member
subscriptions will need to re-subscribe).
"""

from py_vapid import Vapid02
import base64


def main():
    vapid = Vapid02()
    vapid.generate_keys()

    private_pem = vapid.private_pem().decode('utf-8')

    raw_public = vapid.public_key.public_bytes(
        encoding=__import__('cryptography').hazmat.primitives.serialization.Encoding.X962,
        format=__import__('cryptography').hazmat.primitives.serialization.PublicFormat.UncompressedPoint,
    )
    public_b64 = base64.urlsafe_b64encode(raw_public).rstrip(b'=').decode('utf-8')

    raw_private = vapid.private_key.private_numbers().private_value.to_bytes(32, 'big')
    private_b64 = base64.urlsafe_b64encode(raw_private).rstrip(b'=').decode('utf-8')

    print("\n=== VAPID keys generated ===\n")
    print(f"VAPID_PUBLIC_KEY={public_b64}")
    print(f"VAPID_PRIVATE_KEY={private_b64}")
    print("VAPID_CLAIM_EMAIL=mailto:admin@yourchurch.org")
    print("\nSet these as environment variables, then restart the app.\n")


if __name__ == '__main__':
    main()
