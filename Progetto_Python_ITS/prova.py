import requests
from bs4 import BeautifulSoup
import csv
from fuzzywuzzy import fuzz  # Importa fuzzywuzzy

# Input dell'utente per il gioco che vuoi cercare
query = input("Inserisci il gioco che vuoi cercare: ")

# Imposta l'URL per la query di ricerca su Steam
url = f"https://store.steampowered.com/search/?term={query}"

# Headers per evitare di essere bloccato dalle misure anti-bot di Steam
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

# Invia la richiesta GET a Steam
res = requests.get(url, headers=headers)

# Analizza la risposta utilizzando BeautifulSoup
soup = BeautifulSoup(res.text, 'html.parser')

# Crea un file CSV per salvare i dati
with open('steam_game_details.csv', mode='w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file, quotechar='"', quoting=csv.QUOTE_MINIMAL)
    
    # Scrivi la riga di intestazione nel file CSV (rimosso il campo 'Platforms')
    writer.writerow(["Titolo", "Prezzo", "Data di rilascio", "Descrizione", "Generi", "Editore", "Link", "Immagine"])

    # Cicla attraverso i link dei risultati di gioco
    game_links = soup.find_all('a', class_='search_result_row')

    for link in game_links:
        # Estrai il titolo del gioco
        title = link.find('span', class_='title').text if link.find('span', class_='title') else 'Titolo non disponibile'
        
        # Usa il fuzzy matching per verificare se la query è abbastanza simile al titolo
        similarity = fuzz.partial_ratio(query.lower(), title.lower())  # Confronta query con il titolo
        if similarity >= 85:  # Accetta solo corrispondenze con almeno l'85% di similarità
            # Estrai l'app_id e altri dettagli come prima
            href = link["href"]
            app_id = href.split("/app/")[1].split("/")[0]

            # Estrai il prezzo utilizzando la classe aggiornata per il prezzo finale
            price_tag = link.find('div', class_='discount_final_price')  # Classe aggiornata per il prezzo finale
            if price_tag:
                price = price_tag.text.strip()
            else:
                price = 'Prezzo non disponibile'

            # Salta i giochi gratuiti (prezzo uguale a "Free")
            if "Free" in price:
                continue
            
            # Vai alla pagina del gioco per ottenere più dettagli come descrizione, generi, editore e immagine
            game_url = f"https://store.steampowered.com/app/{app_id}/"
            game_res = requests.get(game_url, headers=headers)
            game_soup = BeautifulSoup(game_res.text, 'html.parser')

            # Estrai la descrizione (se disponibile)
            description = game_soup.find('div', class_='game_description_snippet')
            description = description.text.strip() if description else 'Descrizione non disponibile'

            # Estrai la data di rilascio
            release_date = game_soup.find('div', class_='date')
            release_date = release_date.text.strip() if release_date else 'Data di rilascio non disponibile'

            # Estrai i generi da più posizioni possibili
            genres = []

            # Controlla i generi nella sezione 'tags'
            genre_section = game_soup.find('div', class_='glance_tags')
            if genre_section:
                genre_tags = genre_section.find_all('a')
                for genre in genre_tags:
                    genre_text = genre.text.strip()
                    if genre_text:  # Aggiungi solo generi non vuoti
                        genres.append(genre_text)

            # Se non sono stati trovati generi, controlla nella sezione 'categories'
            if not genres:
                categories_section = game_soup.find('div', class_='details_block')
                if categories_section:
                    category_tags = categories_section.find_all('a', class_='category')
                    for category in category_tags:
                        category_text = category.text.strip()
                        if category_text:  # Aggiungi solo categorie non vuote
                            genres.append(category_text)

            # Default se non sono stati trovati generi
            if not genres:
                genres = ['Nessun genere disponibile']

            # Unisci tutti i generi con un trattino '-'
            genres_str = ' - '.join(genres)

            # Estrai l'editore (correggi l'IndexError)
            publisher = 'Editore non disponibile'
            publisher_section = game_soup.find('div', class_='dev_row')
            if publisher_section:
                publisher_links = publisher_section.find_all('a')
                if len(publisher_links) > 1:
                    publisher = publisher_links[1].text.strip()  # L'editore è solitamente il secondo link

            # Prova a ottenere l'URL dell'immagine
            image_url = None
            # Primo tentativo: cerca il tag dell'immagine della copertura del gioco
            image_tag = game_soup.find('img', class_='game_header_image_full')
            if image_tag:
                image_url = image_tag['src']
            # Secondo tentativo: prova a ottenerlo dal meta tag og:image (fallback comune)
            if not image_url:
                image_tag = game_soup.find('meta', property='og:image')
                if image_tag:
                    image_url = image_tag['content']

            # Se non è stato trovato un URL dell'immagine, usa un'immagine segnaposto
            if not image_url:
                image_url = 'Immagine non disponibile'

            # Scrivi i dati estratti nel file CSV (rimosso il campo 'Platforms')
            writer.writerow([title, price, release_date, description, genres_str, publisher, game_url, image_url])

    print("Scraping completato.")
