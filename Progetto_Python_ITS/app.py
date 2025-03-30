# # app.py
# from flask import Flask, render_template, request
# import requests
# from bs4 import BeautifulSoup
# import re

# app = Flask(__name__)

# # Salva i giochi temporaneamente per recuperare i dettagli
# saved_games = []
# searched_games = []

# def generate_slug(title):
#     """Genera uno slug dal titolo del gioco (es. 'Cyberpunk 2077' -> 'cyberpunk-2077')"""
#     return re.sub(r'[^a-zA-Z0-9]+', '-', title.lower()).strip('-')

# def scraping(url):
#     headers = {
#         'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36',
#         'Accept-Language': 'en-US,en;q=0.9'
#     }

#     res = requests.get(url, headers=headers)
#     soup = BeautifulSoup(res.text, 'html.parser')

#     giochi_containers = soup.find_all(class_="item")

#     giochi = []
#     for gioco in giochi_containers:
#         titolo = gioco.find(class_="title")
#         prezzo = gioco.find(class_="price")
#         img_tag = gioco.find("img")
#         link = gioco.find("a", href=True)

#         if titolo and prezzo:
#             titolo_text = titolo.get_text()
#             price = prezzo.get_text().replace("€", "").replace(",", ".")
#             try:
#                 prezzo_float = float(price)
#             except ValueError:
#                 prezzo_float = None
            
#             if img_tag:
#                 immagine_url = img_tag.get("data-src") or img_tag.get("src")  # Usa data-src se presente
#                 if immagine_url.startswith("/"):  # Completa il link se relativo
#                     immagine_url = "https://www.instant-gaming.com" + immagine_url
#             else:
#                 immagine_url = "https://via.placeholder.com/150"

#             link_url = link['href'] if link and 'href' in link.attrs else "#"
            
#             giochi.append({
#                 "titolo": titolo_text,
#                 "prezzo": prezzo_float,
#                 "immagine": immagine_url,
#                 "link": link_url
#             })
        
#     return giochi



# def cerca_giochi(query):
#     """
#     Effettua la ricerca di giochi su instant-gaming in base alla query fornita
#     """
#     if not query:
#         return []
    
#     url = f"https://www.instant-gaming.com/it/ricerca/?query={query}"
    
#     try:
#         return scraping(url)
        
#     except Exception as e:
#         print(f"Errore durante la ricerca: {e}")
#         return [{"titolo": "Errore nel caricamento", "prezzo": None, "immagine": "https://via.placeholder.com/150", "link": "#"}]

# def load_trending_games():
#     """Carica i giochi di tendenza"""
#     try:
#         # Effettua scraping della homepage di Instant Gaming per trovare i giochi di tendenza
        
#         # URL della pagina dei bestseller
#         url = "https://www.instant-gaming.com/it/?utm_source=google&utm_medium=cpc&utm_campaign=1063495812&utm_content=52470996152&utm_term=instant-gaming&gad_source=1&gclid=Cj0KCQjw16O_BhDNARIsAC3i2GBqET0MaxZu3jx5birZ3yGQmmbgbbEr3OYGJLQs_GMcarD2QntMipoaAivXEALw_wcB"
        
#         return scraping(url)
        
#     except Exception as e:
#         print(f"Errore durante il caricamento dei giochi di tendenza: {e}")
#         # Dati di fallback in caso di errore
#         trending_games = [
#             {"titolo": "Grand Theft Auto V", "prezzo": 19.99, "immagine": "https://via.placeholder.com/150", "link": "#"},
#             {"titolo": "Cyberpunk 2077", "prezzo": 29.99, "immagine": "https://via.placeholder.com/150", "link": "#"},
#             {"titolo": "Red Dead Redemption 2", "prezzo": 39.99, "immagine": "https://via.placeholder.com/150", "link": "#"},
#             {"titolo": "FIFA 24", "prezzo": 49.99, "immagine": "https://via.placeholder.com/150", "link": "#"},
#             {"titolo": "Elden Ring", "prezzo": 44.99, "immagine": "https://via.placeholder.com/150", "link": "#"}
#         ]
#         return trending_games
    

# @app.route('/')
# def index():
#     global saved_games
#     saved_games = load_trending_games()
#     return render_template('index.html', games=saved_games, query=None)

# @app.route('/search')
# def search():
#     """Esegue la ricerca e mostra i risultati."""
#     global searched_games
#     query = request.args.get('q', '').strip()
#     if not query:
#         return index()
    
#     searched_games = cerca_giochi(query)  # Salviamo i risultati della ricerca
#     return render_template('index.html', games=searched_games, query=query)

# @app.route('/game/<int:game_id>')
# def game_details(game_id):
#     """Mostra i dettagli di un gioco (sia dai trending che dalla ricerca)."""
#     all_games = saved_games + searched_games  # Unisce entrambe le liste

#     if 0 < game_id <= len(all_games):
#         gioco = all_games[game_id - 1]
#         return render_template('game.html', game=gioco)
    
#     return "Gioco non trovato", 404

# if __name__ == '__main__':
#     app.run(debug=True)
#     # app.run()

from flask import Flask, render_template, request
import requests
from bs4 import BeautifulSoup
import re

app = Flask(__name__)

# Salva i giochi temporaneamente per recuperare i dettagli
saved_games = []
searched_games = []

def generate_slug(title):
    """Genera uno slug dal titolo del gioco (es. 'Cyberpunk 2077' -> 'cyberpunk-2077')"""
    return re.sub(r'[^a-zA-Z0-9]+', '-', title.lower()).strip('-')

def scraping(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9'
    }

    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, 'html.parser')

    giochi_containers = soup.find_all(class_="item")

    giochi = []
    for gioco in giochi_containers:
        titolo = gioco.find(class_="title")
        prezzo = gioco.find(class_="price")
        img_tag = gioco.find("img")
        link = gioco.find("a", href=True)

        if titolo and prezzo:
            titolo_text = titolo.get_text()
            price = prezzo.get_text().replace("€", "").replace(",", ".")
            try:
                prezzo_float = float(price)
            except ValueError:
                prezzo_float = None
            
            if img_tag:
                immagine_url = img_tag.get("data-src") or img_tag.get("src")  # Usa data-src se presente
                if immagine_url.startswith("/"):  # Completa il link se relativo
                    immagine_url = "https://www.instant-gaming.com" + immagine_url
            else:
                immagine_url = "https://via.placeholder.com/150"

            link_url = link['href'] if link and 'href' in link.attrs else "#"
            
            giochi.append({
                "titolo": titolo_text,
                "prezzo": prezzo_float,
                "immagine": immagine_url,
                "link": link_url,
                "slug": generate_slug(titolo_text)  # Aggiunge lo slug
            })
        
    return giochi

def cerca_giochi(query):
    """Effettua la ricerca di giochi su Instant Gaming in base alla query fornita."""
    global searched_games
    searched_games = []  # Reset della lista

    if not query:
        return []
    
    url = f"https://www.instant-gaming.com/it/ricerca/?query={query}"
    
    try:
        searched_games = scraping(url)  # Salviamo i risultati della ricerca
        return searched_games
        
    except Exception as e:
        print(f"Errore durante la ricerca: {e}")
        return [{"titolo": "Errore nel caricamento", "prezzo": None, "immagine": "https://via.placeholder.com/150", "link": "#"}]

def load_trending_games():
    """Carica i giochi di tendenza"""
    global saved_games

    try:
        url = "https://www.instant-gaming.com/it/?utm_source=google&utm_medium=cpc&utm_campaign=1063495812&utm_content=52470996152&utm_term=instant-gaming&gad_source=1&gclid=Cj0KCQjw16O_BhDNARIsAC3i2GBqET0MaxZu3jx5birZ3yGQmmbgbbEr3OYGJLQs_GMcarD2QntMipoaAivXEALw_wcB"
        saved_games = scraping(url)  # Salviamo i giochi di tendenza
        return saved_games
        
    except Exception as e:
        # Dati di fallback in caso di errore
        trending_games = [
            {"titolo": "Grand Theft Auto V", "prezzo": 19.99, "immagine": "https://via.placeholder.com/150", "link": "#"},
            {"titolo": "Cyberpunk 2077", "prezzo": 29.99, "immagine": "https://via.placeholder.com/150", "link": "#"},
            {"titolo": "Red Dead Redemption 2", "prezzo": 39.99, "immagine": "https://via.placeholder.com/150", "link": "#"},
            {"titolo": "FIFA 24", "prezzo": 49.99, "immagine": "https://via.placeholder.com/150", "link": "#"},
            {"titolo": "Elden Ring", "prezzo": 44.99, "immagine": "https://via.placeholder.com/150", "link": "#"}
        ]
        return trending_games

@app.route('/')
def index():
    global saved_games
    if not saved_games:
        saved_games = load_trending_games()
    return render_template('index.html', games=saved_games, query=None)

@app.route('/search')
def search():
    """Esegue la ricerca e mostra i risultati."""
    global searched_games
    query = request.args.get('q', '').strip()
    if not query:
        return index()
    
    searched_games = cerca_giochi(query)  # Salviamo i risultati della ricerca
    return render_template('index.html', games=searched_games, query=query)

@app.route('/game/<slug>')
def game_details(slug):
    """Mostra i dettagli di un gioco."""
    all_games = saved_games + searched_games  # Unisce entrambe le liste

    for gioco in all_games:
        if gioco["slug"] == slug:
            return render_template('game.html', game=gioco)

    return "Gioco non trovato", 404

if __name__ == '__main__':
    app.run(debug=True)