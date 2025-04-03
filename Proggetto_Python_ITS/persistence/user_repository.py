# persistence/user_repository.py
import pandas as pd
import os

class UserRepository:
    def __init__(self):
        self.users_file = 'users.csv'
    
    def load_users(self):
        """Carica gli utenti dal file CSV"""
        try:
            # Carica il CSV in un DataFrame
            users_df = pd.read_csv(self.users_file, header=None, names=['username', 'password'])
            # Converte il DataFrame in un dizionario per una ricerca più facile
            users = users_df.set_index('username').to_dict()['password']
        except FileNotFoundError:
            # Restituisce un dizionario vuoto se il file non esiste
            users = {}
        return users
    
    def save_user(self, username, password):
        """Salva un nuovo utente nel file CSV"""
        new_user_df = pd.DataFrame([[username, password]], columns=['username', 'password'])
        new_user_df.to_csv(self.users_file, mode='a', header=False, index=False)