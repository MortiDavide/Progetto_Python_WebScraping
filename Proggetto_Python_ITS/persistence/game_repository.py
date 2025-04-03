# persistence/game_repository.py
import requests
from bs4 import BeautifulSoup
import re
from fuzzywuzzy import fuzz
import time
import urllib.parse

class GameRepository:
    def __init__(self):
        self.steam_cache = {}  # Cache Steam search results
    
    def search_games(self, query):
        """Search for games across multiple platforms"""
        if not query:
            return []
        
        IG_url = f"https://www.instant-gaming.com/it/ricerca/?query={query}"
        
        try:
            ig_games = self._scrape_instant_gaming(IG_url)
            print(f"Trovati {len(ig_games)} giochi su Instant Gaming")
        except Exception as e:
            print(f"Errore durante lo scraping di Instant Gaming: {e}")
            ig_games = []
        
        # For each Instant Gaming game, try to find a matching Steam game
        steam_games = []
        for ig_game in ig_games:
            if ig_game["piattaforma"].lower() == "pc":
                try:
                    # Use the exact game title for better matching
                    game_title = ig_game["titolo"]
                    
                    # Remove any platform or edition information from the title
                    clean_title = re.sub(r'\s*(\(PC\)|\(Steam\)|\(Epic\)|\- \w+ Edition).*$', '', game_title)
                    
                    # Try to find the game on Steam
                    Steam_url = f"https://store.steampowered.com/search/?term={urllib.parse.quote(clean_title)}"
                    steam_result = self._find_exact_game_on_steam(Steam_url, clean_title)
                    
                    if steam_result:
                        steam_games.append(steam_result)
                    
                    # Small delay to avoid rate limiting
                    time.sleep(0.2)
                except Exception as e:
                    print(f"Errore durante la ricerca su Steam per {ig_game['titolo']}: {e}")
        
        print(f"Trovati {len(steam_games)} giochi su Steam")
        
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
            
            # For each trending PC game, try to find it on Steam
            steam_games = []
            for pc_game in pc_games:
                try:
                    # Clean up the title for better matching
                    game_title = pc_game["titolo"]
                    clean_title = re.sub(r'\s*(\(PC\)|\(Steam\)|\(Epic\)|\- \w+ Edition).*$', '', game_title)
                    
                    # Search on Steam
                    Steam_url = f"https://store.steampowered.com/search/?term={urllib.parse.quote(clean_title)}"
                    steam_result = self._find_exact_game_on_steam(Steam_url, clean_title)
                    
                    if steam_result:
                        steam_games.append(steam_result)
                    
                    # Add a small delay to avoid overloading Steam
                    time.sleep(0.2)
                except Exception as e:
                    print(f"Errore durante la ricerca su Steam per {pc_game['titolo']}: {e}")
            
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
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.instant-gaming.com/'
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
                titolo_text = titolo.get_text().strip()
                platform = self._extract_platform(gioco)

                price = prezzo.get_text().replace("€", "").replace(",", ".")
                try:
                    prezzo_float = float(price)
                except ValueError:
                    prezzo_float = None
                
                if img_tag:
                    immagine_url = img_tag.get("data-src") or img_tag.get("src")
                    if immagine_url and immagine_url.startswith("/"):
                        immagine_url = "https://www.instant-gaming.com" + immagine_url
                else:
                    immagine_url = "https://via.placeholder.com/150"

                link_url = link['href'] if link and 'href' in link.attrs else "#"
                
                # Clean up the title for better comparison with Steam
                clean_title = re.sub(r'\s*(\(PC\)|\(Steam\)|\(Epic\)|\- \w+ Edition).*$', '', titolo_text)
                
                giochi.append({
                    "titolo": titolo_text,
                    "titolo_clean": clean_title,  # Store clean title for better matching
                    "piattaforma": platform,
                    "prezzo": prezzo_float,
                    "immagine": immagine_url,
                    "link": link_url,
                    "sito": "Instant Gaming",
                    "slug": self._generate_slug(titolo_text, platform)
                })
            
        return giochi
    
    def _find_exact_game_on_steam(self, url, title):
        """Find a specific game on Steam by title"""
        # First check if we've already searched for this title
        if title in self.steam_cache:
            return self.steam_cache[title]
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Cookie': 'birthtime=536457201; mature_content=1;'  # Set age verification cookie
        }

        try:
            res = requests.get(url, headers=headers)
            soup = BeautifulSoup(res.text, 'html.parser')
            
            # Find all game result links
            game_links = soup.find_all('a', class_='search_result_row')
            
            best_match = None
            best_score = 0
            
            for link in game_links[:5]:  # Only check top 5 results
                game_title_element = link.find('span', class_='title')
                if not game_title_element:
                    continue
                
                game_title = game_title_element.text.strip()
                
                # Use fuzzy matching to find the best match
                score = fuzz.ratio(title.lower(), game_title.lower())
                
                if score > best_score and score >= 75:  # Must be at least 75% similar
                    best_score = score
                    
                    # Extract price
                    price_float = None
                    
                    # Try to get discounted price first
                    price_tag = link.find('div', class_='discount_final_price')
                    if price_tag:
                        price = price_tag.text.strip()
                        
                        # Skip free games
                        if "Free" not in price and "Gratuito" not in price and "Gratis" not in price:
                            # Extract numbers
                            cleaned_price = re.sub(r'[^\d,\.]', '', price)
                            cleaned_price = cleaned_price.replace(',', '.')
                            
                            if cleaned_price:
                                try:
                                    price_float = float(cleaned_price)
                                except ValueError:
                                    pass
                    
                    # If no discounted price, try regular price
                    if price_float is None:
                        price_tag = link.find('div', class_='search_price')
                        if price_tag:
                            price = price_tag.text.strip()
                            
                            # Skip free games
                            if "Free" not in price and "Gratuito" not in price and "Gratis" not in price:
                                # Extract numbers
                                cleaned_price = re.sub(r'[^\d,\.]', '', price)
                                cleaned_price = cleaned_price.replace(',', '.')
                                
                                if cleaned_price:
                                    try:
                                        price_float = float(cleaned_price)
                                    except ValueError:
                                        pass
                    
                    # Only consider this a match if we found a price
                    if price_float is not None:
                        # Get image URL
                        image_url = None
                        image_element = link.find('div', class_='col search_capsule')
                        if image_element:
                            img_tag = image_element.find('img')
                            if img_tag:
                                image_url = img_tag.get('src')
                        
                        if not image_url:
                            image_url = 'https://via.placeholder.com/150'
                        
                        best_match = {
                            "titolo": game_title,
                            "titolo_clean": game_title,  # Store clean title for reference
                            "piattaforma": "PC",
                            "prezzo": price_float,
                            "immagine": image_url,
                            "link": link.get('href', '#'),
                            "descrizione": f"Gioco disponibile su Steam.",
                            "sito": "Steam",
                            "slug": self._generate_slug(game_title, "PC")
                        }
            
            # Cache the result
            self.steam_cache[title] = best_match
            return best_match
            
        except Exception as e:
            print(f"Errore cercando '{title}' su Steam: {e}")
            return None
    
    def _compare_prices(self, giochi_steam, giochi_ig):
        """Compare prices between Steam and Instant Gaming"""
        giochi_migliori = {}
        
        # First add all games from Instant Gaming
        for gioco in giochi_ig:
            titolo = gioco["titolo"]
            piattaforma = gioco["piattaforma"].lower()
            prezzo_ig = gioco["prezzo"]
            
            # Create a unique key for each game
            chiave = f"{titolo}_{piattaforma}"
            
            giochi_migliori[chiave] = {
                "titolo": titolo,
                "piattaforma": piattaforma,
                "prezzo": prezzo_ig,
                "prezzo_steam": None,  # To be filled if found
                "prezzo_ig": prezzo_ig,
                "immagine": gioco["immagine"],
                "link": gioco["link"],
                "descrizione": gioco.get("descrizione", "Nessuna descrizione disponibile"),
                "sito": "Instant Gaming",
                "slug": gioco["slug"]
            }
        
        # Then compare with Steam games (PC only)
        for gioco_steam in giochi_steam:
            if not gioco_steam:  # Skip None values
                continue
                
            titolo_steam = gioco_steam["titolo"]
            prezzo_steam = gioco_steam["prezzo"]
            
            # Check if there's a similar game from IG for PC
            miglior_match = None
            miglior_punteggio = 0
            
            for chiave, gioco_ig in giochi_migliori.items():
                if gioco_ig["piattaforma"].lower() == "pc":
                    # Use fuzzy matching to compare titles
                    punteggio = fuzz.ratio(titolo_steam.lower(), gioco_ig["titolo"].lower())
                    
                    # Also try with the clean title if available
                    if "titolo_clean" in gioco_steam:
                        clean_score = fuzz.ratio(gioco_steam["titolo_clean"].lower(), gioco_ig["titolo"].lower())
                        punteggio = max(punteggio, clean_score)
                    
                    if punteggio > miglior_punteggio and punteggio >= 70:  # 70% similarity threshold
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
                if chiave not in giochi_migliori:  # Avoid duplicates
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
        
        # Convert dictionary to list and sort by title
        return sorted(list(giochi_migliori.values()), key=lambda x: x["titolo"])
    
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
                    if key in cls.lower():  # Check if the class contains platform keyword
                        return value
        
        return "PC"  # If we don't find anything, it's a PC game
    
    def _generate_slug(self, title, platform):
        """Generate a unique slug from title and platform"""
        base_slug = re.sub(r'[^a-zA-Z0-9]+', '-', title.lower()).strip('-')
        platform_slug = re.sub(r'[^a-zA-Z0-9]+', '-', platform.lower()).strip('-')
        return f"{base_slug}-{platform_slug}"