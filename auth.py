import json
import os

USER_FILE = "users.json"

def load_users():
    if not os.path.exists(USER_FILE):
        return {}
    with open(USER_FILE, "r") as f:
        return json.load(f)

def save_users(users):
    with open(USER_FILE, "w") as f:
        json.dump(users, f, indent=4)

def register(username, password, role="user"):
    users = load_users()
    if username in users:
        return False, "User đã tồn tại"

    users[username] = {
        "password": password,
        "role": role
    }
    save_users(users)
    return True, "Đăng ký thành công"

def login(username, password):
    users = load_users()
    if username not in users:
        return False, None

    if users[username]["password"] != password:
        return False, None

    return True, users[username]["role"]