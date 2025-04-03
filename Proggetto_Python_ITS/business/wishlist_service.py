# business/wishlist_service.py
from persistence.wishlist_repository import WishlistRepository

class WishlistService:
    def __init__(self):
        self.wishlist_repository = WishlistRepository()
    
    def load_wishlist(self):
        """Load the user's wishlist"""
        return self.wishlist_repository.load_wishlist()
    
    def add_to_wishlist(self, game):
        """Add a game to the user's wishlist"""
        # Check if game is already in wishlist
        wishlist_games = self.load_wishlist()
        for wishlist_game in wishlist_games:
            if wishlist_game["slug"] == game["slug"]:
                return  # Game already in wishlist
        
        self.wishlist_repository.save_wishlist(
            game["titolo"],
            game["piattaforma"],
            game["prezzo"],
            game["immagine"],
            game["link"],
            game["sito"],
            game["slug"]
        )
    
    def remove_from_wishlist(self, slug):
        """Remove a game from the user's wishlist"""
        self.wishlist_repository.remove_from_wishlist(slug)