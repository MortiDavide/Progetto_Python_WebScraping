from flask import Flask, render_template, request
import requests
from bs4 import BeautifulSoup
import re

app = Flask(__name__)

saved_games = []
searched_games = []

def generate_slug(title, platform):
    """Genera uno slug unico dal titolo e dalla piattaforma."""
    base_slug = re.sub(r'[^a-zA-Z0-9]+', '-', title.lower()).strip('-')
    platform_slug = re.sub(r'[^a-zA-Z0-9]+', '-', platform.lower()).strip('-')
    return f"{base_slug}-{platform_slug}"

def extract_platform(game_container):
    """Trova la piattaforma del gioco analizzando tutte le classi nel container."""
    platform_classes = {
        "xbox": "Xbox",
        "playstation": "PlayStation",
    }
    
    # Trova tutti i div all'interno del container
    all_divs = game_container.find_all("div")

    for div in all_divs:
        class_list = div.get("class", [])
        for cls in class_list:
            for key, value in platform_classes.items():
                if key in cls.lower():  # Controlliamo se la classe contiene "xbox" o "playstation"
                    return value
    
    return "PC"  # Se non troviamo nulla, è un gioco per PC

def scraping(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9'
    }

    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, 'html.parser')

    container = soup.find(class_="listing-items")

    giochi_containers = container.find_all(class_="item")

    giochi = []
    for gioco in giochi_containers:
        titolo = gioco.find(class_="title")
        prezzo = gioco.find(class_="price")
        img_tag = gioco.find("img")
        link = gioco.find("a", href=True)

        if titolo and prezzo:
            titolo_text = titolo.get_text()
            platform = extract_platform(gioco)  # Trova la piattaforma

            price = prezzo.get_text().replace("€", "").replace(",", ".")
            try:
                prezzo_float = float(price)
            except ValueError:
                prezzo_float = None
            
            if img_tag:
                immagine_url = img_tag.get("data-src") or img_tag.get("src")
                if immagine_url.startswith("/"):
                    immagine_url = "https://www.instant-gaming.com" + immagine_url
            else:
                immagine_url = "https://via.placeholder.com/150"

            link_url = link['href'] if link and 'href' in link.attrs else "#"
            
            giochi.append({
                "titolo": titolo_text,
                "piattaforma": platform,
                "prezzo": prezzo_float,
                "immagine": immagine_url,
                "link": link_url,
                "slug": generate_slug(titolo_text, platform)
            })
        
    return giochi

def cerca_giochi(query):
    global searched_games
    searched_games = []
    
    if not query:
        return []
    
    url = f"https://www.instant-gaming.com/it/ricerca/?query={query}"
    
    try:
        searched_games = scraping(url)
        return searched_games
    except Exception as e:
        print(f"Errore durante la ricerca: {e}")
        return [{"titolo": "Errore nel caricamento", "piattaforma": "N/A", "prezzo": None, "immagine": "https://via.placeholder.com/150", "link": "#"}]

def load_trending_games():
    global saved_games
    try:
        url = "https://www.instant-gaming.com/it/?utm_source=google&utm_medium=cpc&utm_campaign=1063495812&utm_content=52470996152&utm_term=instant-gaming&gad_source=1&gclid=Cj0KCQjw16O_BhDNARIsAC3i2GBqET0MaxZu3jx5birZ3yGQmmbgbbEr3OYGJLQs_GMcarD2QntMipoaAivXEALw_wcB"
        saved_games = scraping(url)
        return saved_games
    except Exception as e:
        print(f"Errore durante il caricamento dei giochi di tendenza: {e}")
        return []

@app.route('/')
def index():
    global saved_games
    if not saved_games:
        saved_games = load_trending_games()
    return render_template('index.html', games=saved_games, query=None)

@app.route('/search')
def search():
    query = request.args.get('q', '').strip()
    if not query:
        return index()
    
    giochi = cerca_giochi(query)  
    return render_template('index.html', games=giochi, query=query)

@app.route('/game/<slug>')
def game_details(slug):
    all_games = saved_games + searched_games

    for gioco in all_games:
        if gioco["slug"] == slug:
            return render_template('game.html', game=gioco)

    return "Gioco non trovato", 404

if __name__ == '__main__':
    app.run(debug=True)
