"""MFA TOTP Service - Two-factor authentication via Google Authenticator"""
import io
import base64
import pyotp
import qrcode


def generate_secret():
    """Generate a new TOTP secret for a user"""
    return pyotp.random_base32()


def get_provisioning_uri(secret, email, issuer="BookKeepr AI"):
    """Build URI for QR code (Google Authenticator compatible)"""
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(name=email, issuer_name=issuer)


def generate_qr_code(secret, email, issuer="BookKeepr AI"):
    """Generate base64-encoded QR code image for setup"""
    uri = get_provisioning_uri(secret, email, issuer)
    qr = qrcode.QRCode(version=1, box_size=8, border=4)
    qr.add_data(uri)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return base64.b64encode(buf.getvalue()).decode('utf-8')


def verify_token(secret, token):
    """Verify a TOTP token. Returns True if valid."""
    if not secret or not token:
        return False
    try:
        totp = pyotp.TOTP(secret)
        return totp.verify(token, valid_window=1)  # accept 1 step before/after
    except Exception:
        return False
