# app.py
from flask import Flask, render_template, request
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

def cerca_giochi(query):
    """
    Effettua la ricerca di giochi su instant-gaming in base alla query fornita
    """
    if not query:
        return []
        
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9'
    }
    
    url = f"https://www.instant-gaming.com/it/ricerca/?query={query}"
    
    try:
        res = requests.get(url, headers=headers)
        soup = BeautifulSoup(res.text, 'html.parser')

        giochi_containers = soup.find_all(class_="item")

        giochi = []
        for gioco in giochi_containers:
            titolo = gioco.find(class_="title")
            prezzo = gioco.find(class_="price")
            immagine = gioco.find("img")
            link = gioco.find("a", href=True)

            if titolo and prezzo:
                titolo_text = titolo.get_text()
                price = prezzo.get_text().replace("€", "").replace(",", ".")
                try:
                    prezzo_float = float(price)
                except ValueError:
                    prezzo_float = None
                
                immagine_url = immagine['src'] if immagine and 'src' in immagine.attrs else "https://via.placeholder.com/150"
                link_url = link['href'] if link and 'href' in link.attrs else "#"
                
                giochi.append({
                    "titolo": titolo_text,
                    "prezzo": prezzo_float,
                    "immagine": immagine_url,
                    "link": link_url
                })
            
        return giochi
        
    except Exception as e:
        print(f"Errore durante la ricerca: {e}")
        return []

def load_trending_games():
    """Carica i giochi di tendenza"""
    try:
        # Effettua scraping della homepage di Instant Gaming per trovare i giochi di tendenza
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9'
        }
        
        # URL della pagina dei bestseller
        url = "https://www.instant-gaming.com/it/bestseller/"
        
        res = requests.get(url, headers=headers)
        soup = BeautifulSoup(res.text, 'html.parser')

        giochi_containers = soup.find_all(class_="item")[:15]  # Prendiamo i primi 15 giochi

        trending_games = []
        for gioco in giochi_containers:
            titolo = gioco.find(class_="title")
            prezzo = gioco.find(class_="price")
            immagine = gioco.find("img")
            link = gioco.find("a", href=True)

            if titolo and prezzo:
                titolo_text = titolo.get_text()
                price = prezzo.get_text().replace("€", "").replace(",", ".")
                try:
                    prezzo_float = float(price)
                except ValueError:
                    prezzo_float = None
                
                immagine_url = immagine['src'] if immagine and 'src' in immagine.attrs else "https://via.placeholder.com/150"
                link_url = link['href'] if link and 'href' in link.attrs else "#"
                
                trending_games.append({
                    "titolo": titolo_text,
                    "prezzo": prezzo_float,
                    "immagine": immagine_url,
                    "link": link_url
                })
        
        return trending_games
        
    except Exception as e:
        print(f"Errore durante il caricamento dei giochi di tendenza: {e}")
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
    trending_games = load_trending_games()
    return render_template('index.html', games=trending_games, query=None)

@app.route('/search')
def search():
    query = request.args.get('q', '').strip()
    if not query:
        return index()
    
    giochi = cerca_giochi(query)
    return render_template('index.html', games=giochi, query=query)

if __name__ == '__main__':
    app.run(debug=True)