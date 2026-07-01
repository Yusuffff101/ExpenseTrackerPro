import bcrypt

entered_password = "password123"

stored_hash = "$2b$12$7qeoeCmHKDdM6/N9T5JJU.kU7EonTdrKYv90KPrz8RrjRhu.eFlRq"

if bcrypt.checkpw(
    entered_password.encode(),
    stored_hash.encode()
):
    print("✅ Login successful!")
else:
    print("❌ Wrong password")