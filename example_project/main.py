from example_project.models import User

user = User(name="Alice", email="alice@example.com")
user.save()

# found = User.get(id=4, raise_if_not_found=False)
# print(found)
