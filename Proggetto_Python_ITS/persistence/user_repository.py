# persistence/user_repository.py
import pandas as pd
import os

class UserRepository:
    def __init__(self):
        self.users_file = 'users.csv'
    
    def load_users(self):
        """Load users from CSV file"""
        try:
            # Load the CSV into a DataFrame
            users_df = pd.read_csv(self.users_file, header=None, names=['username', 'password'])
            # Convert the DataFrame into a dictionary for easier lookup
            users = users_df.set_index('username').to_dict()['password']
        except FileNotFoundError:
            # Return an empty dictionary if the file does not exist
            users = {}
        return users
    
    def save_user(self, username, password):
        """Save a new user to CSV file"""
        new_user_df = pd.DataFrame([[username, password]], columns=['username', 'password'])
        new_user_df.to_csv(self.users_file, mode='a', header=False, index=False)