# Business_logic.py
import requests
from bs4 import BeautifulSoup
import re
from fuzzywuzzy import fuzz
import time
import plotly.express as px
from Persistenza import (
    load_users as load_users_from_db, 
    save_user as save_user_to_db, 
    load_wishlist as load_wishlist_from_db, 
    save_wishlist as save_wishlist_to_db, 
    remove_from_wishlist as remove_from_wishlist_db
)

# Variabili globali
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

def create_price_comparison_graph(games, query=None):
    if not games:
        return ""
    
    title = f'Confronto Prezzi per: {query}' if query else 'Confronto Prezzi Steam vs Instant Gaming'
    
    fig = px.bar(
        games, 
        x='titolo', 
        y=['prezzo_steam', 'prezzo_ig'], 
        title=title, 
        labels={'prezzo_steam': 'Prezzo Steam (€)', 'prezzo_ig': 'Prezzo Instant Gaming (€)'},
        barmode='group'
    )
    
    fig.update_layout(
        paper_bgcolor="#263246",  # Darker background color
        font=dict(
            color="white"  # Set the text color to white
        )
    )
    
    return fig.to_html(full_html=False)

def get_game_by_slug(slug):
    # Combina giochi salvati e cercati
    all_games = saved_games + searched_games
    
    gioco_selezionato = None
    prezzo_steam = "Non disponibile"
    prezzo_ig = "Non disponibile"

    # Cerca il gioco con lo slug specificato
    for gioco in all_games:
        if gioco["slug"] == slug:
            gioco_selezionato = gioco
            # Ottieni le informazioni sui prezzi per Steam e Instant Gaming
            if "steam" in gioco["link"]:
                prezzo_steam = f"{gioco['prezzo']}€" if gioco["prezzo"] else "Non disponibile"
            else:
                prezzo_ig = f"{gioco['prezzo']}€" if gioco["prezzo"] else "Non disponibile"
            break
    
    return gioco_selezionato, prezzo_steam, prezzo_ig

# Funzioni che ora fanno da intermediario tra l'interfaccia e la persistenza

def load_wishlist_games():
    """Carica la wishlist tramite il livello di persistenza"""
    return load_wishlist_from_db()

def add_game_to_wishlist(slug):
    """Aggiunge un gioco alla wishlist"""
    # Combina giochi salvati e cercati
    all_games = saved_games + searched_games
    
    # Verifica se il gioco è già nella wishlist
    wishlist_games = load_wishlist_from_db()
    for game in wishlist_games:
        if game["slug"] == slug:
            return False
    
    # Trova il gioco con lo slug specificato
    for gioco in all_games:
        if gioco["slug"] == slug:
            # Salva nella wishlist tramite il livello di persistenza
            save_wishlist_to_db(
                gioco.get("id", ""),
                gioco["titolo"],
                gioco["piattaforma"],
                gioco["prezzo"],
                gioco["immagine"],
                gioco["link"],
                gioco["sito"],
                gioco["slug"]
            )
            return True
    
    return False

def remove_game_from_wishlist(slug):
    """Rimuove un gioco dalla wishlist tramite il livello di persistenza"""
    return remove_from_wishlist_db(slug)

def authenticate_user(username, password):
    """Autentica un utente tramite il livello di persistenza"""
    users = load_users_from_db()
    for user in users:
        if user["username"] == username and user["password"] == password:
            return user
    return None

def register_user(username, password):
    """Registra un nuovo utente tramite il livello di persistenza"""
    users = load_users_from_db()
    
    # Verifica se l'username esiste già
    for user in users:
        if user["username"] == username:
            return False, "Username già esistente!"
    
    # Salva il nuovo utente
    save_user_to_db(username, password)
    return True, "Registrazione avvenuta con successo!"