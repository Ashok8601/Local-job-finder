from werkzeug.security import generate_password_hash, check_password_hash

def hash_password(password):
    return generate_password_hash(password)  # Secure password hashing

def verify_password(stored_password, provided_password):
    return check_password_hash(stored_password, provided_password)  # Verify hashed password