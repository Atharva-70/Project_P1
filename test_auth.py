from services.auth_services import hash_password, verify_password

password = "admin@123"

hashed = hash_password(password)

print("Hashed:", hashed)

match = verify_password(password, hashed)

print(match)