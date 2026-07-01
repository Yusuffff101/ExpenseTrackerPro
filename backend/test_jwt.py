from auth import create_access_token

token = create_access_token(
    {"sub": "test2@example.com"}
)

print("JWT Token:")
print(token)