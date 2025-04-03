# business/game_service.py
import plotly.express as px
from persistence.game_repository import GameRepository

class GameService:
    def __init__(self):
        self.game_repository = GameRepository()
        self.saved_games = []
        self.searched_games = []
    
    def get_trending_games(self):
        """Ottieni i giochi di tendenza dal repository"""
        if not self.saved_games:
            self.saved_games = self.game_repository.load_trending_games()
        return self.saved_games
    
    def search_games(self, query):
        """Cerca giochi in base a una query"""
        if not query:
            return self.get_trending_games()
        
        self.searched_games = self.game_repository.search_games(query)
        return self.searched_games
    
    def get_game_by_slug(self, slug):
        """Ottieni un gioco specifico tramite il suo slug e restituisci le informazioni sui prezzi"""
        # Combina tutti i giochi per la ricerca
        all_games = self.saved_games + self.searched_games
        
        game = None
        price_info = {
            'steam': "Non disponibile",
            'ig': "Non disponibile"
        }
        
        # Trova il gioco con lo slug fornito
        for gioco in all_games:
            if gioco["slug"] == slug:
                game = gioco
                
                # Ottieni le informazioni sui prezzi per Steam e Instant Gaming
                if "steam" in gioco["link"]:
                    price_info['steam'] = f"{gioco['prezzo']}€" if gioco["prezzo"] else "Non disponibile"
                else:
                    price_info['ig'] = f"{gioco['prezzo']}€" if gioco["prezzo"] else "Non disponibile"
                
                break
        
        return game, price_info
    
    def find_game_by_slug(self, slug):
        """Trova un gioco tramite il suo slug in tutti i giochi disponibili"""
        # Combina tutti i giochi per la ricerca
        all_games = self.saved_games + self.searched_games
        
        for game in all_games:
            if game["slug"] == slug:
                return game
        
        return None
    
    def generate_price_graph(self, games):
        """Genera un grafico HTML per il confronto dei prezzi"""
        graph_html = ""
        
        # Verifica se ci sono giochi con prezzi validi
        if games and any(
            (game.get('prezzo_steam') is not None and game['prezzo_steam'] > 0) or
            (game.get('prezzo_ig') is not None and game['prezzo_ig'] > 0)
            for game in games
        ):
            # Crea il grafico a barre che confronta i prezzi
            fig = px.bar(
                games, 
                x='titolo', 
                y=['prezzo_steam', 'prezzo_ig'], 
                title='Confronto Prezzi Steam vs Instant Gaming', 
                labels={'prezzo_steam': 'Prezzo Steam (€)', 'prezzo_ig': 'Prezzo Instant Gaming (€)'},
                barmode='group'
            )

            fig.update_layout(
                paper_bgcolor="#263246",  # Colore di sfondo più scuro
                font=dict(
                    color="white"  # Imposta il colore del testo su bianco
                )
            )

            # Converti la figura in HTML
            graph_html = fig.to_html(full_html=False)
        
        return graph_html