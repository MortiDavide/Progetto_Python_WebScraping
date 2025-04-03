# persistence/wishlist_repository.py
import pandas as pd
import os

class WishlistRepository:
    def __init__(self):
        self.wishlist_file = "wishlist.csv"
    
    def load_wishlist(self):
        """Load wishlist from CSV file"""
        wishlist_games = []
        if os.path.exists(self.wishlist_file):
            df = pd.read_csv(self.wishlist_file)
            for _, row in df.iterrows():
                wishlist_games.append({
                    "titolo": row["titolo"],
                    "piattaforma": row["piattaforma"],
                    "prezzo": row["prezzo"],
                    "immagine": row["immagine"],
                    "link": row["link"],
                    "sito": row["sito"],
                    "slug": row["slug"]
                })
        return wishlist_games
    
    def save_wishlist(self, titolo, piattaforma, prezzo, immagine, link, sito, slug):
        """Save a game to the wishlist"""
        nuovo_gioco = pd.DataFrame([[titolo, piattaforma, prezzo, immagine, link, sito, slug]], 
                                 columns=["titolo", "piattaforma", "prezzo", "immagine", "link", "sito", "slug"])

        if os.path.exists(self.wishlist_file):
            df = pd.read_csv(self.wishlist_file)
            df = pd.concat([df, nuovo_gioco], ignore_index=True)
        else:
            df = nuovo_gioco

        df.to_csv(self.wishlist_file, index=False)
    
    def remove_from_wishlist(self, slug):
        """Remove a game from the wishlist by slug"""
        if os.path.exists(self.wishlist_file):
            df = pd.read_csv(self.wishlist_file)
            # Remove the game with the given slug
            df = df[df["slug"] != slug]
            # Save the updated wishlist
            df.to_csv(self.wishlist_file, index=False)