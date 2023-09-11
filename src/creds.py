import os
from base64 import b64encode
from hashlib import sha256


def get_creds_hash(username: str, password: str, add_salt: bool = True) -> str:
    user_data = username + password
    if add_salt:
        user_data = user_data + os.urandom(32).hex()
    return b64encode(sha256(user_data.encode("utf8")).digest(), altchars=b"ab").decode("ascii").strip("=")
