import hmac
import hashlib



def verify_signature(headers: dict, payload: str, secret: str) -> bool:
    signature = headers.get("X-Hub-Signature-256")

    if not signature:
        return False
    
    expected_signature = "sha256=" + hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(signature, expected_signature)