# business/game_service.py
import plotly.express as px
from persistence.game_repository import GameRepository

class GameService:
    def __init__(self):
        self.game_repository = GameRepository()
        self.saved_games = []
        self.searched_games = []
    
    def get_trending_games(self):
        """Get trending games from the repository"""
        if not self.saved_games:
            self.saved_games = self.game_repository.load_trending_games()
        return self.saved_games
    
    def search_games(self, query):
        """Search for games based on a query"""
        if not query:
            return self.get_trending_games()
        
        self.searched_games = self.game_repository.search_games(query)
        return self.searched_games
    
    def get_game_by_slug(self, slug):
        """Get a specific game by its slug and return pricing info"""
        # Combine all games for searching
        all_games = self.saved_games + self.searched_games
        
        game = None
        price_info = {
            'steam': "Non disponibile",
            'ig': "Non disponibile"
        }
        
        # Find the game with the given slug
        for gioco in all_games:
            if gioco["slug"] == slug:
                game = gioco
                
                # Get price info for Steam and Instant Gaming
                if "steam" in gioco["link"]:
                    price_info['steam'] = f"{gioco['prezzo']}€" if gioco["prezzo"] else "Non disponibile"
                else:
                    price_info['ig'] = f"{gioco['prezzo']}€" if gioco["prezzo"] else "Non disponibile"
                
                break
        
        return game, price_info
    
    def find_game_by_slug(self, slug):
        """Find a game by its slug in all available games"""
        # Combine all games for searching
        all_games = self.saved_games + self.searched_games
        
        for game in all_games:
            if game["slug"] == slug:
                return game
        
        return None
    
    def generate_price_graph(self, games):
        """Generate an HTML graph for price comparison"""
        graph_html = ""
        
        # Check if there are games with valid prices
        if games and any(
            (game.get('prezzo_steam') is not None and game['prezzo_steam'] > 0) or
            (game.get('prezzo_ig') is not None and game['prezzo_ig'] > 0)
            for game in games
        ):
            # Create the bar chart comparing prices
            fig = px.bar(
                games, 
                x='titolo', 
                y=['prezzo_steam', 'prezzo_ig'], 
                title='Confronto Prezzi Steam vs Instant Gaming', 
                labels={'prezzo_steam': 'Prezzo Steam (€)', 'prezzo_ig': 'Prezzo Instant Gaming (€)'},
                barmode='group'
            )

            fig.update_layout(
                paper_bgcolor="#263246",  # Darker background color
                font=dict(
                    color="white"  # Set the text color to white
                )
            )

            # Convert the figure to HTML
            graph_html = fig.to_html(full_html=False)
        
        return graph_html