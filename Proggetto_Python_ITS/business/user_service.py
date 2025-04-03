# business/user_service.py
from persistence.user_repository import UserRepository

class UserService:
    def __init__(self):
        self.user_repository = UserRepository()
    
    def validate_user(self, username, password):
        """Valida le credenziali dell'utente"""
        users = self.user_repository.load_users()
        return username in users and users[username] == password
    
    def user_exists(self, username):
        """Controlla se un utente esiste già"""
        users = self.user_repository.load_users()
        return username in users
    
    def register_user(self, username, password):
        """Registra un nuovo utente"""
        self.user_repository.save_user(username, password)