# persistence/game_repository.py
import requests
from bs4 import BeautifulSoup
import re
from fuzzywuzzy import fuzz
import time
import urllib.parse
    
class GameRepository:
    def __init__(self):
        self.steam_cache = {}  # Cache per i risultati di ricerca su Steam
    
    def search_games(self, query):
        """Cerca giochi su diverse piattaforme"""
        if not query:
            return []
        
        IG_url = f"https://www.instant-gaming.com/it/ricerca/?query={query}"
        
        try:
            ig_games = self._scrape_instant_gaming(IG_url)
            print(f"Trovati {len(ig_games)} giochi su Instant Gaming")
        except Exception as e:
            print(f"Errore durante lo scraping di Instant Gaming: {e}")
            ig_games = []
        
        # Per ogni gioco di Instant Gaming, prova a trovare un gioco corrispondente su Steam
        steam_games = []
        for ig_game in ig_games:
            if ig_game["piattaforma"].lower() == "pc":
                try:
                    # Usa il titolo esatto del gioco per un matching migliore
                    game_title = ig_game["titolo"]
                    
                    # Rimuovi qualsiasi informazione sulla piattaforma o edizione dal titolo
                    clean_title = re.sub(r'\s*(\(PC\)|\(Steam\)|\(Epic\)|\- \w+ Edition).*$', '', game_title)
                    
                    # Prova a trovare il gioco su Steam
                    Steam_url = f"https://store.steampowered.com/search/?term={urllib.parse.quote(clean_title)}"
                    steam_result = self._find_exact_game_on_steam(Steam_url, clean_title)
                    
                    if steam_result:
                        steam_games.append(steam_result)
                    
                    # Piccolo ritardo per evitare limiti di frequenza
                    time.sleep(0.2)
                except Exception as e:
                    print(f"Errore durante la ricerca su Steam per {ig_game['titolo']}: {e}")
        
        print(f"Trovati {len(steam_games)} giochi su Steam")
        
        if not ig_games and not steam_games:
            return [{"titolo": "Nessun risultato trovato", "piattaforma": "N/A", "prezzo": None, "immagine": "https://via.placeholder.com/150", "link": "#", "slug": "no-results"}]
        
        # Confronta i prezzi e combina i risultati
        combined_games = self._compare_prices(steam_games, ig_games)
        
        # Filtra i giochi senza prezzi validi
        combined_games = [game for game in combined_games if game['prezzo'] is not None]
        
        if not combined_games:
            return [{"titolo": "No games available", "piattaforma": "N/A", "prezzo": None, "immagine": "https://via.placeholder.com/150", "link": "#", "slug": "no-results"}]
        
        return combined_games
    
    def load_trending_games(self):
        """Carica i giochi in tendenza dalle piattaforme"""
        try:
            # Carica i giochi in tendenza da Instant Gaming
            IG_url = "https://www.instant-gaming.com/it/"
            ig_games = self._scrape_instant_gaming(IG_url)
            
            # Filtra solo i giochi per PC
            pc_games = [game for game in ig_games if game["piattaforma"].lower() == "pc"]
            
            # Per ogni gioco PC in tendenza, prova a trovarlo su Steam
            steam_games = []
            for pc_game in pc_games:
                try:
                    # Pulisci il titolo per un matching migliore
                    game_title = pc_game["titolo"]
                    clean_title = re.sub(r'\s*(\(PC\)|\(Steam\)|\(Epic\)|\- \w+ Edition).*$', '', game_title)
                    
                    # Cerca su Steam
                    Steam_url = f"https://store.steampowered.com/search/?term={urllib.parse.quote(clean_title)}"
                    steam_result = self._find_exact_game_on_steam(Steam_url, clean_title)
                    
                    if steam_result:
                        steam_games.append(steam_result)
                    
                    # Aggiungi un piccolo ritardo per evitare di sovraccaricare Steam
                    time.sleep(0.2)
                except Exception as e:
                    print(f"Errore durante la ricerca su Steam per {pc_game['titolo']}: {e}")
            
            # Confronta i prezzi e ottieni le migliori offerte
            trending_games = self._compare_prices(steam_games, ig_games)
            return trending_games
        except Exception as e:
            print(f"Errore durante il caricamento dei giochi di tendenza: {e}")
            return []
    
    def _scrape_instant_gaming(self, url):
        """Scarica i dati dei giochi da Instant Gaming"""
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
                
                # Pulisci il titolo per un confronto migliore con Steam
                clean_title = re.sub(r'\s*(\(PC\)|\(Steam\)|\(Epic\)|\- \w+ Edition).*$', '', titolo_text)
                
                giochi.append({
                    "titolo": titolo_text,
                    "titolo_clean": clean_title,  # Memorizza il titolo pulito per un matching migliore
                    "piattaforma": platform,
                    "prezzo": prezzo_float,
                    "immagine": immagine_url,
                    "link": link_url,
                    "sito": "Instant Gaming",
                    "slug": self._generate_slug(titolo_text, platform)
                })
            
        return giochi
    
    def _find_exact_game_on_steam(self, url, title):
        """Trova un gioco specifico su Steam attraverso il titolo"""
        # Prima controlla se abbiamo già cercato questo titolo
        if title in self.steam_cache:
            return self.steam_cache[title]
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Cookie': 'birthtime=536457201; mature_content=1;'  # Imposta il cookie di verifica dell'età
        }

        try:
            res = requests.get(url, headers=headers)
            soup = BeautifulSoup(res.text, 'html.parser')
            
            # Trova tutti i link dei risultati dei giochi
            game_links = soup.find_all('a', class_='search_result_row')
            
            best_match = None
            best_score = 0
            
            for link in game_links[:5]:  # Controlla solo i primi 5 risultati
                game_title_element = link.find('span', class_='title')
                if not game_title_element:
                    continue
                
                game_title = game_title_element.text.strip()
                
                # Utilizza il matching fuzzy per trovare la corrispondenza migliore
                score = fuzz.ratio(title.lower(), game_title.lower())
                
                if score > best_score and score >= 75:  # Deve essere simile almeno al 75%
                    best_score = score
                    
                    # Estrai il prezzo
                    price_float = None
                    
                    # Prima prova a ottenere il prezzo scontato
                    price_tag = link.find('div', class_='discount_final_price')
                    if price_tag:
                        price = price_tag.text.strip()
                        
                        # Salta i giochi gratuiti
                        if "Free" not in price and "Gratuito" not in price and "Gratis" not in price:
                            # Estrai i numeri
                            cleaned_price = re.sub(r'[^\d,\.]', '', price)
                            cleaned_price = cleaned_price.replace(',', '.')
                            
                            if cleaned_price:
                                try:
                                    price_float = float(cleaned_price)
                                except ValueError:
                                    pass
                    
                    # Se non c'è un prezzo scontato, prova con il prezzo normale
                    if price_float is None:
                        price_tag = link.find('div', class_='search_price')
                        if price_tag:
                            price = price_tag.text.strip()
                            
                            # Salta i giochi gratuiti
                            if "Free" not in price and "Gratuito" not in price and "Gratis" not in price:
                                # Estrai i numeri
                                cleaned_price = re.sub(r'[^\d,\.]', '', price)
                                cleaned_price = cleaned_price.replace(',', '.')
                                
                                if cleaned_price:
                                    try:
                                        price_float = float(cleaned_price)
                                    except ValueError:
                                        pass
                    
                    # Considera una corrispondenza solo se abbiamo trovato un prezzo
                    if price_float is not None:
                        # Ottieni l'URL dell'immagine
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
                            "titolo_clean": game_title,  # Memorizza il titolo pulito per riferimento
                            "piattaforma": "PC",
                            "prezzo": price_float,
                            "immagine": image_url,
                            "link": link.get('href', '#'),
                            "descrizione": f"Gioco disponibile su Steam.",
                            "sito": "Steam",
                            "slug": self._generate_slug(game_title, "PC")
                        }
            
            # Salva in cache il risultato
            self.steam_cache[title] = best_match
            return best_match
            
        except Exception as e:
            print(f"Errore cercando '{title}' su Steam: {e}")
            return None
    
    def _compare_prices(self, giochi_steam, giochi_ig):
        """Confronta i prezzi tra Steam e Instant Gaming"""
        giochi_migliori = {}
        
        # Prima aggiungi tutti i giochi da Instant Gaming
        for gioco in giochi_ig:
            titolo = gioco["titolo"]
            piattaforma = gioco["piattaforma"].lower()
            prezzo_ig = gioco["prezzo"]
            
            # Crea una chiave unica per ogni gioco
            chiave = f"{titolo}_{piattaforma}"
            
            giochi_migliori[chiave] = {
                "titolo": titolo,
                "piattaforma": piattaforma,
                "prezzo": prezzo_ig,
                "prezzo_steam": None,  # Da compilare se trovato
                "prezzo_ig": prezzo_ig,
                "immagine": gioco["immagine"],
                "link": gioco["link"],
                "descrizione": gioco.get("descrizione", "Nessuna descrizione disponibile"),
                "sito": "Instant Gaming",
                "slug": gioco["slug"]
            }
        
        # Poi confronta con i giochi Steam (solo PC)
        for gioco_steam in giochi_steam:
            if not gioco_steam:  # Salta i valori None
                continue
                
            titolo_steam = gioco_steam["titolo"]
            prezzo_steam = gioco_steam["prezzo"]
            
            # Controlla se c'è un gioco simile da IG per PC
            miglior_match = None
            miglior_punteggio = 0
            
            for chiave, gioco_ig in giochi_migliori.items():
                if gioco_ig["piattaforma"].lower() == "pc":
                    # Usa il matching fuzzy per confrontare i titoli
                    punteggio = fuzz.ratio(titolo_steam.lower(), gioco_ig["titolo"].lower())
                    
                    # Prova anche con il titolo pulito se disponibile
                    if "titolo_clean" in gioco_steam:
                        clean_score = fuzz.ratio(gioco_steam["titolo_clean"].lower(), gioco_ig["titolo"].lower())
                        punteggio = max(punteggio, clean_score)
                    
                    if punteggio > miglior_punteggio and punteggio >= 70:  # Soglia di somiglianza del 70%
                        miglior_punteggio = punteggio
                        miglior_match = chiave
            
            if miglior_match:
                # Abbiamo trovato un gioco simile su IG, confronta i prezzi
                giochi_migliori[miglior_match]["prezzo_steam"] = prezzo_steam
                
                # Confronta i prezzi e scegli il più basso
                if prezzo_steam is not None and (giochi_migliori[miglior_match]["prezzo_ig"] is None 
                                               or prezzo_steam < giochi_migliori[miglior_match]["prezzo_ig"]):
                    giochi_migliori[miglior_match]["prezzo"] = prezzo_steam
                    giochi_migliori[miglior_match]["sito"] = "Steam"
                    giochi_migliori[miglior_match]["link"] = gioco_steam["link"]
            else:
                # Non abbiamo trovato un gioco simile su IG, aggiungi il gioco Steam
                chiave = f"{titolo_steam}_pc"
                if chiave not in giochi_migliori:  # Evita i duplicati
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
        
        # Converti il dizionario in lista e ordina per titolo
        return sorted(list(giochi_migliori.values()), key=lambda x: x["titolo"])
    
    def _extract_platform(self, game_container):
        """Trova la piattaforma del gioco analizzando tutte le classi nel contenitore"""
        platform_classes = {
            "xbox": "Xbox",
            "playstation": "PlayStation",
        }
        
        # Trova tutti i div nel contenitore
        all_divs = game_container.find_all("div")

        for div in all_divs:
            class_list = div.get("class", [])
            for cls in class_list:
                for key, value in platform_classes.items():
                    if key in cls.lower():  # Controlla se la classe contiene la parola chiave della piattaforma
                        return value
        
        return "PC"  # Se non troviamo nulla, è un gioco per PC
    
    def _generate_slug(self, title, platform):
        """Genera uno slug univoco dal titolo e dalla piattaforma"""
        base_slug = re.sub(r'[^a-zA-Z0-9]+', '-', title.lower()).strip('-')
        platform_slug = re.sub(r'[^a-zA-Z0-9]+', '-', platform.lower()).strip('-')
        return f"{base_slug}-{platform_slug}"