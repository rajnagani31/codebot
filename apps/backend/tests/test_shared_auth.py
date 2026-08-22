import time
import unittest
from apps.backend.shared.auth import decode_access_token, UserPrincipal
from apps.backend.bot.application.service.auth_service import AuthService
from apps.backend.shared.auth.jwt_utils import AuthException


class TestSharedAuth(unittest.TestCase):
    def test_shared_jwt_decode(self):
        secret = "codebot-dev-jwt-secret"
        auth_service = AuthService(repository=None, secret=secret)

        payload = {
            "typ": "access",
            "sub": "123",
            "email": "test@example.com",
            "user_type": "registered",
            "sid": 456,
            "iat": int(time.time()),
            "exp": int(time.time()) + 3600,
        }
        token = auth_service._encode_token(payload)

        decoded = decode_access_token(token, secret=secret.encode("utf-8"))

        self.assertEqual(decoded.sub, "123")
        self.assertEqual(decoded.email, "test@example.com")
        self.assertEqual(decoded.user_type, "registered")
        self.assertEqual(decoded.sid, 456)

    def test_shared_jwt_expired(self):
        secret = "codebot-dev-jwt-secret"
        auth_service = AuthService(repository=None, secret=secret)

        payload = {
            "typ": "access",
            "sub": "123",
            "exp": int(time.time()) - 100,
        }
        token = auth_service._encode_token(payload)

        with self.assertRaises(AuthException) as ctx:
            decode_access_token(token, secret=secret.encode("utf-8"))

        self.assertIn("expired", str(ctx.exception).lower())


if __name__ == "__main__":
    unittest.main()
