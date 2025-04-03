# app.py
from flask import Flask, render_template, request, redirect, url_for, session, flash
import requests
from bs4 import BeautifulSoup
import re
from fuzzywuzzy import fuzz  # Importa fuzzywuzzy
import time
import csv
import plotly.express as px

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

def IG_scraping(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9'
    }

    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, 'html.parser')

    container = soup.find(class_="listing-items")

    giochi_containers = container.find_all(class_="item")

    giochi = []
    for gioco in giochi_containers[:15]:
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
                "sito": "Instant Gaming",
                "slug": generate_slug(titolo_text, platform)
            })
        
    return giochi

def Steam_scraping(url, query, limite):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9'
    }

    try:
        # Invia la richiesta GET a Steam
        res = requests.get(url, headers=headers)
        
        # Analizza la risposta utilizzando BeautifulSoup
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # Cicla attraverso i link dei risultati di gioco
        game_links = soup.find_all('a', class_='search_result_row')
        
        giochi = []
        
        for link in game_links[:limite]:
            try:
                # Estrai il titolo del gioco
                title_element = link.find('span', class_='title')
                if not title_element:
                    continue  # Salta questo gioco se non ha un titolo
                
                title = title_element.text
                
                # Usa il fuzzy matching per verificare se la query è abbastanza simile al titolo
                similarity = fuzz.partial_ratio(query.lower(), title.lower())
                if similarity < 80:  # Accetta solo corrispondenze con almeno l'80% di similarità
                    continue
                
                # Estrai l'app_id con gestione degli errori
                href = link.get("href", "")
                if "/app/" not in href:
                    continue  # Salta questo gioco se non ha un app_id
                
                try:
                    app_id = href.split("/app/")[1].split("/")[0]
                except IndexError:
                    continue  # Salta questo gioco se non può estrarre l'app_id
                
                # Estrai il prezzo
                price_tag = link.find('div', class_='discount_final_price')
                if not price_tag:
                    continue  # Salta questo gioco se non ha un prezzo
                
                price = price_tag.text.strip()
                
                # Salta i giochi gratuiti (prezzo uguale a "Free")
                if "Free" in price:
                    continue
                
                # Converti il prezzo in numero
                cleaned_price = re.sub(r"[^\d,\.]", "", price)
                cleaned_price = cleaned_price.replace(",", ".")  # Steam usa la virgola come decimale
                
                try:
                    prezzo_float = float(cleaned_price)
                except ValueError:
                    prezzo_float = None
                
                # Vai alla pagina del gioco per ottenere più dettagli
                try:
                    game_url = f"https://store.steampowered.com/app/{app_id}/"
                    game_res = requests.get(game_url, headers=headers)
                    game_soup = BeautifulSoup(game_res.text, 'html.parser')
                    
                    # Estrai la descrizione
                    description = game_soup.find('div', class_='game_description_snippet')
                    description = description.text.strip() if description else 'Descrizione non disponibile'
                    
                    # Estrai la data di rilascio
                    release_date = game_soup.find('div', class_='date')
                    release_date = release_date.text.strip() if release_date else 'Data di rilascio non disponibile'
                    
                    # Estrai i generi
                    genres = []
                    genre_section = game_soup.find('div', class_='glance_tags')
                    if genre_section:
                        genre_tags = genre_section.find_all('a')
                        for genre in genre_tags:
                            genre_text = genre.text.strip()
                            if genre_text:
                                genres.append(genre_text)
                    
                    if not genres:
                        genres = ['Nessun genere disponibile']
                    
                    genres_str = ' - '.join(genres)
                    
                    # Estrai l'editore
                    publisher = 'Editore non disponibile'
                    publisher_section = game_soup.find('div', class_='dev_row')
                    if publisher_section:
                        publisher_links = publisher_section.find_all('a')
                        if len(publisher_links) > 1:
                            publisher = publisher_links[1].text.strip()
                    
                    # Estrai l'URL dell'immagine
                    image_url = None
                    image_tag = game_soup.find('img', class_='game_header_image_full')
                    if image_tag:
                        image_url = image_tag.get('src', '')
                    
                    if not image_url:
                        image_tag = game_soup.find('meta', property='og:image')
                        if image_tag:
                            image_url = image_tag.get('content', '')
                    
                    if not image_url:
                        image_url = 'https://via.placeholder.com/150'
                    
                    platform = "PC"
                    
                    giochi.append({
                        "titolo": title,
                        "piattaforma": platform,
                        "prezzo": prezzo_float,
                        "immagine": image_url,
                        "link": game_url,
                        "data-rilascio": release_date,
                        "descrizione": description,
                        "generi": genres_str,
                        "autore": publisher,
                        "sito": "Steam",
                        "slug": generate_slug(title, platform)
                    })
                    
                except Exception as e:
                    print(f"Errore nell'elaborazione della pagina del gioco {app_id}: {e}")
                    continue
                    
            except Exception as e:
                print(f"Errore nell'elaborazione di un risultato di gioco: {e}")
                continue
        
        return giochi
        
    except Exception as e:
        print(f"Errore durante lo scraping di Steam: {e}")
        return []

def confronta_prezzi(giochi_steam, giochi_ig):
    giochi_migliori = {}
    
    # Prima aggiungiamo tutti i giochi PC da Instant Gaming
    for gioco in giochi_ig:
        titolo = gioco["titolo"]
        piattaforma = gioco["piattaforma"].lower()
        prezzo_ig = gioco["prezzo"]
        
        # Crea una chiave univoca per ogni gioco combinando titolo e piattaforma
        chiave = f"{titolo}_{piattaforma}"
        
        # Aggiungi solo i giochi PC o per altre piattaforme
        giochi_migliori[chiave] = {
            "titolo": titolo,
            "piattaforma": piattaforma,
            "prezzo": prezzo_ig,
            "prezzo_steam": None,  # Ancora da definire
            "prezzo_ig": prezzo_ig,
            "immagine": gioco["immagine"],
            "link": gioco["link"],
            "descrizione": gioco.get("descrizione", "Nessuna descrizione disponibile"),
            "sito": "Instant Gaming",
            "slug": gioco["slug"]
        }
    
    # Poi confrontiamo con i giochi di Steam (solo PC)
    for gioco_steam in giochi_steam:
        titolo_steam = gioco_steam["titolo"]
        prezzo_steam = gioco_steam["prezzo"]
        
        # Verifica se esiste un gioco simile da IG per PC
        miglior_match = None
        miglior_punteggio = 0
        
        for chiave, gioco_ig in giochi_migliori.items():
            if gioco_ig["piattaforma"].lower() == "pc":
                # Usa fuzzy matching per confrontare i titoli
                punteggio = fuzz.ratio(titolo_steam.lower(), gioco_ig["titolo"].lower())
                if punteggio > miglior_punteggio and punteggio >= 80:  # Soglia di similarità
                    miglior_punteggio = punteggio
                    miglior_match = chiave
        
        if miglior_match:
            # Abbiamo trovato un gioco simile su IG, confrontiamo i prezzi
            giochi_migliori[miglior_match]["prezzo_steam"] = prezzo_steam
            
            # Confronta i prezzi e scegli il più basso
            if prezzo_steam is not None and (giochi_migliori[miglior_match]["prezzo_ig"] is None 
                                           or prezzo_steam < giochi_migliori[miglior_match]["prezzo_ig"]):
                giochi_migliori[miglior_match]["prezzo"] = prezzo_steam
                giochi_migliori[miglior_match]["sito"] = "Steam"
                giochi_migliori[miglior_match]["link"] = gioco_steam["link"]
        else:
            # Non abbiamo trovato un gioco simile su IG, aggiungiamo il gioco Steam
            chiave = f"{titolo_steam}_pc"
            giochi_migliori[chiave] = {
                "titolo": titolo_steam,
                "piattaforma": "pc",
                "prezzo": prezzo_steam,
                "prezzo_steam": prezzo_steam,
                "prezzo_ig": None,  # Non disponibile
                "immagine": gioco_steam["immagine"],
                "link": gioco_steam["link"],
                "descrizione": gioco_steam.get("descrizione", "Nessuna descrizione disponibile"),
                "sito": "Steam",
                "slug": gioco_steam["slug"]
            }
    
    # Converte il dizionario in una lista
    return list(giochi_migliori.values())

def cerca_giochi(query):
    global searched_games
    searched_games = []
    
    if not query:
        return []
    
    IG_url = f"https://www.instant-gaming.com/it/ricerca/?query={query}"
    Steam_url = f"https://store.steampowered.com/search/?term={query}"
    
    try:
        ig_games = IG_scraping(IG_url)   # Giochi da Instant Gaming
        print(f"Trovati {len(ig_games)} giochi su Instant Gaming")
    except Exception as e:
        print(f"Errore durante lo scraping di Instant Gaming: {e}")
        ig_games = []
    
    try:
        steam_games = Steam_scraping(Steam_url, query, 15)  # Giochi da Steam
        print(f"Trovati {len(steam_games)} giochi su Steam")
    except Exception as e:
        print(f"Errore durante lo scraping di Steam: {e}")
        steam_games = []
    
    if not ig_games and not steam_games:
        return [{"titolo": "No games available", "piattaforma": "N/A", "prezzo": None, "immagine": "https://via.placeholder.com/150", "link": "#", "slug": "no-results"}]
    
    searched_games = confronta_prezzi(steam_games, ig_games)  # Unisce i risultati
    
    # Filtra giochi senza prezzo valido
    searched_games = [game for game in searched_games if game['prezzo'] is not None]
    
    if not searched_games:
        return [{"titolo": "No games available", "piattaforma": "N/A", "prezzo": None, "immagine": "https://via.placeholder.com/150", "link": "#", "slug": "no-results"}]
    
    return searched_games




def load_trending_games():
    global saved_games
    try:
        # Carica i giochi di tendenza da Instant Gaming
        IG_url = "https://www.instant-gaming.com/it/"
        ig_games = IG_scraping(IG_url)
        
        # Filtra solo i giochi PC
        pc_games = [game for game in ig_games if game["piattaforma"].lower() == "pc"]
        
        # Estrai i titoli dei giochi PC
        titoli_pc = [game["titolo"] for game in pc_games]
        
        # Crea una ricerca combinata per Steam (primi 5 giochi per evitare ricerche troppo ampie)
        # Steam ha limiti su quanto può essere lunga una query di ricerca
        steam_games = []
        for titolo in titoli_pc[:10]:  # Limita a 10 giochi per evitare problemi
            try:
                Steam_url = f"https://store.steampowered.com/search/?term={titolo}"
                risultati = Steam_scraping(Steam_url, titolo, 1)
                steam_games.extend(risultati)
                # Aggiungi un piccolo ritardo per evitare di sovraccaricare Steam
                time.sleep(0.5)
            except Exception as e:
                print(f"Errore durante la ricerca su Steam per {titolo}: {e}")
        
        # Confronta i prezzi e ottieni i migliori
        saved_games = confronta_prezzi(steam_games, ig_games)
        return saved_games
    except Exception as e:
        print(f"Errore durante il caricamento dei giochi di tendenza: {e}")
        return []


@app.route('/')
def index():
    global saved_games
    if not saved_games:
        saved_games = load_trending_games()
    
    query = request.args.get('q', '').strip()  # If no query, use an empty string
    games = saved_games  # Default to trending games if no query is provided
    
    # If there is a query, we filter games based on the search term
    if query:
        games = cerca_giochi(query)  # This should return a list of games matching the query
    
    # Initialize the graph_html as an empty string
    graph_html = ""
    
    # Create the graph only if there are games and we have valid data
    if games and any(
    (game.get('prezzo_steam') is not None and game['prezzo_steam'] > 0) or
    (game.get('prezzo_ig') is not None and game['prezzo_ig'] > 0)
    for game in games
        ):

        # Prepare data for the plotly graph
        titles = [game.get('titolo', 'Unknown') for game in games]  # Extract titles (x-axis)
        prezzi_steam = [game.get('prezzo_steam', 0) for game in games]  # Extract Steam prices (y-axis for Steam)
        prezzi_ig = [game.get('prezzo_ig', 0) for game in games]  # Extract Instant Gaming prices (y-axis for IG)

        # Plot the graph
        fig = px.bar(
            games, 
            x='titolo', 
            y=['prezzo_steam', 'prezzo_ig'], 
            title='Confronto Prezzi Steam vs Instant Gaming', 
            labels={'value':'prezzo'},
            barmode='group'
        )

        # Update the layout
        fig.update_layout(
            paper_bgcolor="#263246",  # Darker background color
            font=dict(color="white")  # Set the text color to white
        )

        graph_html = fig.to_html(full_html=False)
    
    # Pass the games and the graph to the template (if there are games)
    return render_template('index.html', games=games, query=query, graph_html=graph_html)



@app.route('/search')
def search():
    query = request.args.get('q', '').strip()
    
    if not query:
        return index()  # If no query, return trending games
    
    # Get the search results
    searched_games = cerca_giochi(query)  # Assuming this function returns search results
    
    # Initialize an empty graph_html variable
    graph_html = ""
    
    # Check if no games are found or if the "No games available" message is returned
    if searched_games and searched_games[0]["titolo"] == "No games available":
        return render_template('index.html', games=searched_games, query=query, graph_html=graph_html, no_results=True)
    
    # If there are games, and we should create a graph
    if searched_games:  
        valid_games = [game for game in searched_games if game['prezzo_steam'] and game['prezzo_ig']]  # Filter games with valid prices
        if valid_games:  # Only generate graph if there are valid games
            fig = px.bar(
                valid_games, 
                x='titolo', 
                y=['prezzo_steam', 'prezzo_ig'], 
                title=f'Confronto Prezzi per: {query}', 
                labels={'prezzo_steam': 'Prezzo Steam (€)', 'prezzo_ig': 'Prezzo Instant Gaming (€)'},
                barmode='group'
            )
            graph_html = fig.to_html(full_html=False)

    return render_template('index.html', games=searched_games, query=query, graph_html=graph_html)







@app.route('/game/<slug>')
def game_details(slug):
    # Combine saved and searched games
    all_games = saved_games + searched_games  # Assuming 'searched_games' holds your search results
    
    gioco_selezionato = None
    prezzo_steam = "Non disponibile"
    prezzo_ig = "Non disponibile"

    # Search for the game with the given slug
    for gioco in all_games:
        if gioco["slug"] == slug:
            gioco_selezionato = gioco  # Set the selected game
            # Get price info for Steam and Instant Gaming
            if "steam" in gioco["link"]:
                prezzo_steam = f"{gioco['prezzo']}€" if gioco["prezzo"] else "Non disponibile"
            else:
                prezzo_ig = f"{gioco['prezzo']}€" if gioco["prezzo"] else "Non disponibile"
            break  # Once we find the game, we can break the loop
    
    if gioco_selezionato:
        return render_template('game.html', game=gioco_selezionato, prezzo_steam=prezzo_steam, prezzo_ig=prezzo_ig)
    
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