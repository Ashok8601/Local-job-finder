from isvalid import hash_password, verify_password

# Step 1: Akash ka hashed password generate karna
hashed_password = hash_password("akash")
print(f"Hashed Password: {hashed_password}")

# Step 2: Password verify karna
user_input = "akash"  # Yahan user ka input hoga

if verify_password(hashed_password, user_input):
    print("✅ Password match ho gaya, login successful!")
else:
    print("❌ Invalid password, login failed!")
if __name__ == '__main__':
    app.run(debug=True)
