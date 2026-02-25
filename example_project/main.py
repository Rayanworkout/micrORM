from database import db

user_names = [
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
]

for user in user_names:
    db.create_user(name=user, email=f"{user}@gmail.com", ignore_conflicts=True)

users = db.get_all_users()

print(f"Fetched {len(users)} users.")
