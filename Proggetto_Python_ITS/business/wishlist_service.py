# business/wishlist_service.py
from persistence.wishlist_repository import WishlistRepository
from flask import session

class WishlistService:
    def __init__(self):
        self.wishlist_repository = WishlistRepository()
    
    def get_current_username(self):
        """Ottiene lo username dell'utente corrente dalla sessione"""
        return session.get('username')
    
    def load_wishlist(self):
        """Carica la wishlist dell'utente corrente"""
        username = self.get_current_username()
        if not username:
            return []  # Ritorna una lista vuota se l'utente non ha effettuato l'accesso
        return self.wishlist_repository.load_wishlist(username)
    
    def add_to_wishlist(self, game):
        """Aggiunge un gioco alla wishlist dell'utente corrente"""
        username = self.get_current_username()
        if not username:
            return False  # Non può aggiungere se l'utente non ha effettuato l'accesso
        
        self.wishlist_repository.save_wishlist(
            username,
            game["titolo"],
            game["piattaforma"],
            game["prezzo"],
            game["immagine"],
            game["link"],
            game["sito"],
            game["slug"]
        )
        return True
    
    def remove_from_wishlist(self, slug):
        """Rimuove un gioco dalla wishlist dell'utente corrente"""
        username = self.get_current_username()
        if not username:
            return False
        self.wishlist_repository.remove_from_wishlist(username, slug)
        return True