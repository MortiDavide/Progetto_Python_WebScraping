import os
import pandas as pd

# Percorso del file CSV
current_file = __file__
current_dir = os.path.dirname(current_file)
file_dir = os.path.join(current_dir, 'wishlist.csv')

def inizializza_file():
    """Controlla se il file CSV esiste e ha delle colonne. Se vuoto, lo inizializza con le intestazioni."""
    if not os.path.exists(file_dir):
        # Se il file non esiste, crea un file vuoto con intestazioni
        columns = ['id', 'titolo', 'prezzo', 'release_date', 'descrizione', 'generi', 'editore', 'game_url', 'image_url', 'utenza', 'password', 'Stato']
        df = pd.DataFrame(columns=columns)
        df.to_csv(file_dir, index=False)
    else:
        try:
            df = pd.read_csv(file_dir)
            if df.empty:
                # Se il file esiste ma è vuoto, lo inizializziamo con le intestazioni
                columns = ['id', 'titolo', 'prezzo', 'release_date', 'descrizione', 'generi', 'editore', 'game_url', 'image_url', 'utenza', 'password', 'Stato']
                df = pd.DataFrame(columns=columns)
                df.to_csv(file_dir, index=False)
        except pd.errors.EmptyDataError:
            # Gestione di un file esistente ma vuoto
            columns = ['id', 'titolo', 'prezzo', 'release_date', 'descrizione', 'generi', 'editore', 'game_url', 'image_url', 'utenza', 'password', 'Stato']
            df = pd.DataFrame(columns=columns)
            df.to_csv(file_dir, index=False)

def cerca_ultimo_id():
    """Restituisce l'ultimo ID presente nel file CSV."""
    # Inizializza il file se necessario
    inizializza_file()
    
    df = pd.read_csv(file_dir)
    if df.empty:
        return 0
    else:
        # Ritorna l'ultimo ID presente nel file
        return df['id'].max()

def leggiDettagli(id):
    """Restituisce i dettagli dell'account corrispondente all'ID."""
    df = pd.read_csv(file_dir)
    account = df[df['id'] == id].iloc[0]  # Prendi la prima riga che corrisponde all'ID
    return account.to_dict()

def scriviDettagli(dettagli):
    """Scrive i dettagli nel file CSV."""
    df = pd.read_csv(file_dir)
    # Convertiamo il dizionario in un DataFrame e lo concatenamo
    dettagli_df = pd.DataFrame([dettagli])  # Creiamo un DataFrame con il dizionario
    df = pd.concat([df, dettagli_df], ignore_index=True)  # Concatenazione dei DataFrame
    df.to_csv(file_dir, index=False)


def disattiva_account(id_account):
    """Disattiva un account (impedisce l'accesso)."""
    df = pd.read_csv(file_dir)
    df.loc[df['id'] == id_account, 'Stato'] = False
    df.to_csv(file_dir, index=False)

