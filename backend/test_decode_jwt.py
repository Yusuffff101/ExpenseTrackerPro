from jose import jwt
from auth import create_access_token, SECRET_KEY, ALGORITHM

token = create_access_token(
    {"sub": "test2@example.com"}
)

print("Token:")
print(token)

payload = jwt.decode(
    token,
    SECRET_KEY,
    algorithms=[ALGORITHM]
)

print("\nDecoded Payload:")
print(payload)