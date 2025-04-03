# persistence/game_repository.py
import requests
from bs4 import BeautifulSoup
import re
from fuzzywuzzy import fuzz
import time

class GameRepository:
    def __init__(self):
        pass
    
    def search_games(self, query):
        """Search for games across multiple platforms"""
        if not query:
            return []
        
        IG_url = f"https://www.instant-gaming.com/it/ricerca/?query={query}"
        Steam_url = f"https://store.steampowered.com/search/?term={query}"
        
        try:
            ig_games = self._scrape_instant_gaming(IG_url)
            print(f"Trovati {len(ig_games)} giochi su Instant Gaming")
        except Exception as e:
            print(f"Errore durante lo scraping di Instant Gaming: {e}")
            ig_games = []
        
        try:
            steam_games = self._scrape_steam(Steam_url, query, 15)
            print(f"Trovati {len(steam_games)} giochi su Steam")
        except Exception as e:
            print(f"Errore durante lo scraping di Steam: {e}")
            steam_games = []
        
        if not ig_games and not steam_games:
            return [{"titolo": "Nessun risultato trovato", "piattaforma": "N/A", "prezzo": None, "immagine": "https://via.placeholder.com/150", "link": "#", "slug": "no-results"}]
        
        # Compare prices and combine results
        combined_games = self._compare_prices(steam_games, ig_games)
        
        # Filter games without valid prices
        combined_games = [game for game in combined_games if game['prezzo'] is not None]
        
        if not combined_games:
            return [{"titolo": "No games available", "piattaforma": "N/A", "prezzo": None, "immagine": "https://via.placeholder.com/150", "link": "#", "slug": "no-results"}]
        
        return combined_games
    
    def load_trending_games(self):
        """Load trending games from platforms"""
        try:
            # Load trending games from Instant Gaming
            IG_url = "https://www.instant-gaming.com/it/"
            ig_games = self._scrape_instant_gaming(IG_url)
            
            # Filter only PC games
            pc_games = [game for game in ig_games if game["piattaforma"].lower() == "pc"]
            
            # Extract PC game titles
            titoli_pc = [game["titolo"] for game in pc_games]
            
            # Search for these games on Steam (limited to first 10)
            steam_games = []
            for titolo in titoli_pc[:10]:
                try:
                    Steam_url = f"https://store.steampowered.com/search/?term={titolo}"
                    risultati = self._scrape_steam(Steam_url, titolo, 1)
                    steam_games.extend(risultati)
                    # Add a small delay to avoid overloading Steam
                    time.sleep(0.5)
                except Exception as e:
                    print(f"Errore durante la ricerca su Steam per {titolo}: {e}")
            
            # Compare prices and get the best deals
            trending_games = self._compare_prices(steam_games, ig_games)
            return trending_games
        except Exception as e:
            print(f"Errore durante il caricamento dei giochi di tendenza: {e}")
            return []
    
    def _scrape_instant_gaming(self, url):
        """Scrape games from Instant Gaming"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9'
        }

        res = requests.get(url, headers=headers)
        soup = BeautifulSoup(res.text, 'html.parser')

        container = soup.find(class_="listing-items")
        if not container:
            return []

        giochi_containers = container.find_all(class_="item")

        giochi = []
        for gioco in giochi_containers[:15]:
            titolo = gioco.find(class_="title")
            prezzo = gioco.find(class_="price")
            img_tag = gioco.find("img")
            link = gioco.find("a", href=True)

            if titolo and prezzo:
                titolo_text = titolo.get_text()
                platform = self._extract_platform(gioco)

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
                    "slug": self._generate_slug(titolo_text, platform)
                })
            
        return giochi
    
    def _scrape_steam(self, url, query, limite):
        """Scrape games from Steam"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9'
        }

        try:
            # Send a GET request to Steam
            res = requests.get(url, headers=headers)
            
            # Parse the response using BeautifulSoup
            soup = BeautifulSoup(res.text, 'html.parser')
            
            # Find all game result links
            game_links = soup.find_all('a', class_='search_result_row')
            
            giochi = []
            
            for link in game_links[:limite]:
                try:
                    # Extract game title
                    title_element = link.find('span', class_='title')
                    if not title_element:
                        continue  # Skip this game if no title
                    
                    title = title_element.text
                    
                    # Use fuzzy matching to check if query is similar enough to title
                    similarity = fuzz.partial_ratio(query.lower(), title.lower())
                    if similarity < 80:  # Accept only matches with at least 80% similarity
                        continue
                    
                    # Extract app_id with error handling
                    href = link.get("href", "")
                    if "/app/" not in href:
                        continue  # Skip this game if no app_id
                    
                    try:
                        app_id = href.split("/app/")[1].split("/")[0]
                    except IndexError:
                        continue  # Skip this game if can't extract app_id
                    
                    # Extract price
                    price_tag = link.find('div', class_='discount_final_price')
                    if not price_tag:
                        continue  # Skip this game if no price
                    
                    price = price_tag.text.strip()
                    
                    # Skip free games
                    if "Free" in price:
                        continue
                    
                    # Convert price to number
                    cleaned_price = re.sub(r"[^\d,\.]", "", price)
                    cleaned_price = cleaned_price.replace(",", ".")  # Steam uses comma as decimal
                    
                    try:
                        prezzo_float = float(cleaned_price)
                    except ValueError:
                        prezzo_float = None
                    
                    # Get more details from the game page
                    try:
                        game_url = f"https://store.steampowered.com/app/{app_id}/"
                        game_res = requests.get(game_url, headers=headers)
                        game_soup = BeautifulSoup(game_res.text, 'html.parser')
                        
                        # Extract description
                        description = game_soup.find('div', class_='game_description_snippet')
                        description = description.text.strip() if description else 'Descrizione non disponibile'
                        
                        # Extract release date
                        release_date = game_soup.find('div', class_='date')
                        release_date = release_date.text.strip() if release_date else 'Data di rilascio non disponibile'
                        
                        # Extract genres
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
                        
                        # Extract publisher
                        publisher = 'Editore non disponibile'
                        publisher_section = game_soup.find('div', class_='dev_row')
                        if publisher_section:
                            publisher_links = publisher_section.find_all('a')
                            if len(publisher_links) > 1:
                                publisher = publisher_links[1].text.strip()
                        
                        # Extract image URL
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
                            "slug": self._generate_slug(title, platform)
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
    
    def _compare_prices(self, giochi_steam, giochi_ig):
        """Compare prices between Steam and Instant Gaming"""
        giochi_migliori = {}
        
        # First add all games from Instant Gaming
        for gioco in giochi_ig:
            titolo = gioco["titolo"]
            piattaforma = gioco["piattaforma"].lower()
            prezzo_ig = gioco["prezzo"]
            
            # Create a unique key for each game combining title and platform
            chiave = f"{titolo}_{piattaforma}"
            
            # Add only the PC games or for other platforms
            giochi_migliori[chiave] = {
                "titolo": titolo,
                "piattaforma": piattaforma,
                "prezzo": prezzo_ig,
                "prezzo_steam": None,  # To be defined
                "prezzo_ig": prezzo_ig,
                "immagine": gioco["immagine"],
                "link": gioco["link"],
                "descrizione": gioco.get("descrizione", "Nessuna descrizione disponibile"),
                "sito": "Instant Gaming",
                "slug": gioco["slug"]
            }
        
        # Then compare with Steam games (PC only)
        for gioco_steam in giochi_steam:
            titolo_steam = gioco_steam["titolo"]
            prezzo_steam = gioco_steam["prezzo"]
            
            # Check if there's a similar game from IG for PC
            miglior_match = None
            miglior_punteggio = 0
            
            for chiave, gioco_ig in giochi_migliori.items():
                if gioco_ig["piattaforma"].lower() == "pc":
                    # Use fuzzy matching to compare titles
                    punteggio = fuzz.ratio(titolo_steam.lower(), gioco_ig["titolo"].lower())
                    if punteggio > miglior_punteggio and punteggio >= 80:  # Similarity threshold
                        miglior_punteggio = punteggio
                        miglior_match = chiave
            
            if miglior_match:
                # We found a similar game on IG, compare prices
                giochi_migliori[miglior_match]["prezzo_steam"] = prezzo_steam
                
                # Compare prices and choose the lowest
                if prezzo_steam is not None and (giochi_migliori[miglior_match]["prezzo_ig"] is None 
                                               or prezzo_steam < giochi_migliori[miglior_match]["prezzo_ig"]):
                    giochi_migliori[miglior_match]["prezzo"] = prezzo_steam
                    giochi_migliori[miglior_match]["sito"] = "Steam"
                    giochi_migliori[miglior_match]["link"] = gioco_steam["link"]
            else:
                # We didn't find a similar game on IG, add the Steam game
                chiave = f"{titolo_steam}_pc"
                giochi_migliori[chiave] = {
                    "titolo": titolo_steam,
                    "piattaforma": "pc",
                    "prezzo": prezzo_steam,
                    "prezzo_steam": prezzo_steam,
                    "prezzo_ig": None,  # Not available
                    "immagine": gioco_steam["immagine"],
                    "link": gioco_steam["link"],
                    "descrizione": gioco_steam.get("descrizione", "Nessuna descrizione disponibile"),
                    "sito": "Steam",
                    "slug": gioco_steam["slug"]
                }
        
        # Convert dictionary to list
        return list(giochi_migliori.values())
    
    def _extract_platform(self, game_container):
        """Find the platform of the game by analyzing all classes in the container"""
        platform_classes = {
            "xbox": "Xbox",
            "playstation": "PlayStation",
        }
        
        # Find all divs in the container
        all_divs = game_container.find_all("div")

        for div in all_divs:
            class_list = div.get("class", [])
            for cls in class_list:
                for key, value in platform_classes.items():
                    if key in cls.lower():  # Check if the class contains "xbox" or "playstation"
                        return value
        
        return "PC"  # If we don't find anything, it's a PC game
    
    def _generate_slug(self, title, platform):
        """Generate a unique slug from title and platform"""
        base_slug = re.sub(r'[^a-zA-Z0-9]+', '-', title.lower()).strip('-')
        platform_slug = re.sub(r'[^a-zA-Z0-9]+', '-', platform.lower()).strip('-')
        return f"{base_slug}-{platform_slug}"