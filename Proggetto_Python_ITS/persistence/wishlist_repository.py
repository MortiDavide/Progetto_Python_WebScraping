# persistence/wishlist_repository.py
import pandas as pd
import os

class WishlistRepository:
    def __init__(self):
        self.wishlist_dir = "wishlists"
        # Assicuriamoci che la directory esista
        if not os.path.exists(self.wishlist_dir):
            os.makedirs(self.wishlist_dir)
    
    def get_user_wishlist_path(self, username):
        """Ottieni il percorso del file wishlist per uno specifico utente"""
        return os.path.join(self.wishlist_dir, f"{username}_wishlist.csv")
    
    def load_wishlist(self, username):
        """Carica la wishlist da file CSV per uno specifico utente"""
        wishlist_games = []
        wishlist_file = self.get_user_wishlist_path(username)
        
        if os.path.exists(wishlist_file):
            df = pd.read_csv(wishlist_file)
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
    
    def save_wishlist(self, username, titolo, piattaforma, prezzo, immagine, link, sito, slug):
        """Salva un gioco nella wishlist di uno specifico utente"""
        wishlist_file = self.get_user_wishlist_path(username)
        nuovo_gioco = pd.DataFrame([[titolo, piattaforma, prezzo, immagine, link, sito, slug]], 
                                 columns=["titolo", "piattaforma", "prezzo", "immagine", "link", "sito", "slug"])

        if os.path.exists(wishlist_file):
            df = pd.read_csv(wishlist_file)
            # Verifica se il gioco è già presente (evita duplicati)
            if not (df["slug"] == slug).any():
                df = pd.concat([df, nuovo_gioco], ignore_index=True)
        else:
            df = nuovo_gioco

        df.to_csv(wishlist_file, index=False)
    
    def remove_from_wishlist(self, username, slug):
        """Rimuove un gioco dalla wishlist di uno specifico utente tramite slug"""
        wishlist_file = self.get_user_wishlist_path(username)
        if os.path.exists(wishlist_file):
            df = pd.read_csv(wishlist_file)
            # Rimuove il gioco con lo slug specificato
            df = df[df["slug"] != slug]
            # Salva la wishlist aggiornata
            df.to_csv(wishlist_file, index=False)