from database import db


for user in [
    "Lucas",
    "Emma",
    "Liam",
    "Chloé",
    "Noah",
    "Léa",
    "Gabriel",
    "Inès",
    "Arthur",
    "Manon",
    "Louis",
    "Camille",
    "Jules",
    "Sarah",
    "Hugo",
    "Zoé",
    "Nathan",
    "Anna",
    "Raphaël",
    "Clara",
]:
    # continue
    db.create_user(name=user, email=f"{user}@gmail.com")

users = db.get_all_users()

print(f"Fetched {len(users)} users.")
