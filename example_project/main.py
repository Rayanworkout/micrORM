from database import db

db.create_user(name="rayan")

users = db.get_all_users()

print(f"Fetched {len(users)} users. {users}")
