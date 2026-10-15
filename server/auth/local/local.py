import secrets
from base64 import b32encode
from datetime import datetime, timedelta

from fastapi import Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pyotp import TOTP
from pyotp.utils import build_uri
from qrcode import QRCode

from global_config import AuthType, GlobalConfig
from helpers import get_env

try:
    import security
except ImportError:
    from server import security

from ..base import BaseAuth
from ..models import Login, Token

global_config = GlobalConfig()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/token", auto_error=False)


class LocalAuth(BaseAuth):
    JWT_ALGORITHM = "HS256"

    def __init__(self) -> None:
        self.username = get_env("SIWAN_USERNAME", fallback_keys=["FLATNOTES_USERNAME"], mandatory=False, default="admin").lower()
        self.session_expiry_days = get_env(
            "SIWAN_SESSION_EXPIRY_DAYS", fallback_keys=["FLATNOTES_SESSION_EXPIRY_DAYS"], default=30, cast_int=True
        )

        # TOTP
        self.is_totp_enabled = False
        if global_config.auth_type == AuthType.TOTP:
            self.is_totp_enabled = True
            self.totp_key = get_env("SIWAN_TOTP_KEY", fallback_keys=["FLATNOTES_TOTP_KEY"], mandatory=True)
            self.totp_key = b32encode(self.totp_key.encode("utf-8"))
            self.totp = TOTP(self.totp_key)
            self.last_used_totp = None
            self._display_totp_enrolment()

    def login(self, data: Login) -> Token:
        # Check Username
        username_correct = secrets.compare_digest(
            self.username.lower(), data.username.lower()
        )

        # Check Password & TOTP
        perms = security.get_permissions()
        stored_password_hash = perms.get("admin_password", "")

        if self.is_totp_enabled:
            current_totp = self.totp.now()
            if len(data.password) > 6:
                plain_pwd = data.password[:-6]
                input_totp = data.password[-6:]
                password_correct = (
                    security.verify_password(plain_pwd, stored_password_hash)
                    and secrets.compare_digest(current_totp, input_totp)
                    and (current_totp != self.last_used_totp)
                )
                if password_correct:
                    self.last_used_totp = current_totp
            else:
                password_correct = False
        else:
            password_correct = security.verify_password(data.password, stored_password_hash)

        # Raise error if incorrect
        if not (username_correct and password_correct):
            raise ValueError("Incorrect login credentials.")

        # Create Token
        access_token = self._create_access_token(data={"sub": self.username})
        return Token(access_token=access_token)

    def authenticate(
        self, request: Request, token: str = Depends(oauth2_scheme)
    ):
        # If no token is found in the header, check the cookies
        if token is None:
            token = request.cookies.get("token")
        # Validate the token
        try:
            self._validate_token(token)
        except (JWTError, ValueError):
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

    def _validate_token(self, token: str) -> bool:
        if token is None:
            raise ValueError
        secret_key = security.get_jwt_secret()
        payload = jwt.decode(
            token, secret_key, algorithms=[self.JWT_ALGORITHM]
        )
        username = payload.get("sub")
        if username is None or username.lower() != self.username:
            raise ValueError
        token_ver = payload.get("ver")
        current_ver = security.get_permissions().get("token_version", 1)
        if token_ver is not None and token_ver != current_ver:
            raise ValueError("Token revoked")
        return True

    def _create_access_token(self, data: dict):
        to_encode = data.copy()
        expiry_datetime = datetime.utcnow() + timedelta(
            days=self.session_expiry_days
        )
        to_encode.update({
            "exp": expiry_datetime,
            "role": "admin",
            "ver": security.get_permissions().get("token_version", 1)
        })
        secret_key = security.get_jwt_secret()
        encoded_jwt = jwt.encode(
            to_encode, secret_key, algorithm=self.JWT_ALGORITHM
        )
        return encoded_jwt

    def _display_totp_enrolment(self):
        # Fix for #237. Remove padding as per spec:
        # https://github.com/google/google-authenticator/wiki/Key-Uri-Format#secret
        unpadded_secret = self.totp_key.rstrip(b"=")
        uri = build_uri(unpadded_secret, self.username, issuer="flatnotes")
        qr = QRCode()
        qr.add_data(uri)
        print(
            "\nScan this QR code with your TOTP app of choice",
            "e.g. Authy or Google Authenticator:",
        )
        qr.print_ascii()
        print(
            f"Or manually enter this key: {self.totp.secret.decode('utf-8')}\n"
        )
