from flask import Flask, render_template, request, redirect, url_for, session, flash
import requests
from bs4 import BeautifulSoup
import re
import csv

app = Flask(__name__)
app.secret_key = 'supersecretkey'

saved_games = []
searched_games = []
users_file = 'users.csv'

# Funzione per leggere gli utenti dal CSV
def load_users():
    users = {}
    try:
        with open(users_file, newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                if len(row) == 2:
                    users[row[0]] = row[1]
    except FileNotFoundError:
        pass
    return users

# Funzione per salvare un nuovo utente nel CSV
def save_user(username, password):
    with open(users_file, 'a', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([username, password])

users = load_users()

def generate_slug(title, platform):
    base_slug = re.sub(r'[^a-zA-Z0-9]+', '-', title.lower()).strip('-')
    platform_slug = re.sub(r'[^a-zA-Z0-9]+', '-', platform.lower()).strip('-')
    return f"{base_slug}-{platform_slug}"

def extract_platform(game_container):
    platform_classes = {"xbox": "Xbox", "playstation": "PlayStation"}
    all_divs = game_container.find_all("div")
    for div in all_divs:
        class_list = div.get("class", [])
        for cls in class_list:
            for key, value in platform_classes.items():
                if key in cls.lower():
                    return value
    return "PC"

def scraping(url):
    headers = {'User-Agent': 'Mozilla/5.0', 'Accept-Language': 'en-US,en;q=0.9'}
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
            platform = extract_platform(gioco)
            price = prezzo.get_text().replace("€", "").replace(",", ".")
            try:
                prezzo_float = float(price)
            except ValueError:
                prezzo_float = None
            immagine_url = img_tag.get("data-src") or img_tag.get("src") if img_tag else "https://via.placeholder.com/150"
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
        return []

def load_trending_games():
    global saved_games
    try:
        url = "https://www.instant-gaming.com/it/"
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

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        users = load_users()
        if username in users and users[username] == password:
            session['user_id'] = username
            session['username'] = username
            flash('Login avvenuto con successo!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Credenziali non valide.', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        users = load_users()
        if username in users:
            flash('Username già esistente!', 'warning')
        else:
            save_user(username, password)
            flash('Registrazione avvenuta con successo! Ora puoi accedere.', 'success')
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    flash("Sei uscito dall'account.", 'info')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)