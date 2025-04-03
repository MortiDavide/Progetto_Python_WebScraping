# Persistenza.py
import os
import pandas as pd

# File paths
users_file = 'users.csv'
wishlist_file = "wishlist.csv"

# Funzione per leggere gli utenti dal CSV
def load_users():
    users = []
    if os.path.exists(users_file):
        df = pd.read_csv(users_file)
        for _, row in df.iterrows():
            users.append({
                "id": row.get("id", _),
                "username": row["username"],
                "password": row["password"]
            })
    return users

# Funzione per salvare un nuovo utente nel CSV
def save_user(username, password):
    nuovo_utente = pd.DataFrame([[username, password]], columns=["username", "password"])

    if os.path.exists(users_file):
        df = pd.read_csv(users_file)
        df = pd.concat([df, nuovo_utente], ignore_index=True)
    else:
        df = nuovo_utente

    df.to_csv(users_file, index=False)

# Funzione per caricare la wishlist dal CSV
def load_wishlist():
    wishlist_games = []
    if os.path.exists(wishlist_file):
        df = pd.read_csv(wishlist_file)
        for _, row in df.iterrows():
            wishlist_games.append({
                "id": row.get("id", _),
                "titolo": row["titolo"],
                "piattaforma": row["piattaforma"],
                "prezzo": row["prezzo"],
                "immagine": row["immagine"],
                "link": row["link"],
                "sito": row["sito"],
                "slug": row["slug"]
            })
    return wishlist_games

# Funzione per salvare un gioco nella wishlist
def save_wishlist(id, titolo, piattaforma, prezzo, immagine, link, sito, slug):
    nuovo_gioco = pd.DataFrame([[id, titolo, piattaforma, prezzo, immagine, link, sito, slug]], 
                             columns=["id", "titolo", "piattaforma", "prezzo", "immagine", "link", "sito", "slug"])

    if os.path.exists(wishlist_file):
        df = pd.read_csv(wishlist_file)
        df = pd.concat([df, nuovo_gioco], ignore_index=True)
    else:
        df = nuovo_gioco

    df.to_csv(wishlist_file, index=False)

# Funzione per rimuovere un gioco dalla wishlist
def remove_from_wishlist(slug):
    if os.path.exists(wishlist_file):
        df = pd.read_csv(wishlist_file)
        # Rimuovi il gioco con lo slug specificato
        df = df[df["slug"] != slug]
        # Salva la wishlist aggiornata
        df.to_csv(wishlist_file, index=False)
    return True