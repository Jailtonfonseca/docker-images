import json
from flask_login import UserMixin
from app import app

# Simple file-based user store
USER_STORE_PATH = '/app_data/users.json'

class User(UserMixin):
    def __init__(self, id, username, password_hash):
        self.id = id
        self.username = username
        self.password_hash = password_hash

    @staticmethod
    def get_all_users():
        try:
            with open(USER_STORE_PATH, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    @staticmethod
    def find_by_username(username):
        users = User.get_all_users()
        user_data = next((u for u in users if u['username'] == username), None)
        if user_data:
            return User(id=user_data['id'], username=user_data['username'], password_hash=user_data['password_hash'])
        return None

    @staticmethod
    def find_by_id(user_id):
        users = User.get_all_users()
        user_data = next((u for u in users if u['id'] == user_id), None)
        if user_data:
            return User(id=user_data['id'], username=user_data['username'], password_hash=user_data['password_hash'])
        return None

    @staticmethod
    def save_user(username, password_hash):
        users = User.get_all_users()
        new_id = len(users) + 1
        users.append({'id': new_id, 'username': username, 'password_hash': password_hash})
        with open(USER_STORE_PATH, 'w') as f:
            json.dump(users, f, indent=4)
        return new_id