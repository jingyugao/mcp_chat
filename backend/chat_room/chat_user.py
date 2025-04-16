
from backend.database import User

class User(User):
    def __init__(self, name: str, age: int):
        self.name = name
        self.age = age

