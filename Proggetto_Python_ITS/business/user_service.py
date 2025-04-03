# business/user_service.py
from persistence.user_repository import UserRepository

class UserService:
    def __init__(self):
        self.user_repository = UserRepository()
    
    def validate_user(self, username, password):
        """Validate user credentials"""
        users = self.user_repository.load_users()
        return username in users and users[username] == password
    
    def user_exists(self, username):
        """Check if a user already exists"""
        users = self.user_repository.load_users()
        return username in users
    
    def register_user(self, username, password):
        """Register a new user"""
        self.user_repository.save_user(username, password)