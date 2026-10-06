import base64
import hashlib
import io
import secrets

import segno  # pip install segno  (pure Python)


def new_token() -> str:
    return secrets.token_urlsafe(24)  # 192 bits, unguessable


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def qr_png_base64(url: str) -> str:
    buf = io.BytesIO()
    # error level 'q' keeps it scannable if a printed card gets scuffed
    segno.make(url, error="q").save(buf, kind="png", scale=8, border=4)
    return base64.b64encode(buf.getvalue()).decode()


def qr_svg(url: str) -> str:
    buf = io.BytesIO()
    segno.make(url, error="q").save(buf, kind="svg", scale=8, border=4)
    return buf.getvalue().decode()
